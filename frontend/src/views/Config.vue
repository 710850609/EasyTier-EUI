<template>
  <div class="config-page">
    <div v-if="isLoadingConfigList" class="config-skeleton">
      <div class="skeleton-toolbar">
        <var-skeleton title :rows="0" />
      </div>
      <div class="skeleton-content">
        <var-paper class="skeleton-paper" :elevation="1">
          <var-skeleton title :rows="0" />
          <var-skeleton :rows="2" />
          <var-skeleton title :rows="0" />
          <var-skeleton :rows="3" />
          <var-skeleton title :rows="0" />
          <var-skeleton :rows="4" />
        </var-paper>
      </div>
    </div>

    <div v-else-if="!fastSettingMode && configList.length === 0" class="empty-state-full">
      <var-icon name="file-document-outline" size="56" color="var(--color-text-disabled)" />
      <p class="empty-title">暂无配置</p>
      <p class="empty-hint">创建第一个配置开始使用 EasyTier</p>
      <var-button type="primary" size="large" @click="showCreateDialog = true">
        <var-icon name="plus" size="18" />
        新增配置
      </var-button>
    </div>

    <template v-else>
      <div class="toolbar" v-if="!fastSettingMode">
        <div class="toolbar-row">
          <div class="toolbar-group toolbar-main">
            <var-select
              class="config-switcher"
              v-model="selectedConfig"
              placeholder="选择配置"
              variant="outlined"
              size="small"
              @change="onConfigSwitch"
            >
              <var-option
                v-for="cfg in configList"
                :key="cfg.profile"
                :label="cfg.name"
                :value="cfg.profile"
              >
                <div class="config-option">
                  <span>{{ cfg.name }}</span>                
                </div>
              </var-option>
            </var-select>

            <div class="config-actions-group" v-if="selectedConfig">
              <var-button size="small" type="primary" @click="showCreateDialog = true">新增</var-button>
              <var-button size="small" type="primary" @click="startEditName">改名</var-button>
              <var-button size="small" type="danger" @click="deleteCurrentConfig">删除</var-button>
            </div>
          </div>

          <div class="toolbar-group toolbar-status" v-if="selectedConfig">
            <div class="toolbar-toggles">
              <label class="toggle-item">
                <span class="toggle-label">开机自启</span>
                <label class="switch-wrapper">
                  <input type="checkbox" :checked="currentConfigAutostart" @change="(e) => handleSwitchChange(currentConfigData, 'autostart', e.target.checked)" />
                  <span class="switch-slider"></span>
                </label>
              </label>
            </div>
          </div>
        </div>

        <div class="toolbar-row toolbar-actions" v-if="selectedConfig">
          <var-button type="primary" size="small" @click="saveConfig" auto-loading>保存配置</var-button>
          <var-button type="primary" size="small" @click="openCodePage" auto-loading>编辑文件</var-button>
          <var-button type="primary" size="small" @click="downloadConfig" auto-loading>分享网络</var-button>
        </div>
      </div>

      <div class="content-area" v-if="selectedConfig">
        <var-form ref="form">
          <var-paper class="config-section merged-section" :elevation="2">
            <!-- 基础设置 -->
            <div class="section-header">
              <div class="section-header-left">
                <svg-icon type="mdi" :path="mdiHomeEdit" width="24" height="24" color="var(--color-primary)" />
                <span class="section-title">{{ fastSettingMode ? '快速设置' : '基础设置' }}</span>
              </div>
            </div>

            <var-skeleton :loading="isLoadingConfig">
              <div class="input-row">
                <var-cell>
                  <var-input
                    v-model="config.network_identity.network_name"
                    placeholder="网络名称"
                    size="small"
                    :rules="[(v) => !!v || '网络名称不能为空']"
                    blur-color="var(--color-primary)"
                  >
                    <template #prepend-icon>
                      <svg-icon type="mdi" :path="mdilAccount"></svg-icon>
                    </template>
                    <template #label>网络名称</template>
                  </var-input>
                </var-cell>
                <var-cell>
                  <var-input
                    v-model="config.network_identity.network_secret"
                    placeholder="网络密码"
                    :type="showPassword ? 'text' : 'password'"
                    :rules="[(v) => !!v || '网络密码不能为空']"
                    size="small"
                    blur-color="var(--color-primary)"
                  >
                    <template #prepend-icon>
                      <svg-icon type="mdi" :path="mdilLock" />
                    </template>
                    <template #label>网络密码</template>
                    <template #append-icon>
                      <svg-icon
                        type="mdi"
                        :path="showPassword ? mdiEyeOff : mdiEye"
                        width="24"
                        height="24"
                        @click="showPassword = !showPassword"
                        style="cursor: pointer; opacity: 0.54;"
                        size="8"
                      />
                    </template>
                  </var-input>
                </var-cell>
              </div>

              <var-cell>
                  <var-cell>
                    <template #icon><div class="section-subtitle">初始节点</div></template>
                    <template #extra>
                       <div class="peer-actions">
                         <var-button type="primary" size="mini" auto-loading @click="refreshPublicPeerOptions">刷新节点</var-button>
                         <var-button type="primary" size="mini" auto-loading @click="checkPeers">检测节点</var-button>
                       </div>
                    </template>
                  </var-cell>
                <var-select
                  variant="outlined"
                  size="small"
                  v-model="config.peer"
                  multiple
                  placeholder="初始节点，用于发现组网设备"
                  :chip="true"
                  blur-color="var(--color-primary)"
                  class="peer-select"
                >
                  <template #default>
                    <var-cell>
                      <template #icon>
                        <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                      </template>
                      <template #description>
                        <var-input placeholder="输入初始节点" size="mini" v-model="customPeer" blur-color="var(--color-primary)" />
                      </template>
                      <template #extra>
                        <var-button type="primary" size="small" @click="addPeer">添加</var-button>
                      </template>
                    </var-cell>
                    <var-option
                      v-for="peer in publicPeerOptions"
                      :key="peer.uri"
                      :label="peer.label || peer.uri"
                      :value="peer.uri"
                    >
                      <var-cell :title="peer.label || peer.uri">
                        <template #extra v-if="peer.status !== undefined">
                          <svg-icon size="16" type="mdi" :path="mdiCircle" :color="peer.status == 1 ? 'var(--color-success)' : 'var(--color-danger)'"></svg-icon>
                        </template>
                      </var-cell>
                    </var-option>
                  </template>
                </var-select>
              </var-cell>
              <var-cell v-if="fastSettingMode">
                <p>
                  <span style="font-size: 14px; color: var(--color-warning); margin-top: 8px;">默认使用动态社区节点用于发现组网节点。如不想用，请刷新页面重新选择正常模式进行配置</span>
                </p>
              </var-cell>
            </var-skeleton>

            <!-- 高级设置 -->
            <var-collapse v-if="!fastSettingMode" v-model="flagsOpen" :accordion="true" class="flags-section-inner" :elevation="12">
              <var-collapse-item name="flags">
                <template #title>
                  <div class="collapse-title">
                    <svg-icon type="mdi" :path="mdiShieldEdit" width="24" height="24" color="var(--color-primary)" />
                    <span class="section-title">高级设置</span>
                  </div>
                </template>
                <var-skeleton :loading="isLoadingConfig">
                  <div class="flags-content">
                    <div class="feature-section">
                      <div class="section-subtitle">功能开关</div>
                      <div class="feature-grid">
                        <div
                          v-for="feature in featureSwitches"
                          :key="feature.key"
                          class="feature-item"
                        >
                          <var-checkbox v-model="config.flags[feature.key]">
                            {{ feature.label }}
                          </var-checkbox>
                          <var-tooltip :content="feature.tooltip" v-if="feature.tooltip">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </var-tooltip>
                        </div>
                      </div>
                    </div>
                    <var-divider />

                    <div class="input-row">
                      <div class="input-section">
                        <div class="section-subtitle">主机名</div>
                        <var-input v-model="config.hostname" placeholder="留空默认为主机名" variant="outlined" size="small" />
                      </div>
                      <div class="input-section">
                        <div class="section-subtitle">虚拟IPv4</div>
                        <var-input v-model="config.ipv4" placeholder="固定虚拟IPv4" variant="outlined" size="small" />
                      </div>
                    </div>

                    <div class="input-row">
                      <div class="input-section">
                        <div class="section-subtitle">TUN接口名称
                          <var-tooltip content="当多个网络同时使用相同的TUN接口名称时，将会在设置TUN的IP时产生冲突" :offset-x="160">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </var-tooltip>
                        </div>
                        <var-input v-model="config.flags.dev_name" placeholder="留空自动生成随机名称" variant="outlined" size="small" />
                      </div>
                      <div class="input-section">
                        <div class="section-subtitle">MTU
                          <var-tooltip content="TUN设备的MTU，默认加密: 1360，不加密: 1380。取值范围 400 ~ 1380" :offset-x="160">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </var-tooltip>
                        </div>
                        <var-input
                          v-model="mtuStr"
                          type="number"
                          :rules="(v) => (v === '' || v >= 400 && v <= 1380) || 'MTU值超出范围[400, 1380]'"
                          placeholder="留空默认加密:1360, 不加密:1380"
                          variant="outlined"
                          size="small"
                        />
                      </div>
                    </div>

                    <div class="input-row">
                      <div class="input-section">
                        <div class="section-subtitle">线程数
                          <var-tooltip content="仅当开启多线程时生效，取值必须大于2" :offset-x="60">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </var-tooltip>
                        </div>
                        <var-input
                          v-model="multiThreadCountStr"
                          placeholder="留空默认为2"
                          variant="outlined"
                          type="number"
                          :rules="(v) => (v === '' || v >= 2) || '线程数必须大于等于2'"
                          size="small"
                        />
                      </div>
                      <div class="input-section">
                        <div class="section-subtitle">加密算法</div>
                        <var-select
                          v-model="config.flags.encryption_algorithm"
                          placeholder="留空默认aes-gcm"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        >
                          <var-option v-for="(e, index) in encryptionAlgorithmList" :key="index" :label="e" :value="e" />
                        </var-select>
                      </div>
                    </div>

                    <div class="input-row">
                      <div class="input-section">
                        <div class="section-subtitle">转发白名单网络
                          <var-tooltip content="仅转发白名单网络的流量，支持通配*符字符串。多个网络名称间可以使用英文空格间隔" :offset-x="60">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </var-tooltip>
                        </div>
                        <var-input
                          v-model="config.flags.relay_network_whitelist"
                          multiple
                          placeholder="网络名称，支持通配*符字符串"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        />
                      </div>
                      <div class="input-section">
                        <div class="section-subtitle">子网代理CIDR</div>
                        <var-select
                          v-model="config.proxy_network"
                          multiple
                          placeholder="子网网段"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        >
                          <var-cell>
                            <template #icon>
                              <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                            </template>
                            <template #description>
                              <var-input placeholder="格式: 192.168.1.1/24 或 192.168.1.1/32 等" size="mini" v-model="customProxyNetwork" blur-color="var(--color-primary)" />
                            </template>
                            <template #extra>
                              <var-button type="primary" size="small" @click="addProxyNetwork">添加</var-button>
                            </template>
                          </var-cell>
                          <var-option v-for="(e, index) in config.proxy_network" :key="index" :label="e" :value="e" />
                        </var-select>
                      </div>
                    </div>

                    <div class="input-row">
                      <div class="input-section">
                        <div class="section-subtitle">默认协议</div>
                        <var-select
                          v-model="config.flags.default_protocol"
                          placeholder="默认协议"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        >
                          <var-option v-for="(e, index) in defaultProtocolList" :key="index" :label="e.label" :value="e.value" />
                        </var-select>
                      </div>
                      <div class="input-section">
                        <div class="section-subtitle">压缩算法</div>
                        <var-select
                          v-model="config.flags.compression"
                          placeholder="默认无"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        >
                          <var-option v-for="(e, index) in compressionOptions" :key="index" :label="e.label" :value="e.value" />
                        </var-select>
                      </div>
                    </div>

                    <div class="input-section">
                      <div class="section-subtitle">监听地址
                        <var-tooltip content="部分协议需要较高版本支持，具体可加ET群咨询" :offset-x="50">
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </var-tooltip>
                      </div>
                      <var-select
                        v-model="config.listeners"
                        multiple
                        placeholder="监听地址"
                        variant="outlined"
                        :chip="true"
                        size="small"
                      >
                        <var-cell>
                          <template #icon>
                            <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                          </template>
                          <template #description>
                            <var-input placeholder="自定义监听" size="mini" v-model="customListener" blur-color="var(--color-primary)" />
                          </template>
                          <template #extra>
                            <var-button type="primary" size="small" @click="addListener">添加</var-button>
                          </template>
                        </var-cell>
                        <var-option v-for="(e, index) in listenerOptions" :key="index" :label="e" :value="e" />
                      </var-select>
                    </div>
                  </div>
                </var-skeleton>
              </var-collapse-item>
            </var-collapse>


          </var-paper>
        </var-form>
      </div>
    </template>

    <var-popup v-model:show="showCodePage" class="code-editor-popup" :close-on-click-overlay="false">
      <div class="code-editor-container">
        <div class="code-editor-header">
          <span class="editor-title">编辑配置文件</span>
          <var-space>
            <var-button type="primary" size="mini" round @click="saveToml" auto-loading>
              <var-icon name="check"/>
            </var-button>
            <var-button type="info" size="mini" round @click="showCodePage = false">
              <var-icon name="window-close"/>
            </var-button>
          </var-space>
        </div>
        <div class="code-editor-content">
          <CodeEditor v-model="configToml" language="toml" style="height: calc(96vh - 60px);" />
        </div>
      </div>
    </var-popup>

    <var-dialog v-model:show="showRenameDialog" @confirm="confirmEditName" @cancel="showRenameDialog = false"
      confirmButtonText="确认" cancelButtonText="取消">
      <template #title>
        <var-icon name="pencil" color="var(--color-primary)" />
        <span>重命名配置</span>
      </template>
      <var-input
        placeholder="请输入新名称"
        v-model="editNameValue"
        :rules="[v => !!v || '名称不能为空']"
      />
    </var-dialog>

    <var-dialog v-model:show="showCreateDialog" @confirm="confirmCreateConfig" @cancel="showCreateDialog = false"
      confirmButtonText="确认" cancelButtonText="取消">
      <template #title>
        <var-icon name="plus-circle" color="var(--color-primary)" />
        <span>新增配置名称</span>
      </template>
      <var-input
        placeholder="请输入配置名称"
        v-model="newConfigName"
        :rules="[v => !!v || '配置名称不能为空']"
      />
    </var-dialog>
  </div>
