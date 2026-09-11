<template>
  <div class="stun-page">
    <!-- 1. 提示弹窗 -->
    <var-popup v-model:show="showTipPopup" position="top">
      <div class="tip-popup-content">
        <div class="tip-popup-header">
          <svg-icon type="mdi" :path="mdiInformationOutline" size="20" color="var(--color-primary)"></svg-icon>
          <span class="tip-popup-title">{{ $t('stun.tipTitle') }}</span>
        </div>
        <p>{{ $t('stun.tipContent') }}</p>
        <ul>
          <li>{{ $t('stun.tipItem1') }}</li>
          <li>{{ $t('stun.tipItem2') }}</li>
          <li>{{ $t('stun.tipItem3') }}</li>
        </ul>
      </div>
    </var-popup>

    <!-- 2. STUN 核心 -->
    <var-paper class="stun-block" :elevation="0">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiShieldLock" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('stun.stunCore') }}</span>
      </div>
      <var-divider />

      <div class="setting-row">
        <div class="version-info-block">
          <a class="setting-label setting-link" href="https://github.com/heiher/natmap" target="_blank" rel="noopener">{{ $t('stun.natmap') }}</a>
          <span class="version-value" v-if="existsNatmap">{{ natmapVersion || $t('stun.unknownVersion') }}</span>
          <span class="version-value" v-else style="color: var(--color-text-disabled);">{{ $t('stun.notInstalled') }}</span>
        </div>
        <var-button v-if="!existsNatmap" type="primary" size="small" @click="installNatmap" :loading="natmapInstalling">
          <var-icon name="download" />
          {{ $t('stun.installNatmap') }}
        </var-button>
        <var-button v-else type="primary" size="small" @click="checkNatmapVersion" auto-loading>
          <var-icon name="refresh" />
          {{ $t('stun.checkVersion') }}
        </var-button>
      </div>
    </var-paper>

    <!-- 3.1 Nat 穿透 -->
    <var-paper class="stun-block" :elevation="0">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiAccessPointNetwork" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ $t('stun.natTraversal') }}</span>
        <var-button type="primary" size="mini" round text @click="showTipPopup = true">
          <var-icon name="help-circle-outline" size="14" />
        </var-button>
        <div class="block-header-actions">
          <var-button type="primary" size="small" @click="addProfile">
            <var-icon name="plus" />
            {{ $t('stun.addProfile') }}
          </var-button>
        </div>
      </div>
      <var-divider />

      <!-- 空状态 -->
      <div class="profile-empty" v-if="profiles.length === 0">
        <span class="profile-empty-text">{{ $t('stun.noProfiles') }}</span>
      </div>

      <div class="profile-list" v-else>
        <div
          v-for="(p, idx) in profiles"
          :key="p.id"
          class="profile-row"
          :class="{ 'profile-row--active': !isDraft && idx === activeProfileIndex }"
          @click="switchProfile(idx)"
        >
          <div class="profile-row-left">
            <span
              class="status-dot"
              :style="{ background: p.running ? 'var(--color-success)' : 'var(--color-text-disabled)' }"
            />
            <span class="profile-row-name">{{ p.name }}</span>
            <var-chip size="mini" plain :type="p.stunConfig.protocol === 'tcp' ? 'primary' : 'warning'">
              {{ p.stunConfig.protocol.toUpperCase() }}
            </var-chip>
            <span class="profile-row-port" v-if="p.stunConfig.bindPort">
              {{ p.stunConfig.bindPort }}
            </span>
            <span class="profile-row-port" v-if="p.running && p.mapping">
               →
            </span>
            <span class="profile-row-mapping" v-if="p.running && p.mapping" @click.stop="copyText(`${p.mapping.protocol}://${p.mapping.public_addr}:${p.mapping.public_port}`)">
               {{ p.mapping.protocol }}://{{ p.mapping.public_addr }}:{{ p.mapping.public_port }}
            </span>
            <span class="profile-row-error" v-if="p.running && p.error_msg" @click.stop="copyText(p.error_msg)">
              {{ p.error_msg }}
            </span>
          </div>
          <div class="profile-row-right" @click.stop>
            <var-button
              v-if="!p.running"
              type="primary"
              size="small"
              @click="startStun(idx)"
              auto-loading
            >
              {{ $t('stun.start') }}
            </var-button>
            <var-button
              v-if="p.running"
              type="danger"
              size="small"
              @click="stopStun(idx)"
              auto-loading
            >
              {{ $t('stun.stop') }}
            </var-button>
          </div>
        </div>
      </div>
    </var-paper>

    <!-- 3.2 Natmap 设置 + 变动配置 -->
    <var-paper class="stun-block" :elevation="0" v-if="activeProfile">
      <div class="block-header">
        <svg-icon type="mdi" :path="mdiTune" size="24" color="var(--color-primary)"></svg-icon>
        <span class="block-title">{{ isDraft ? $t('stun.newSettings') : activeProfile.name }} {{ $t('stun.natmapSettings') }}</span>
        <div class="block-header-actions">
          <var-button type="danger" size="small" @click="removeProfile" auto-loading>
            <var-icon :name="isDraft ? 'window-close' : 'delete'" />
            {{ $t('stun.deleteProfile') }}
          </var-button>
        </div>
      </div>
      <var-divider />

      <!-- Natmap 参数 -->
      <div class="form-grid">
        <div class="form-row">
          <label class="form-label">{{ $t('stun.profileName') }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.name"
          />
        </div>

        <div class="form-row">
          <label class="form-label">{{ $t('stun.protocol') }}</label>
          <var-select
            variant="outlined"
            size="small"
            v-model="activeProfile.stunConfig.protocol"
          >
            <var-option :label="$t('stun.protocolTcp')" value="tcp" />
            <var-option :label="$t('stun.protocolUdp')" value="udp" />
          </var-select>
        </div>

        <div class="form-row">
          <label class="form-label">{{ $t('stun.bindPort') }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.stunConfig.bindPort"
          />
        </div>

<!--        <div class="form-row">-->
<!--          <label class="form-label">{{ $t('stun.interface') }}</label>-->
<!--          <var-input-->
<!--            variant="outlined"-->
<!--            size="small"-->
<!--            v-model="activeProfile.stunConfig.interface"-->
<!--            :placeholder="$t('stun.interfacePlaceholder')"-->
<!--          />-->
<!--        </div>-->

<!--        <div class="form-row">-->
<!--          <label class="form-label">{{ $t('stun.keepaliveInterval') }}</label>-->
<!--          <var-input-->
<!--            variant="outlined"-->
<!--            size="small"-->
<!--            v-model="activeProfile.stunConfig.keepaliveInterval"-->
<!--            type="number"-->
<!--          />-->
<!--        </div>-->

<!--        <div class="form-row">-->
<!--          <label class="form-label">UDP STUN 检测周期</label>-->
<!--          <var-input-->
<!--            variant="outlined"-->
<!--            size="small"-->
<!--            v-model="activeProfile.stunConfig.checkCycle"-->
<!--            type="number"-->
<!--          />-->
<!--        </div>-->

<!--        <div class="form-row">-->
<!--          <label class="form-label">{{ $t('stun.stunServer') }}</label>-->
<!--          <var-input-->
<!--            variant="outlined"-->
<!--            size="small"-->
<!--            v-model="activeProfile.stunConfig.stunServer"-->
<!--          />-->
<!--        </div>-->

<!--        <div class="form-row">-->
<!--          <label class="form-label">{{ $t('stun.httpServer') }}</label>-->
<!--          <var-input-->
<!--            variant="outlined"-->
<!--            size="small"-->
<!--            v-model="activeProfile.stunConfig.httpServer"-->
<!--            placeholder="TCP协议时，必填"-->
<!--          />-->
<!--        </div>-->
      </div>

      <var-divider />

      <!-- 公网IP/端口变更推送 -->
      <div class="section-label">
        {{ $t('stun.changePushLabel') }}
        <span v-if="activeProfile?.changeConfig?.domainName"> → </span>
        <span v-if="activeProfile?.changeConfig?.domainName" class="profile-row-mapping" @click="copyText(`txt://${activeProfile.changeConfig.domainName}`)">txt://{{ activeProfile.changeConfig.domainName }}</span>
      </div>
      <div class="form-grid">
        <div class="form-row">
          <label class="form-label">{{ $t('stun.dnsProvider') }}</label>
          <var-select
            variant="outlined"
            size="small"
            v-model="activeProfile.changeConfig.dnsProvider"
          >
            <var-option label="dynv6" value="dynv6" />
<!--          <var-option :label="$t('stun.providerAliyun')" value="aliyun" />-->
<!--          <var-option :label="$t('stun.providerCloudflare')" value="cloudflare" />-->
<!--          <var-option :label="$t('stun.providerTencent')" value="tencent" />-->
<!--          <var-option :label="$t('stun.providerCustom')" value="custom" />-->
          </var-select>
        </div>

        <div class="form-row">
          <label class="form-label">{{ $t('stun.domainName') }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.changeConfig.domainName"
          />
        </div>

        <div class="form-row">
          <label class="form-label">{{ $t('stun.apiKey') }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.changeConfig.apiKey"
            type="text"
          />
        </div>

        <div class="form-row">
          <label class="form-label">{{ $t('stun.apiSecret') }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.changeConfig.apiSecret"
            type="text"
          />
        </div>
      </div>

      <div class="block-footer">
        <var-button type="primary" @click="saveCurrentConfig" auto-loading>
          <var-icon name="content-save" />
          {{ $t('common.save') }}
        </var-button>
        <var-button @click="testPushTxtRecord" auto-loading>
          <var-icon name="send" />
          {{ $t('stun.testPush') }}
        </var-button>
      </div>
    </var-paper>

    <var-dialog v-model:show="showDeleteConfirm" :title="deleteConfirmTitle" @confirm="confirmDeleteProfile">
      <p style="color: var(--color-text-secondary); font-size: 14px; margin: 0;">
        {{ $t('stun.confirmDeleteDesc') }}
      </p>
    </var-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  mdiInformationOutline,
  mdiShieldLock,
  mdiAccessPointNetwork,
  mdiTune
} from '@mdi/js'
import { copyToClipboard } from '../utils/clipboard.js'
import SvgIcon from '@jamescoyle/vue-icon'
import toast from '../components/toast.js'
import api from '../utils/api.js'

const { t } = useI18n()

function createDefaultProfile(item, index) {
  return reactive({
    id: item.id,
    name: item.name || ('stun-' + (index + 1)),
    running: false,
    mapping: null,
    error_msg: '',
    stunConfig: {
      protocol: 'udp',
      stunServer: '',
      httpServer: '',
      interface: '',
      keepaliveInterval: '',
      checkCycle: '',
      bindPort: '11010'
    },
    changeConfig: {
      dnsProvider: 'dynv6',
      apiKey: '',
      apiSecret: '',
      domainName: ''
    }
  })
}

// Natmap 信息
const natmapVersion = ref('')
const existsNatmap = ref(false)
const natmapInstalling = ref(false)
const showTipPopup = ref(false)

// 多配置
const profiles = reactive([])
const activeProfileIndex = ref(0)
const natmapOperating = ref(false)
const draftProfile = ref(null)
const editProfile = ref(null)
const showDeleteConfirm = ref(false)
const deleteTargetIdx = ref(-1)

const activeProfile = computed(() => {
  if (draftProfile.value) return draftProfile.value
  return editProfile.value
})

const isDraft = computed(() => !!draftProfile.value)

const publicUri = computed(() => {
  const m = activeProfile.value?.mapping
  if (!m) return ''
  return `${m.protocol}://${m.public_addr}:${m.public_port}`
})

// 从后端加载配置
async function loadConfig() {
  try {
    const { data } = await api.stun.listStun()
    if (data && Array.isArray(data) && data.length > 0) {
      draftProfile.value = null
      profiles.length = 0
      data.forEach((item, idx) => {
        const profile = createDefaultProfile(item)
        if (item.stunConfig) Object.assign(profile.stunConfig, item.stunConfig)
        if (item.changeConfig) Object.assign(profile.changeConfig, item.changeConfig)
        if (item.mapping) profile.mapping = item.mapping
        profile.running = item.running || false
        profile.error_msg = item.error_msg || ''
        profiles.push(profile)
      })
      activeProfileIndex.value = 0
      editProfile.value = JSON.parse(JSON.stringify(profiles[0]))
    }
  } catch (e) {
    console.error('Failed to load STUN config:', e)
  }
}

// 切换配置
function switchProfile(index) {
  draftProfile.value = null
  activeProfileIndex.value = index
  if (profiles[index]) {
    editProfile.value = JSON.parse(JSON.stringify(profiles[index]))
  }
}

// 添加配置
function addProfile() {
  draftProfile.value = createDefaultProfile('', profiles.length)
}

// 删除配置
function removeProfile() {
  if (isDraft.value) {
    draftProfile.value = null
    editProfile.value = null
    return
  }
  deleteTargetIdx.value = activeProfileIndex.value
  showDeleteConfirm.value = true
}

const deleteConfirmTitle = computed(() => {
  const name = deleteTargetIdx.value >= 0 ? profiles[deleteTargetIdx.value]?.name || '' : ''
  return t('stun.confirmDelete', { name })
})

async function confirmDeleteProfile() {
  const idx = deleteTargetIdx.value
  if (idx < 0 || idx >= profiles.length) return
  const profileId = profiles[idx].id
  profiles.splice(idx, 1)
  if (profiles.length === 0) {
    activeProfileIndex.value = 0
    editProfile.value = null
  } else if (activeProfileIndex.value >= profiles.length) {
    activeProfileIndex.value = profiles.length - 1
    editProfile.value = JSON.parse(JSON.stringify(profiles[activeProfileIndex.value]))
  } else {
    editProfile.value = JSON.parse(JSON.stringify(profiles[activeProfileIndex.value]))
  }
  try {
    await api.stun.deleteStun(profileId)
    toast.success(t('stun.configDeleted'))
  } catch (e) {
    toast.error(t('stun.configDeleteFailed'))
  }
  showDeleteConfirm.value = false
}

// 检查 Natmap 版本
async function checkNatmapVersion() {
  try {
    const { data } = await api.stun.getNatmapVersion()
    existsNatmap.value = data.exists_natmap || false
    natmapVersion.value = data.current_version || ''
  } catch (e) {
    toast.error(t('stun.checkVersionFailed'))
  }
}

// 安装 Natmap
async function installNatmap() {
  natmapInstalling.value = true
  try {
    const { data } = await api.stun.installNatmap()
    if (data.success) {
      toast.success(t('stun.installNatmapSuccess'))
      await checkNatmapVersion()
    }
  } catch (e) {
    toast.error(t('stun.installNatmapFailed'))
  } finally {
    natmapInstalling.value = false
  }
}

// 启动 Natmap
async function startStun(idx) {
  switchProfile(idx)
  natmapOperating.value = true
  const profile = profiles[idx]
  try {
    await api.stun.startStun({id: profile.id})
    profile.running = true
    toast.success(t('stun.startSuccess'))
    fetchStunStatus()
  // } catch (e) {
  //   toast.error(t('stun.startFailed'))
  } finally {
    natmapOperating.value = false
  }
}

// 停止 Natmap
async function stopStun(idx) {
  switchProfile(idx)
  natmapOperating.value = true
  const profile = profiles[idx]
  try {
    await api.stun.stopStun(profile.id)
    profile.running = false
    profile.mapping = null
    profile.error_msg = ''
    toast.success(t('stun.stopSuccess'))
  } catch (e) {
    toast.error(t('stun.stopFailed'))
  } finally {
    natmapOperating.value = false
  }
}

// 轮询 STUN 状态
let statusPollTimer = null
async function fetchStunStatus() {
  try {
    const { data } = await api.stun.listStun()
    if (data && Array.isArray(data)) {
      const statusMap = {}
      data.forEach(item => { statusMap[item.id] = item })
      profiles.forEach(p => {
        const info = statusMap[p.id]
        if (info) {
          Object.assign(p, {
            id: info.id,
            running: info.running || false,
            mapping: info.mapping || null,
            error_msg: info.error_msg || '' })
        }
      })
    }
  } catch (e) {
    // 静默失败
  }
}
function pollStunStatus() {
  if (statusPollTimer) clearInterval(statusPollTimer)
  statusPollTimer = setInterval(fetchStunStatus, 5000)
}

// 保存当前配置
async function saveCurrentConfig() {
  const profileToSave = activeProfile.value
  if (!profileToSave) return

  // 必填项校验
  if (!profileToSave.name || !profileToSave.name.trim()) {
    toast.error(t('stun.nameRequired'))
    return
  }
  if (!profileToSave.stunConfig?.protocol) {
    toast.error(t('stun.protocolRequired'))
    return
  }
  if (!profileToSave.stunConfig?.bindPort) {
    toast.error(t('stun.bindPortRequired'))
    return
  }

  try {
    if (isDraft.value) {
      const res = await api.stun.saveStun(profileToSave.id, {
        name: profileToSave.name,
        stunConfig: { ...profileToSave.stunConfig },
        changeConfig: { ...profileToSave.changeConfig }
      })
      profileToSave.id = res.data.id
      profiles.push(profileToSave)
      draftProfile.value = null
      activeProfileIndex.value = profiles.length - 1
      editProfile.value = JSON.parse(JSON.stringify(profiles[activeProfileIndex.value]))
    } else {
      // 同步编辑副本回 profiles
      if (editProfile.value) {
        Object.assign(profiles[activeProfileIndex.value], JSON.parse(JSON.stringify(editProfile.value)))
      }
      const p = profiles[activeProfileIndex.value]
      await api.stun.saveStun(p.id, {
        name: p.name,
        stunConfig: { ...p.stunConfig },
        changeConfig: { ...p.changeConfig }
      })
      fetchStunStatus()
    }
    toast.success(t('stun.configSaved'))
  } catch (e) {
    // toast.error(t('stun.configSaveFailed'))
  }
}

// 测试推送 TXT 记录
async function testPushTxtRecord() {
  try {
    const { data } = await api.stun.testPushTxtRecord(activeProfile.value.changeConfig)
    if (data.success) {
      toast.success(t('stun.pushSuccess'))
    }
  } catch (e) {
    toast.error(t('stun.pushFailed'))
  }
}

// 复制文本
async function copyText(text) {
  try {
    await copyToClipboard(text)
    toast.success(t('nodes.copySuccess'))
  } catch (e) {
    toast.error(t('nodes.copyFailed'))
  }
}

onMounted(() => {
  loadConfig()
  checkNatmapVersion()
  pollStunStatus()
})

onUnmounted(() => {
  if (statusPollTimer) {
    clearInterval(statusPollTimer)
    statusPollTimer = null
  }
})
</script>

<style scoped>
.stun-page {
  padding: 16px;
  max-width: 800px;
  margin: 0 auto;
}

.stun-block {
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 12px;
  background: var(--color-surface-container);
}

.block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.block-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.tip-popup-content {
  padding: 16px 20px 20px;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.tip-popup-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.tip-popup-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-on-surface);
}

.tip-popup-content p {
  margin: 0 0 8px 0;
}

.tip-popup-content ul {
  margin: 0;
  padding-left: 20px;
}

.tip-popup-content li {
  margin-bottom: 4px;
}

.setting-link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.setting-link:hover {
  text-decoration: underline;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  gap: 12px;
}

.version-info-block {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.setting-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.version-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-surface);
}

/* 配置列表 */
.profile-list {
  display: flex;
  flex-direction: column;
}

.profile-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px 0;
}

.profile-empty-text {
  font-size: 14px;
  color: var(--color-text-disabled);
}

.profile-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  gap: 8px;
}

