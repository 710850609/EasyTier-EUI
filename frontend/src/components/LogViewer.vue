<template>
  <var-popup
    v-model:show="showLocal"
    position="bottom"
    :teleport="false"
    :overlay-style="{ background: 'transparent' }"
    :style="{ height: isMobile ? '85vh' : '70vh', borderRadius: '16px 16px 0 0', '--popup-content-background-color': 'transparent' }"
    @closed="handleClosed"
  >
    <div class="log-viewer">
      <div class="log-viewer-toolbar">
        <span class="log-viewer-title">{{ $t('logViewer.title') }}</span>
        <div class="log-viewer-actions">
          <var-button size="small" text @click="toggleLogPause">
            <template #icon>
              <var-icon :name="logPaused ? 'play' : 'pause'" />
            </template>
            {{ logPaused ? $t('logViewer.resume') : $t('logViewer.pause') }}
          </var-button>
          <var-button size="small" text @click="toggleLogWrap">
            <template #icon><var-icon :name="logWrap ? 'wrap' : 'format-line-spacing'" /></template>
            {{ logWrap ? $t('logViewer.wrap') : $t('logViewer.noWrap') }}
          </var-button>
          <var-button size="small" text @click="clearLogContent">
            <template #icon><var-icon name="delete" /></template>
            {{ $t('logViewer.clear') }}
          </var-button>
          <var-button size="small" text @click="copyLogContent">
            <template #icon><var-icon name="content-copy" /></template>
            {{ $t('logViewer.copy') }}
          </var-button>
        </div>
      </div>
      <div class="log-viewer-content">
        <div v-if="logLoading" class="log-viewer-loading">
          <var-loading />
          <span>{{ $t('logViewer.loading') }}</span>
        </div>
        <div ref="logEditorRef" class="log-editor" v-show="!logLoading && logEditorView"></div>
        <div v-if="!logLoading && !logEditorView" class="log-viewer-empty">{{ $t('logViewer.noLogs') }}</div>
      </div>
    </div>
  </var-popup>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { EditorView, ViewPlugin, Decoration } from '@codemirror/view'
import { EditorState, Compartment, RangeSetBuilder } from '@codemirror/state'
import { oneDark } from '@codemirror/theme-one-dark'
import { StreamLanguage } from '@codemirror/language'
import { api } from '../utils/api.js'
import { Poller } from '../utils/poller.js'
import { copyToClipboard } from '../utils/clipboard.js'
import toast from './toast.js'

const { t } = useI18n()

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['update:show'])

const showLocal = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const isMobile = window.innerWidth < 768

const logOffset = ref(0)
const logPaused = ref(false)
const logLoading = ref(false)
const logEditorRef = ref(null)
const logEditorView = ref(null)
const logWrap = ref(false)

const MAX_LOG_CONTENT_SIZE = 300 * 1024

const logPoller = new Poller({
  interval: 2000,
  immediate: true,
  onError: (error) => console.error('获取日志失败:', error)
})

const lineWrapCompartment = new Compartment()

const LEVEL_DEFS = [
  { pattern: /\b(ERROR|CRITICAL|FATAL)\b/,           token: 'keyword',  cls: 'log-line-error' },
  { pattern: /\b(WARN|WARNING)\b/,                   token: 'typeName', cls: 'log-line-warn' },
  { pattern: /\bINFO\b/,                             token: 'number',   cls: 'log-line-info' },
  { pattern: /\b(DEBUG|TRACE)\b/,                    token: 'comment',  cls: 'log-line-debug' },
  { pattern: /\b(TunDeviceError|ListenerAddFailed|ConnectionError|ConnectError)\b/, token: 'keyword', cls: 'log-line-error' },
  { pattern: /\b(PeerRemoved|PeerConnRemoved)\b/,    token: 'typeName', cls: 'log-line-warn' },
  { pattern: /\bTunDeviceReady|PeerAdded|PeerConnAdded|ListenerAdded|ConnectionAccepted|Connecting|VpnPortalStarted|VpnPortalClientConnected|DhcpIpv4Changed|PublicIpv6Changed|CredentialChanged\b/, token: 'number', cls: 'log-line-info' },
]

