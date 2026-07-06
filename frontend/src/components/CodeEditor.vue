<template>
  <div ref="editorRef" class="code-editor"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { EditorView, keymap, lineNumbers } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { oneDark } from '@codemirror/theme-one-dark'
import { defaultKeymap, indentWithTab } from '@codemirror/commands'
import { syntaxHighlighting, defaultHighlightStyle, StreamLanguage } from '@codemirror/language'
import { toml } from '@codemirror/legacy-modes/mode/toml'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'toml'
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const editorRef = ref(null)
let editorView = null

// TOML 语言支持
const tomlLanguage = StreamLanguage.define(toml)

onMounted(() => {
  if (!editorRef.value) return

  const startState = EditorState.create({
    doc: props.modelValue,
    extensions: [
      lineNumbers(),
      oneDark,
      tomlLanguage,
      keymap.of([...defaultKeymap, indentWithTab]),
      syntaxHighlighting(defaultHighlightStyle),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          emit('update:modelValue', update.state.doc.toString())
        }
      }),
      EditorView.theme({
        '&': {
          fontSize: '14px',
          backgroundColor: 'transparent !important',
          WebkitFontSmoothing: 'antialiased',
          MozOsxFontSmoothing: 'grayscale',
          textRendering: 'optimizeLegibility'
        },
        '.cm-editor': {
          height: '100%',
          maxHeight: '100%'
        },
        '.cm-scroller': {
          overflow: 'auto'
        },
        '.cm-content': {
          padding: '16px',
          lineHeight: '1.7',
          fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", "Source Code Pro", "SF Mono", "Ubuntu Mono", Consolas, "Courier New", monospace',
          fontFeatureSettings: '"calt" 1, "liga" 1, "ss02" 1, "ss03" 1, "ss04" 1, "ss05" 1, "ss06" 1, "zero" 1',
          fontVariantLigatures: 'contextual',
          fontWeight: '400'
        },
        '.cm-gutters': {
          backgroundColor: 'rgba(13, 17, 23, 0.5)',
          borderRight: '1px solid rgba(48, 54, 61, 0.5)',
          paddingLeft: '8px',
          paddingRight: '8px'
        },
        '.cm-lineNumbers': {
          color: '#484f58'
        },
        '.cm-activeLineGutter': {
          backgroundColor: 'rgba(33, 38, 45, 0.5)'
        },
        '.cm-activeLine': {
          backgroundColor: 'rgba(56, 139, 253, 0.08)'
        },
        '.cm-selectionBackground': {
          backgroundColor: 'rgba(56, 139, 253, 0.3) !important'
        },
        '.cm-cursor': {
          borderLeftColor: '#58a6ff'
        },
        '&.cm-focused': {
          outline: 'none'
        }
      }),
      EditorView.editorAttributes.of({
        style: 'height: 100%'
      }),
      EditorState.readOnly.of(props.readonly)
    ]
  })

  editorView = new EditorView({
    state: startState,
    parent: editorRef.value
  })

  // 使用 ResizeObserver 确保编辑器正确适应容器
  const resizeObserver = new ResizeObserver(() => {
    if (editorView) {
      editorView.requestMeasure()
    }
  })
  resizeObserver.observe(editorRef.value)

  // 保存引用以便清理
  editorRef.value._resizeObserver = resizeObserver
})

onUnmounted(() => {
  if (editorRef.value && editorRef.value._resizeObserver) {
    editorRef.value._resizeObserver.disconnect()
  }
  if (editorView) {
    editorView.destroy()
  }
})

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  if (editorView && newValue !== editorView.state.doc.toString()) {
    editorView.dispatch({
      changes: {
        from: 0,
        to: editorView.state.doc.length,
        insert: newValue
      }
    })
  }
})
</script>

<style scoped>
.code-editor {
  height: 100%;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(13, 17, 23, 0.75);
  backdrop-filter: blur(12px) saturate(140%);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
}

html.dark .code-editor {
  background: rgba(13, 17, 23, 0.45);
}

:deep(.cm-editor) {
  height: 100%;
  background: transparent !important;
}

:deep(.cm-scroller) {
  overflow: auto;
  background: transparent !important;
}

/* TOML 语法高亮样式 */
:deep(.cm-keyword) { color: #ff7b72; }
:deep(.cm-string) { color: #a5d6ff; }
:deep(.cm-number) { color: #79c0ff; }
:deep(.cm-comment) { color: #8b949e; font-style: italic; }
:deep(.cm-property) { color: #7ee787; }
:deep(.cm-operator) { color: #ff7b72; }
:deep(.cm-punctuation) { color: #c9d1d9; }

/* 滚动条样式 */
:deep(.cm-scroller::-webkit-scrollbar) {
  width: 12px;
  height: 12px;
}

:deep(.cm-scroller::-webkit-scrollbar-track) {
  background: transparent;
}

:deep(.cm-scroller::-webkit-scrollbar-thumb) {
  background: rgba(48, 54, 61, 0.6);
  border-radius: 6px;
  border: 3px solid transparent;
  background-clip: padding-box;
}

:deep(.cm-scroller::-webkit-scrollbar-thumb:hover) {
  background: rgba(72, 79, 88, 0.8);
  background-clip: padding-box;
}
</style>