</template>

<script setup>
import { ref, computed, inject, onMounted, nextTick } from 'vue'
import toast from '../components/toast.js'
import { api } from '../utils/api.js'
import CodeEditor from '../components/CodeEditor.vue'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiEye, mdiEyeOff, mdiHomeEdit, mdiShieldEdit, mdiCircle } from '@mdi/js'
import { mdilPencil, mdilAccount, mdilLock } from '@mdi/light-js'

const fastSettingMode = inject('fastSettingMode', ref(false))
const publicPeerOptions = ref([])
const customPeer = ref('')
const customProxyNetwork = ref('')
const customListener = ref('')
const flagsOpen = ref([])
const form = ref(null)
const showCodePage = ref(false)
const isLoadingConfig = ref(true)
const isLoadingConfigList = ref(true)
const configToml = ref('')
const isRefreshingPublicPeerOptions = ref(false)
const showPassword = ref(false)
const isPeerChecking = ref(false)

const configList = ref([])
const selectedConfig = ref('')
const showCreateDialog = ref(false)
const showRenameDialog = ref(false)
const newConfigName = ref('')
const editNameValue = ref('')
const encryptionAlgorithmList = ref(['aes-gcm','xor','chacha20','aes-gcm','aes-gcm-256','openssl-aes128-gcm','openssl-aes256-gcm','openssl-chacha20'])
const defaultProtocolList = ref([{'label':'默认','value':''},{'label':'tcp','value':'tcp'},{'label':'udp','value':'udp'},{'label':'quic','value':'quic'},{'label':'wg','value':'wg'},{'label':'ws','value':'ws'},{'label':'wss','value':'wss'},{'label':'faketcp','value':'faketcp'}])
const compressionOptions = ref([{'label':'无压缩','value':'none'},{'label':'zstd','value':'zstd'}])