const logLanguage = StreamLanguage.define({
  token(stream) {
    for (const def of LEVEL_DEFS) {
      if (stream.match(def.pattern)) return def.token
    }
    stream.next()
    return null
  }
})

const logLevelLinePlugin = ViewPlugin.fromClass(class {
    constructor(view) {
      this.decorations = this.build(view)
    }
    update(update) {
      if (update.docChanged || update.viewportChanged) {
        this.decorations = this.build(update.view)
      }
    }
    build(view) {
      const builder = new RangeSetBuilder()
      for (const { from, to } of view.visibleRanges) {
        const startLine = view.state.doc.lineAt(from)
        const endLine = view.state.doc.lineAt(to)
        for (let i = startLine.number; i <= endLine.number; i++) {
          const line = view.state.doc.line(i)
          const text = line.text
          let cls = ''
          for (const def of LEVEL_DEFS) {
            if (def.pattern.test(text)) {
              cls = def.cls
              break
            }
          }
          if (cls) {
            builder.add(line.from, line.from, Decoration.line({ class: cls }))
          }
        }
      }
      return builder.finish()
    }
  }, {
    decorations: v => v.decorations
  })

const createLogEditor = () => {
  if (logEditorView.value) return
  const state = EditorState.create({
    doc: '',
    extensions: [
      oneDark,
      logLanguage,
      logLevelLinePlugin,
      EditorState.readOnly.of(true),
      lineWrapCompartment.of([]),
      EditorView.editorAttributes.of({ style: 'height: 100%' }),
      EditorView.theme({
        '&': {
          fontSize: '12px',
          backgroundColor: 'transparent !important',
        },
        '.cm-editor': {
          height: '100%',
        },
        '.cm-scroller': {
          overflow: 'auto',
        },
        '.cm-content': {
          padding: '12px',
          lineHeight: '1.7',
          fontFamily: '"SF Mono", "Cascadia Code", "Consolas", "Courier New", monospace',
        },
        '&.cm-focused': {
          outline: 'none',
        },
        '.cm-activeLine': {
          backgroundColor: 'transparent',
        },
        '.cm-line.log-line-error': { color: '#f85149' },
        '.cm-line.log-line-warn': { color: '#d2991d' },
        '.cm-line.log-line-info': { color: '#7ee787' },
        '.cm-line.log-line-debug': { color: '#8b949e' },
      }),
    ],
  })
  logEditorView.value = new EditorView({
    state,
    parent: logEditorRef.value,
  })
}

const destroyLogEditor = () => {
  if (logEditorView.value) {
    logEditorView.value.destroy()
    logEditorView.value = null
  }
}

const fetchLogs = async () => {
  if (logPaused.value) return
  try {
    const resp = await api.monitor.getLogs({ lines: 100, offset: logOffset.value, log_type: 'easytier' })
    const result = resp.data || resp
    if (result && typeof result === 'object' && logEditorView.value) {
      const newLines = result.lines || ''
      const doc = logEditorView.value.state.doc
      if (result.appending && doc.length > 0) {
        logEditorView.value.dispatch({
          changes: { from: doc.length, insert: newLines }
        })
        const newLen = doc.length + newLines.length
        if (newLen > MAX_LOG_CONTENT_SIZE) {
          const text = logEditorView.value.state.doc.toString()
          const cutoff = text.length - MAX_LOG_CONTENT_SIZE
          const firstNl = text.indexOf('\n', cutoff)
          const trimmed = text.slice(firstNl > 0 ? firstNl + 1 : cutoff)
          logEditorView.value.dispatch({
            changes: { from: 0, to: text.length, insert: trimmed }
          })
        }
      } else {
        logEditorView.value.dispatch({
          changes: { from: 0, to: doc.length, insert: newLines }
        })
      }
      logOffset.value = result.offset || 0
    }
    logLoading.value = false
    scrollLogToBottom()
  } catch (error) {
    if (error.name === 'AbortError') return
    logLoading.value = false
  }
}