.profile-row:hover {
  background: var(--color-surface-container-highest);
}

.profile-row--active {
  background: var(--color-primary-container);
  border-left: 3px solid var(--color-primary);
  padding-left: 9px;
}

.profile-row-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.profile-row-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-row-port {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-family: 'Consolas', 'JetBrains Mono', monospace;
}

.profile-row-mapping {
  font-size: 12px;
  color: var(--color-success);
  font-family: 'Consolas', 'JetBrains Mono', monospace;
  background: rgba(76, 175, 80, 0.08);
  padding: 1px 8px;
  border-radius: 4px;
  word-break: break-all;
  cursor: pointer;
  transition: background 0.15s;
}
.profile-row-mapping:hover {
  background: rgba(76, 175, 80, 0.15);
}

.profile-row-error {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 12px;
  color: var(--color-danger);
  font-family: 'Consolas', 'JetBrains Mono', monospace;
  background: rgba(244, 67, 54, 0.06);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(244, 67, 54, 0.15);
  white-space: pre-wrap;
  word-break: break-all;
  cursor: pointer;
  transition: background 0.15s;
  flex-basis: 100%;
  margin-top: 2px;
  max-height: 66px;
  overflow-y: auto;
}
.profile-row-error:hover {
  background: rgba(244, 67, 54, 0.1);
}