const config = ref({
  hostname: undefined,
  dhcp: true,
  ipv4: '',
  network_identity: { network_name: '', network_secret: '' },
  rpc_portal: '',
  listeners: [],
  peer: [],
  flags: { bind_device: true, multi_thread: true, enable_ipv6: true },
  proxy_network: []
})

const currentConfigData = computed(() => configList.value.find(c => c.profile === selectedConfig.value) || {})
const currentConfigAutostart = computed(() => currentConfigData.value.autostart || false)

const featureSwitches = [
  { key: 'latency_first', label: '开启延迟优先模式', tooltip: '优先选择延迟最低的连接路径' },
  { key: 'multi_thread', label: '启用多线程', tooltip: '启用多线程处理，提高性能' },
  { key: 'private_mode', label: '启用私有模式', tooltip: '启用私有模式，限制节点发现' },
  { key: 'enable_kcp_proxy', label: '启用 KCP 代理', tooltip: '使用 KCP 协议进行数据传输，提高弱网环境下的稳定性 (KCP 代理会优先于 QUIC 代理生效)' },
  { key: 'enable_quic_proxy', label: '启用 QUIC 代理', tooltip: '使用 QUIC 协议进行代理传输' },
  { key: 'disable_kcp_input', label: '禁用 KCP 输入', tooltip: '关闭 KCP 协议的入站连接' },
  { key: 'disable_quic_input', label: '禁用 QUIC 输入', tooltip: '关闭 QUIC 协议的入站连接' },
  { key: 'disable_tcp_hole_punching', label: '禁用 TCP 打洞', tooltip: '关闭 TCP 协议的 NAT 打洞功能' },
  { key: 'disable_udp_hole_punching', label: '禁用 UDP 打洞', tooltip: '关闭 UDP 协议的 NAT 打洞功能' },
  { key: 'disable_sym_hole_punching', label: '禁用对称 NAT 打洞', tooltip: '关闭对称型 NAT 的打洞功能' },
  { key: 'use_smoltcp', label: '使用用户态协议栈', tooltip: '使用用户态TCP/IP协议栈，避免系统防火墙问题无法子网代理或KCP代理' },
  { key: 'proxy_forward_by_system', label: '系统转发', tooltip: '启用系统级 IP 转发' },
  { key: 'p2p_only', label: '仅 P2P', tooltip: '只允许 P2P 连接，不使用中继' },
  { key: 'disable_p2p', label: '禁用 P2P', tooltip: '关闭点对点直连功能，所有流量通过中继' },
  { key: 'enable_exit_node', label: '启用出口节点', tooltip: '允许此节点作为网络的出口' },
  { key: 'enable_encryption', label: '启用加密', tooltip: '开启数据传输加密，提高安全性但性能降低' },
  { key: 'enable_ipv6', label: '启用 IPv6', tooltip: '开启 IPv6 支持' },
  { key: 'no_tun', label: '无 TUN 模式', tooltip: '不使用 TUN 设备。' },
  { key: 'accept_dns', label: '启用魔法 DNS', tooltip: '启用魔法DNS，可使用域名访问其他节点，例如：<主机名>.et.net。 魔法 DNS 目前仅支持在 Windows 和 MacOS 上自动配置系统 DNS，Linux 上需要手动配置 DNS 服务器为 100.100.100.101 才可正常使用' },
  { key: 'relay_all_peer_rpc', label: '转发 RPC 包', tooltip: '允许转发 RPC 数据包' },
  { key: 'bind_device', label: '仅使用物理网卡', tooltip: '只使用物理网卡进行通信，排除虚拟网卡' },
  { key: 'user_stack', label: '使用用户态协议栈', tooltip: '使用用户态网络协议栈代替内核协议栈' },
]