const scrollLogToBottom = () => {
  nextTick(() => {
    const view = logEditorView.value
    if (view) {
      view.scrollDOM.scrollTop = view.scrollDOM.scrollHeight
    }
  })
}

const toggleLogPause = () => {
  logPaused.value = !logPaused.value
  if (!logPaused.value) {
    fetchLogs()
  }
}

const toggleLogWrap = () => {
  logWrap.value = !logWrap.value
  if (logEditorView.value) {
    logEditorView.value.dispatch({
      effects: lineWrapCompartment.reconfigure(
        logWrap.value ? EditorView.lineWrapping : []
      )
    })
  }
}

const clearLogContent = () => {
  if (logEditorView.value) {
    const doc = logEditorView.value.state.doc
    logEditorView.value.dispatch({
      changes: { from: 0, to: doc.length }
    })
  }
}

const copyLogContent = async () => {
  if (!logEditorView.value) return
  const text = logEditorView.value.state.doc.toString()
  if (!text) return
  try {
    await copyToClipboard(text)
    toast.success(t('nodes.copySuccess'))
  } catch (error) {
    toast.error(t('nodes.copyFailed'))
  }
}

const handleClosed = () => {
  logPoller.stop()
  logOffset.value = 0
  logPaused.value = false
  destroyLogEditor()
}

watch(showLocal, async (val) => {
  if (val) {
    logLoading.value = true
    logOffset.value = 0
    logPaused.value = false
    await nextTick()
    await nextTick()
    createLogEditor()
    logPoller.start(fetchLogs)
  }
})

onUnmounted(() => {
  logPoller.stop()
  destroyLogEditor()
})
</script>

<style scoped>
.log-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
  border-radius: 16px 16px 0 0;
  overflow: hidden;
}

:deep(.var-popup--content-background-color) {
  background-color: transparent !important;
}

.log-viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
  background: rgba(var(--color-surface-container-rgb), 0);
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
}

.log-viewer-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-surface);
  white-space: nowrap;
}

.log-viewer-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.log-viewer-actions :deep(.var-button--text) {
  color: var(--color-on-surface-variant) !important;
}

.log-viewer-actions :deep(.var-button--text:hover) {
  color: var(--color-on-surface) !important;
}

.log-viewer-content {
  position: relative;
  flex: 1;
  min-height: 0;
  background: rgba(13, 17, 23, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.log-editor {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.log-viewer-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-on-surface-variant);
  font-size: 14px;
}

.log-viewer-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-on-surface-variant);
  font-size: 14px;
}

.log-editor :deep(.cm-editor) {
  height: 100%;
  background: transparent !important;
}

.log-editor :deep(.cm-scroller) {
  overflow: auto;
  background: transparent !important;
}

.log-editor :deep(.cm-scroller::-webkit-scrollbar) {
  width: 10px;
  height: 10px;
}

.log-editor :deep(.cm-scroller::-webkit-scrollbar-track) {
  background: transparent;
}

.log-editor :deep(.cm-scroller::-webkit-scrollbar-thumb) {
  background: rgba(var(--color-outline-variant-rgb), 0.6);
  border-radius: 5px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.log-editor :deep(.cm-scroller::-webkit-scrollbar-thumb:hover) {
  background: rgba(var(--color-outline-variant-rgb), 0.8);
  background-clip: padding-box;
}

@media (max-width: 767px) {
  .log-viewer-toolbar {
    padding: 10px 12px;
  }

  .log-viewer-title {
    font-size: 15px;
  }
}

html.dark .log-viewer-content {
  background: rgba(13, 17, 23, 0.3) !important;
}
</style>