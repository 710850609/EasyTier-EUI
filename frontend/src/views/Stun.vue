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
      <div class="setting-row">
        <div class="version-info-block">
          <span class="setting-label" v-if="!natTypeResult">{{ $t('stun.natType') }}</span>
          <template v-if="natTypeResult">
            <span class="nat-protocol-label">TCP</span>
            <var-chip :type="getNatTypeChipType(natTypeResult.tcp)" size="mini" plain>
              {{ getNatTypeName(natTypeResult.tcp) }}
            </var-chip>
            <span class="nat-protocol-label">UDP</span>
            <var-chip :type="getNatTypeChipType(natTypeResult.udp)" size="mini" plain>
              {{ getNatTypeName(natTypeResult.udp) }}
            </var-chip>
          </template>
          <span v-else class="version-value" style="color: var(--color-text-disabled);">{{ $t('stun.notChecked') }}</span>
        </div>
        <var-button type="primary" size="small" @click="checkNatType" auto-loading>
          <var-icon name="refresh" />
          {{ $t('stun.checkNatType') }}
        </var-button>
      </div>

      <div v-if="natTypeResult" class="setting-row nat-hint-row" :class="isNatGood ? 'nat-hint--success' : 'nat-hint--warning'">
        <span>{{ isNatGood ? $t('stun.natGoodHint') : $t('stun.natBadHint') }}</span>
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
            <div class="profile-row-info">
              <div class="profile-row-line">
                <span class="profile-row-name">{{ p.name }}</span>
                <var-chip size="mini" plain type="info">
                  {{ p.stunConfig.protocol }}
                </var-chip>
                <var-chip size="mini" plain :type="getProtocolChipType(p.stunConfig.listenProtocol)">
                  <template v-if="p.stunConfig.listenProtocol">
                    {{ p.stunConfig.listenProtocol }}:{{ p.stunConfig.listenPort }}
                  </template>
                </var-chip>
              </div>
              <div class="profile-row-line" v-if="p.running && p.mapping">
                <span class="profile-row-arrow">→</span>
                <span class="profile-row-mapping" @click.stop="copyText(`${p.stunConfig.listenProtocol}://${p.mapping.public_addr}:${p.mapping.public_port}`)">
                  {{ p.stunConfig.listenProtocol }}://{{ p.mapping.public_addr }}:{{ p.mapping.public_port }}
                </span>
              </div>
              <div class="profile-row-line" v-if="p.running && p.error_msg">
                <span class="profile-row-error" @click.stop="copyText(p.error_msg)">{{ p.error_msg }}</span>
              </div>
            </div>
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
          <label class="form-label">{{ $t('stun.listenProtocol') }}</label>
          <var-select
            variant="outlined"
            size="small"
            v-model="activeProfile.stunConfig.listenProtocol"
            @change="onListenProtocolChange"
          >
            <var-option label="tcp" value="tcp" />
            <var-option label="udp" value="udp" />
            <var-option label="quic" value="quic" />
            <var-option label="wg" value="wg" />
            <var-option label="ws" value="ws" />
            <var-option label="wss" value="wss" />
            <var-option label="faketcp" value="faketcp" />
          </var-select>
        </div>

        <div class="form-row">
          <label class="form-label">{{ $t('stun.listenPort') }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.stunConfig.listenPort"
          />
        </div>
      </div>

      <var-divider />

      <!-- 公网IP/端口变更推送 -->
      <div class="section-label">
        {{ $t('stun.changePushLabel') }}
        <span v-if="activeProfile?.changeConfig?.zoneName"> → </span>
        <span v-if="activeProfile?.changeConfig?.zoneName" class="profile-row-mapping" @click="copyText(`txt://${activeProfile.changeConfig.subDomain ? activeProfile.changeConfig.subDomain + '.' : ''}${activeProfile.changeConfig.zoneName}`)">txt://{{ activeProfile.changeConfig.subDomain ? activeProfile.changeConfig.subDomain + '.' : '' }}{{ activeProfile.changeConfig.zoneName }}</span>
      </div>
      <div class="form-grid">
        <div class="form-row">
          <label class="form-label">{{ $t('stun.dnsProvider') }}
            <a v-if="currentProviderWebsite" :href="currentProviderWebsite" target="_blank" class="provider-link">
              &#x2197; {{ $t('stun.website') }}
            </a>
          </label>
          <var-select
            variant="outlined"
            size="small"
            v-model="activeProfile.changeConfig.dnsProvider"
          >
            <var-option label="dynv6" value="dynv6" />
          </var-select>
        </div>

        <div class="form-row" v-for="field in currentProviderFields" :key="field.key">
          <label class="form-label">{{ field.tip }}</label>
          <var-input
            variant="outlined"
            size="small"
            v-model="activeProfile.changeConfig[field.key]"
            :placeholder="field.tip"
          />
        </div>
      </div>

      <div class="block-footer">
        <var-button type="primary" @click="saveCurrentConfig" auto-loading>
          <var-icon name="content-save" />
          {{ $t('common.save') }}
        </var-button>
<!--        <var-button @click="testPushTxtRecord" auto-loading>-->
<!--          <var-icon name="send" />-->
<!--          {{ $t('stun.testPush') }}-->
<!--        </var-button>-->
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

const listenPortDefaults = {
  tcp: '11010',
  udp: '11010',
  wg: '11011',
  ws: '11011',
  wss: '11012',
  quic: '11012',
  faketcp: '11013'
}

function createDefaultProfile(item, index) {
  return reactive({
    id: item.id,
    name: item.name || ('stun-' + (index + 1)),
    running: false,
    mapping: null,
    error_msg: '',
    stunConfig: {
      listenProtocol: 'udp',
      listenPort: '11010',
    },
    changeConfig: {
      dnsProvider: 'dynv6'
    }
  })
}

function onListenProtocolChange(value) {
  if (listenPortDefaults[value] && activeProfile.value) {
    activeProfile.value.stunConfig.listenPort = listenPortDefaults[value]
  }
}

// DNS 服务商元数据：key 为 dnsProvider 值，fields 定义该服务商需要的输入项
// 新增服务商时只需在此处添加元数据即可
const dnsProviderMeta = {
  dynv6: {
    website: 'https://dynv6.com',
    fields: [
      { key: 'zoneName', tip: 'zone', required: true },
      { key: 'httpToken', tip: 'HTTP token', required: true },
      { key: 'subDomain', tip: 'sub domain prefix', required: false },
    ]
  }
}

const currentProviderFields = computed(() => {
  const provider = activeProfile.value?.changeConfig?.dnsProvider
  return dnsProviderMeta[provider]?.fields || []
})

const currentProviderWebsite = computed(() => {
  const provider = activeProfile.value?.changeConfig?.dnsProvider
  return dnsProviderMeta[provider]?.website || ''
})

function getProtocolChipType(protocol) {
  const typeMap = { tcp: 'primary', udp: 'warning', quic: 'success', wg: 'info', ws: 'success', wss: 'info', faketcp: 'warning' }
  // return typeMap[protocol] || 'default'
  return 'primary'
}

// Natmap 信息
const natmapVersion = ref('')
const existsNatmap = ref(false)
const natmapInstalling = ref(false)
const natTypeResult = ref(null)
const showTipPopup = ref(false)

const isNatGood = computed(() => {
  if (!natTypeResult.value) return null
  const tcp = String(natTypeResult.value.tcp)
  const udp = String(natTypeResult.value.udp)
  const good = (v) => v === '0' || v === '1'
  return good(tcp) || good(udp)
})

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

// 检测 NAT 类型
async function checkNatType() {
  try {
    const { data } = await api.stun.natCheck()
    if (data) {
      natTypeResult.value = { tcp: data.tcp, udp: data.udp }
    }
  } catch (e) {
    toast.error(t('stun.checkNatTypeFailed'))
  }
}

// NAT 类型数值 → 显示名称
function getNatTypeName(raw) {
  const v = String(raw)
  if (v === '-1' || v === 'unknown') return 'unknown'
  return 'nat' + (Number(v))
}

function getNatTypeChipType(raw) {
  const v = String(raw)
  if (v === '-1' || v === 'unknown') return 'default'
  const n = Number(v)
  if (n <= 1) return 'success'
  if (n <= 3) return 'warning'
  return 'danger'
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
            stunConfig: info.stunConfig || {},
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
  if (!profileToSave.stunConfig?.listenProtocol) {
    toast.error(t('stun.listenProtocolRequired'))
    return
  }
  if (!profileToSave.stunConfig?.listenPort) {
    toast.error(t('stun.listenPortRequired'))
    return
  }

  // 变更推送必填校验（根据 DNS 服务商元数据）
  for (const field of currentProviderFields.value) {
    if (field.required && !profileToSave.changeConfig?.[field.key]) {
      toast.error(t('validate.required', { label: field.tip }))
      return
    }
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

.nat-protocol-label {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.nat-hint-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-top: 4px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.nat-hint--success {
  background: var(--color-success-container);
  color: var(--color-on-success-container);
}

.nat-hint--warning {
  background: var(--color-warning-container);
  color: var(--color-on-warning-container);
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
  align-items: flex-start;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.profile-row-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.profile-row-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.profile-row-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-row-arrow {
  font-size: 13px;
  color: var(--color-text-disabled);
  font-family: 'Consolas', 'JetBrains Mono', monospace;
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

.provider-link {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
  margin-left: 8px;
}

.provider-link:hover {
  text-decoration: underline;
}
</style>