const listenerOptions = ref([
  'tcp://0.0.0.0:11010', 'udp://0.0.0.0:11010', 'wg://0.0.0.0:11011',
  'ws://0.0.0.0:11011', 'wss://0.0.0.0:11012', 'quic://0.0.0.0:11012', 'faketcp://0.0.0.0:11013',
])

const addListener = () => {
  const listener = customListener.value
  if (!listener) return
  config.value.listeners.unshift(listener)
  customListener.value = ''
}

const mtuStr = computed({
  get: () => config.value.flags.mtu != null ? String(config.value.flags.mtu) : '',
  set: (val) => { config.value.flags.mtu = val === '' ? null : parseInt(val, 10) }
})

const multiThreadCountStr = computed({
  get: () => config.value.flags.multi_thread_count != null ? String(config.value.flags.multi_thread_count) : '',
  set: (val) => { config.value.flags.multi_thread_count = val === '' ? null : parseInt(val, 10) }
})

const addPeer = () => {
  const peer = customPeer.value
  if (!peer) return
  publicPeerOptions.value.unshift({ uri: peer, label: peer })
  config.value.peer.unshift(peer)
  customPeer.value = ''
}

const addProxyNetwork = () => {
  const proxy = customProxyNetwork.value
  if (!proxy) return
  config.value.proxy_network.unshift(proxy)
  customProxyNetwork.value = ''
}