.profile-row-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* 设置栏标题操作按钮 */
.block-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.mapping-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.mapping-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  min-width: 80px;
}

.mapping-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-surface);
  font-family: monospace;
  flex: 1;
}

.mapping-uri {
  color: var(--color-primary);
  cursor: pointer;
  user-select: all;
}

.form-row {
  margin-bottom: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0 16px;
}

.form-row-full {
  grid-column: 1 / -1;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  .form-row-full {
    grid-column: 1;
  }
}

.section-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 12px;
  padding: 6px 0;
}

.section-label > span {
  font-weight: 400;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.form-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.input-with-btn {
  display: flex;
  gap: 8px;
  align-items: center;
}

.block-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 8px;
}

.stun-textarea {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  color: var(--color-on-surface);
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  outline: none;
  resize: vertical;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.stun-textarea:focus {
  border-color: var(--color-primary);
}

.stun-textarea::placeholder {
  color: var(--color-text-disabled);
}

/* 移动端适配 */
@media (max-width: 767px) {
  .stun-page {
    padding: 12px;
  }

  .stun-block {
    padding: 12px;
    margin-bottom: 12px;
  }

  .setting-row {
    flex-wrap: wrap;
  }

  .block-footer {
    flex-direction: column;
  }

  .block-footer .var-button {
    width: 100%;
  }
}
</style>