const ensureInt = (str) => {
  if (str && typeof str === 'string') return parseInt(str, 10)
  return str
}

const saveConfig = async (start = false) => {
  const valid = await form.value.validate()
  if (!valid) return
  return new Promise((resolve, reject) => {
    let data = { ...config.value }
    data._profile = selectedConfig.value
    data.peer = data.peer.map(e => ({ uri: e }))
    data.proxy_network = data.proxy_network.map(e => ({ cidr: e }))
    data.dhcp = !data.ipv4 || !(data.ipv4.trim())
    if (data.flags.enable_ipv6 === undefined) data.flags.enable_ipv6 = true
    if (data.flags.enable_encryption === undefined) data.flags.enable_encryption = true
    api.configs.save(data).then(res => {
      toast.success('保存配置成功')
      const restartLoading = toast.loading('服务重启中...')
      api.services.restart(selectedConfig.value).then(() => {
        toast.success('服务重启成功')
        if (fastSettingMode.value) {
          toast.info('退出引导设置模式')
          fastSettingMode.value = false
        }
      }).finally(() => {
        restartLoading.clear()
        resolve()
      })
    }).catch(e => reject(e))
  })
}

const downloadConfig = () => {
  const url = api.configs.getDownloadUrl(selectedConfig.value)
  window.open(url, '_blank')
}

const openCodePage = () => {
  return new Promise((resolve, reject) => {
    api.configs.getToml(selectedConfig.value).then(res => {
      configToml.value = res.data
      showCodePage.value = true
      resolve()
    }).catch(e => reject(e))
  })
}

const saveToml = () => {
  return new Promise((resolve, reject) => {
    api.configs.saveToml({ toml: configToml.value, _profile: selectedConfig.value }).then(res => {
      const restartLoading = toast.loading('保存成功，服务重启中...')
      api.services.restart(selectedConfig.value).then(() => {
        toast.success('服务重启成功')
        loadConfig(selectedConfig.value)
      }).finally(() => {
        restartLoading.clear()
        resolve()
      })
    }).catch(e => reject(e))
  })
}

const refreshPublicPeerOptions = () => {
  isRefreshingPublicPeerOptions.value = true
  return new Promise((resolve) => {
    api.peers.publicPeers({ refresh: true }).then(data => {
      publicPeerOptions.value = data.data
      toast.success('刷新可选节点成功')
    }).finally(() => {
      isRefreshingPublicPeerOptions.value = false
      resolve()
    })
  })
}

const checkPeers = () => {
  if (isPeerChecking.value) {
    toast.warning('检测节点可用状态中，请稍后...')
    return
  }
  toast.info('开始检测节点可用状态，这可能需要一些时间，请稍后...')
  return new Promise((resolve, reject) => {
    isPeerChecking.value = true
    api.peers.checkPeers().then(data => {
      publicPeerOptions.value = data.data.sort((a, b) => b.status - a.status)
      toast.success('检测节点可用状态成功，请点击初始化节点列表查看')
    }).catch(() => {
      toast.error('检测节点可用状态失败')
    }).finally(() => {
      isPeerChecking.value = false
      resolve()
    })
  })
}

const loadConfig = (profile) => {
  isLoadingConfig.value = true
  return api.configs.get(profile).then(data => {
    const json = data.data
    json.peer = (json.peer || []).map(e => e.uri)
    json.proxy_network = (json.proxy_network || []).map(e => e.cidr)
    if (json.listeners) {
      json.listeners.forEach(e => {
        if (!listenerOptions.value.includes(e)) listenerOptions.value.unshift(e)
      })
    }
    if (json.flags?.mtu) json.flags.mtu = ensureInt(json.flags.mtu)
    if (json.flags?.multi_thread_count) json.flags.multi_thread_count = ensureInt(json.flags.multi_thread_count)
    config.value = {
      ...config.value,
      ...json,
      hostname: json.hostname || undefined,
      ipv4: json.ipv4 || undefined,
      flags: {
        ...config.value.flags,
        ...json.flags,
        mtu: json.flags?.mtu || undefined,
        multi_thread_count: json.flags?.multi_thread_count || undefined
      }
    }
  }).finally(() => {
    isLoadingConfig.value = false
  })
}

const loadConfigs = async () => {
  try {
    const res = await api.configs.listConfigFiles()
    if (res && res.data) {
      await nextTick()
      configList.value = res.data
    } else {
      configList.value = []
    }
  } catch (error) {
    toast.error('加载配置列表失败: ' + (error.message || '未知错误'))
  } finally {
    isLoadingConfigList.value = false
  }
}

const loadedProfiles = ref(new Set())

const onConfigSwitch = async (profile) => {
  const cfg = configList.value.find(c => c.profile === profile)
  if (cfg) {
    try {
      if (!loadedProfiles.value.has(profile)) {
        await loadConfig(cfg.profile)
        loadedProfiles.value.add(profile)
      }
    } catch (error) {
      toast.error('加载配置失败: ' + (error.message || '未知错误'))
    }
  }
}

const deleteCurrentConfig = async () => {
  const cfg = currentConfigData.value
  if (!cfg || !cfg.profile) return
  if (cfg.running) {
    toast.warning('请先停止服务再删除配置')
    return
  }
  try {
    await api.configs.delete(cfg.profile)
    toast.success('配置已删除')
    await loadConfigs()
    if (configList.value.length > 0) {
      selectedConfig.value = configList.value[0].profile
      await loadConfig(configList.value[0].profile)
    } else {
      selectedConfig.value = ''
    }
  } catch (error) {
    toast.error('删除配置失败: ' + error.message)
  }
}

const confirmCreateConfig = () => {
  if (!newConfigName.value.trim()) {
    toast.warning('请输入配置名称')
    return
  }
  const name = newConfigName.value.trim()
  const profile = `${name}.toml`
  config.value._profile = profile
  config.value.hostname = undefined
  config.value.dhcp = true,
  config.value.ipv4 =  '',
  config.value.network_identity = { network_name: '', network_secret: '' },
  config.value.rpc_portal = '',
  config.value.listeners = []
  config.value.peer = []
  config.value.flags = { bind_device: true, multi_thread: true, enable_ipv6: true }
  config.value.proxy_network = []
  configList.value.push({ 'profile': profile, 'name': name, 'autostart': false })
  selectedConfig.value = profile
  loadedProfiles.value.add(profile)
  newConfigName.value = ''
  isLoadingConfig.value = false
}

const startEditName = () => {
  const cfg = currentConfigData.value
  editNameValue.value = cfg.name || ''
  showRenameDialog.value = true
}

const confirmEditName = async () => {
  const newName = editNameValue.value.trim()
  if (!newName) {
    toast.warning('请输入新名称')
    return
  }
  if (newName === currentConfigData.value.name) {
    showRenameDialog.value = false
    return
  }
  try {
    const res = await api.configs.rename(selectedConfig.value, newName)
    selectedConfig.value = res.data.profile
    toast.success('重命名成功')
    showRenameDialog.value = false
    await loadConfigs()
  } catch (error) {
    toast.error('重命名失败: ' + error.message)
  }
}

const handleSwitchChange = async (cfg, field, val) => {
  cfg[field] = val
  if (field === 'autostart') {
    try {
      await api.services.autoStart(cfg.profile, val)
      toast.success(val ? '已开启开机自启' : '已关闭开机自启')
    } catch (error) {
      cfg[field] = !val
      toast.error('操作失败: ' + error.message)
    }
  }
}

onMounted(async () => {
  await loadConfigs()
  if (configList.value.length > 0) {
    selectedConfig.value = configList.value[0].profile
    await loadConfig(configList.value[0].profile)
    loadedProfiles.value.add(configList.value[0].profile)
  }
  api.peers.publicPeers().then(data => {
    publicPeerOptions.value = data.data
    if (fastSettingMode.value && config.value.peer.length === 0) {
      newConfigName.value = '默认'
      confirmCreateConfig()
      const peers = publicPeerOptions.value.slice(0, 3).map(e => e.uri)
      config.value.peer.unshift(...peers)
      isLoadingConfig.value = false
    }    
  })
})
</script>

<style scoped>
.config-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px);
  overflow: hidden;
}

.config-skeleton {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.skeleton-toolbar {
  flex-shrink: 0;
  margin: 12px 16px 0;
  padding: 12px 20px;
  border-radius: 12px;
  background: var(--color-surface-container);
}

.skeleton-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.skeleton-paper {
  padding: 20px;
  border-radius: 16px;
  background: var(--color-surface-container) !important;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.empty-state-full {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 16px;
  padding: 48px 24px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.empty-hint {
  font-size: 14px;
  color: var(--color-text-disabled);
  margin: 0 0 8px;
}

.toolbar {
  flex-shrink: 0;
  margin: 16px 16px 0;
  padding: 16px 20px;
  background: var(--color-surface-container);
  border: 1px solid var(--color-outline-variant);
  border-radius: 12px;
}

.toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-main {
  flex: 1;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.toolbar-status {
  margin-left: auto;
  gap: 12px;
  flex-shrink: 0;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-outline-variant);
  margin-top: 8px;
}

.toolbar-toggles {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-actions-group {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: 4px;
}

.config-switcher {
  min-width: 200px;
  max-width: 300px;
}

.config-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-option-dot.running {
  background: var(--color-success);
}

.toggle-item {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.toggle-label {
  font-size: 12px;
  color: var(--color-on-surface-variant);
  white-space: nowrap;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
  margin-top: 4px;
  position: relative;
}

.config-section {
  margin: 0 0 16px;
  padding: 20px;
  border-radius: 16px;
  background: var(--color-surface-container) !important;
}

.merged-section {
  display: flex;
  flex-direction: column;
  padding-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.section-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}

.peer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flags-section {
  margin-top: 16px;
  border-radius: 16px;
  overflow: hidden;
  background: var(--color-surface-container) !important;
}

.flags-section-inner {
  margin-top: 8px;
}

:deep(.flags-section .var-collapse-item) {
  border-radius: 16px;
  overflow: hidden;
  background: var(--color-surface-container) !important;
}

:deep(.flags-section-inner .var-collapse-item) {
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-surface-container-high) !important;
}

:deep(.flags-section-inner .var-collapse-item__header) {
  padding: 12px 16px;
}

:deep(.flags-section-inner .var-divider) {
  margin: 8px 0;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.flags-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 8px 0;
}

.section-subtitle {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
}

.feature-section {
  margin-bottom: 8px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.help-icon {
  color: var(--color-primary);
  cursor: pointer;
  transition: color 0.2s;
}

.help-icon:hover {
  color: var(--color-info);
}

.input-section {
  display: flex;
  flex-direction: column;
}

.input-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.peer-select {
  max-width: 100%;
}

.peer-select :deep(.var-select__select) {
  max-height: 120px;
  overflow-y: auto;
}

.peer-select :deep(.var-chip) {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.var-select__select) {
  max-height: 120px;
  overflow-y: auto;
}

:deep(.var-chip) {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.switch-wrapper {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;
  cursor: pointer;
}

.switch-wrapper input {
  opacity: 0;
  width: 0;
  height: 0;
}

.switch-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-text-disabled);
  border-radius: 10px;
  transition: background-color 0.2s;
}

.switch-slider::before {
  content: '';
  position: absolute;
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}

.switch-wrapper input:checked + .switch-slider {
  background-color: var(--color-primary);
}

.switch-wrapper input:checked + .switch-slider::before {
  transform: translateX(16px);
}

.code-editor-popup {
  :deep(.var-popup__content) {
    width: 98vw !important;
    height: 96vh !important;
    max-width: 1600px !important;
    max-height: 1000px !important;
    background: #0d1117 !important;
    border-radius: 16px !important;
    border: 1px solid rgba(48, 54, 61, 0.4) !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6),
                0 0 0 1px rgba(255, 255, 255, 0.03) inset !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
  }
}

.code-editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background: #0d1117;
}

.code-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: var(--color-surface-container) !important;
  border-bottom: 1px solid var(--color-outline);
  flex-shrink: 0;
}

.code-editor-header :deep(.var-button--mini) {
  min-width: 24px !important;
  height: 24px !important;
  padding: 0 4px !important;
}

.code-editor-header :deep(.var-button--mini .var-icon) {
  font-size: 16px !important;
}

.editor-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 0.5px;
}

.code-editor-content {
  padding: 0;
  background: #0d1117;
}

:deep(.var-form) {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

:deep(.var-collapse-item__content) {
  padding: 8px 16px 16px;
}

:deep(.var-input__input) {
  color: var(--color-text);
}

:deep(.var-input__placeholder) {
  color: var(--color-text-disabled);
}

:deep(.var-input__label) {
  color: var(--color-text);
}

:deep(.var-select__label) {
  color: var(--color-text);
}

:deep(.var-select__placeholder) {
  color: var(--color-text-disabled);
}

:deep(.var-chip) {
  background: var(--color-primary-container) !important;
  color: var(--color-on-primary-container) !important;
}

:deep(.var-chip__close) {
  color: var(--color-on-primary-container) !important;
}

:deep(.var-checkbox__text) {
  color: var(--color-text);
}

:deep(.var-collapse-item__header) {
  color: var(--color-text);
}

:deep(.var-collapse-item__title) {
  color: var(--color-text);
}

.code-editor-content::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

.code-editor-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 5px;
}

.code-editor-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #6366f1 0%, #a855f7 100%);
  border-radius: 5px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.code-editor-content::-webkit-scrollbar-thumb:hover {
  background: #484f58;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.is-spinning {
  animation: spin 1s linear infinite;
}

@media (max-width: 767px) {
  .config-page {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 56px);
    overflow: hidden;
  }

  .toolbar {
    flex-shrink: 0;
    margin: 16px;
    padding: 12px;
    border-radius: 10px;
  }

  .toolbar-row {
    gap: 8px;
  }

  .toolbar-main {
    width: 100%;
  }

  .toolbar-status {
    margin-left: 0;
    width: 100%;
    justify-content: space-between;
  }

  .toolbar-toggles {
    margin-left: auto;
  }

  .config-actions-group {
    margin-left: auto;
  }

  .config-switcher {
    min-width: 120px;
    max-width: 160px;
  }

  .content-area {
    padding: 12px;
  }

  .section-header {
    margin-bottom: 12px;
  }

  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .input-row {
    grid-template-columns: 1fr;
  }

  .code-editor-popup {
    :deep(.var-popup__content) {
      width: 100vw !important;
      height: 100vh !important;
      max-width: 100vw !important;
      max-height: 100vh !important;
      border-radius: 0 !important;
    }
  }

  .code-editor-header {
    padding: 12px 16px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .editor-title {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>