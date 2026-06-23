<template>
  <div class="config-page">
    <div v-if="isLoadingConfigList" class="config-skeleton">
      <div class="skeleton-toolbar">
        <var-skeleton title :rows="1" />
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
      <var-button type="primary" size="large" @click="setupShowMode(1);" auto-loading>
        <var-icon name="plus" size="18" />
        快速新增
      </var-button>
      <var-button type="primary" size="large" @click="setupShowMode(2);" auto-loading>
        <var-icon name="plus" size="18" />
        普通新增
      </var-button>
    </div>

    <template v-else>
      <var-paper class="toolbar" :elevation="2" v-if="!fastSettingMode">
        <div class="toolbar-row">
          <div class="toolbar-group toolbar-main">
            <var-select
              class="config-switcher"
              v-model="selectedConfig"
              placeholder="选择配置"
              variant="outlined"
              size="small"
              blur-color="var(--color-primary)"
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
              <var-button size="small" type="primary" @click="showCreateDialog = true; showMode = 1;" v-if="showMode === 0">新增</var-button>
              <var-button size="small" type="primary" @click="startEditName" :loading="isRenaming" v-if="showMode === 0">改名</var-button>
              <!-- <var-button size="small" type="danger" @click="showDeleteDialog = true" :loading="isDeletingConfig" v-if="showMode === 0">删除</var-button> -->
              <var-button size="small" type="danger" @click="exitAddMode" :loading="isDeletingConfig" v-if="showMode !== 0">退出新增</var-button>
              <label class="toggle-item">
                <var-loading v-if="changingAutostart" size="small" />
                <label class="switch-wrapper" v-if="!changingAutostart">
                  <input type="checkbox" :checked="currentConfigAutostart" @change="(e) => handleSwitchChange(currentConfigData, 'autostart', e.target.checked)" />
                  <span class="switch-slider"></span>
                </label>
                <span class="toggle-label">自启</span>
              </label>
            </div>
          </div>
          <var-divider class="toolbar-divider" />
          <div class="toolbar-group toolbar-status" v-if="selectedConfig">
            <div class="toolbar-toggles">
              <!-- <label class="toggle-item">
                <span class="toggle-label">开机自启</span>
                <var-loading v-if="changingAutostart" size="small" />
                <label class="switch-wrapper" v-if="!changingAutostart">
                  <input type="checkbox" :checked="currentConfigAutostart" @change="(e) => handleSwitchChange(currentConfigData, 'autostart', e.target.checked)" />
                  <span class="switch-slider"></span>
                </label>
              </label> --> 
              <div class="toggle-item">
                <var-button type="primary" size="small" @click="saveConfig" auto-loading>保存配置</var-button>
                <var-button type="primary" size="small" @click="openCodePage" auto-loading v-if="showMode === 0">编辑文件</var-button>
                <var-button type="primary" size="small" @click="showShareConfigType = true" v-if="showMode === 0">分享网络</var-button>
                <var-button size="small" type="danger" @click="showDeleteDialog = true" :loading="isDeletingConfig" v-if="showMode === 0">删除</var-button>

              </div>
            </div>
          </div>
        </div>
        
        <!-- <var-divider />
        <div class="toolbar-row toolbar-actions">
          <var-button type="primary" size="small" @click="saveConfig" auto-loading>保存配置</var-button>
          <var-button type="primary" size="small" @click="openCodePage" auto-loading v-if="showMode === 0">编辑文件</var-button>
          <var-button type="primary" size="small" @click="showShareConfigType = true" v-if="showMode === 0">分享网络</var-button>
        </div> -->
      </var-paper>

      <div class="content-area" v-if="selectedConfig || fastSettingMode">
        <var-form ref="form">
          <var-paper class="config-section merged-section" :elevation="2">
            <!-- 基础设置 -->
            <div class="section-header">
              <div class="section-header-left">
                <svg-icon type="mdi" :path="mdiHomeEdit" width="24" height="24" color="var(--color-primary)" />
                <span class="section-title">{{ fastSettingMode ? '快速设置' : '基础设置' }}</span>
              </div>
              <div v-if="fastSettingMode && !isLoadingConfig && publicPeerOptions.length > 0">
                <span class="fast-setting-hint">填写网络名称和密码，后点击即可 -&gt; </span>
                <var-button type="primary" size="small" @click="saveConfig" auto-loading>保存并启动</var-button>
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
                    variant="outlined"
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
                    variant="outlined"
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
                        class="eye-icon"
                        size="8"
                      />
                    </template>
                  </var-input>
                </var-cell>
              </div>

              <var-cell v-if="!fastSettingMode" class="peer-cell">
                <div class="peer-cell-header">
                  <div class="section-subtitle">
                    初始节点
                    <var-icon name="information-outline" size="12pt" @click="showPublicPeerTip = true" color="var(--color-primary)" />
                  </div>                    
                  <!-- <div class="peer-actions">
                    <var-button type="primary" size="mini" auto-loading @click="refreshPublicPeerOptions">获取最新节点</var-button>
                    <var-button type="primary" size="mini" auto-loading @click="checkPeers">检测节点</var-button>
                  </div> -->
                </div>
                
                <var-select
                  variant="outlined"
                  size="small"
                  v-model="config.peer"
                  multiple
                  :placeholder="`${config.peer.length} 个节点，用于发现组网设备`"
                  :chip="true"
                  class="peer-select"
                >
                  <template #default>
                    <div class="peer-custom-input">
                      <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" size="20" />
                      <var-input 
                        placeholder="输入自定义节点，例如 tcp://1.2.3.4:11010" 
                        size="small" 
                        v-model="customPeer" 
                        class="peer-custom-field"
                      />
                      <var-button type="primary" size="small" @click="addPeer">添加</var-button>
                    </div>
                    
                    <div class="peer-options-list">
                      <var-option
                        v-for="peer in publicPeerOptions"
                        :key="peer.uri"
                        :value="peer.uri"
                        :label="peer.uri"
                        class="peer-option-wrapper"
                      >
                      <var-cell>
                        <template #description>
                          <!-- 左侧：地址信息 -->
                          <div class="peer-info">
                            <div class="peer-primary-uri">
                              {{ peer.uri }}
                            </div>
                            <span style="font-size: 12px; color: var(--color-primary);">{{ peer.hostname || '' }}</span>
                            <!-- <span v-if="peer.src_uri != peer.uri && peer.dynamic">{{ peer.src_uri }}</span> -->
                            <div class="peer-secondary-uri">
                              <span class="peer-tag latency-tag" :class="peer.latency < 500 ? (peer.latency < 100 ? 'latency-good' : 'latency-normal') : 'latency-bad'"  
                                v-if="peer.latency > 0">
                                {{ peer.latency }}ms
                              </span>
                              <span class="peer-tag relay-tag" v-if="peer.relay == 1">可中转</span>
                              <span class="peer-tag dynamic-tag" v-if="peer.dynamic">动态</span>
                            </div>
                          </div>
                        </template>
                        <template #extra>
                          <!-- 右侧：状态标识 -->
                          <div class="status-dot" v-if="peer.status in [0, 1]" :class="peer.status == 1 ? 'status-online' : 'status-offline'"></div>
                          <div class="peer-status-area"></div>
                        </template>
                      </var-cell>
                      </var-option>
                    </div>
                  </template>
                  <template #append-icon>
                    <var-icon 
                      name="refresh" 
                      :class="{ 'is-spinning': isRefreshingPublicPeerOptions }"
                      color="var(--color-primary)"
                      @click.stop="refreshPublicPeerOptions(true, true)"
                    />
                  </template>
                </var-select>
              </var-cell>
              
              <var-cell v-if="fastSettingMode">
                <div class="fast-setting-mode-hint">
                  <p>
                    <span>默认开机自启、使用社区节点用于发现组网节点。</span>
                    <var-icon name="help-circle-outline" size="12pt" @click="showPublicPeerTip = true" class="help-icon" />
                  </p>
                  <p>
                    <span>如不想用，请 <var-button type="primary" size="mini" @click="fastSettingMode = false">重新选择</var-button> 普通模式进行配置</span>
                  </p>
                </div>
              </var-cell>
            </var-skeleton>
          </var-paper>

          <!-- 高级设置 -->
          <var-paper v-if="!fastSettingMode" :elevation="3" class="flags-section-paper">
            <var-collapse v-model="flagsOpen" :accordion="true" class="flags-section-inner">
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
                        <var-tooltip v-if="feature.tooltip" teleport="body">
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          <template #content>
                            <div class="tooltip-multiline">
                              {{ feature.tooltip }}
                            </div>
                          </template>
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
                      <var-tooltip trigger="click">
                        <div class="section-subtitle">TUN接口名称
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                        <template #content>
                          <div class="tooltip-multiline">
                            当多个网络同时使用相同的TUN接口名称时，将会在设置TUN的IP时产生冲突
                          </div>
                        </template>
                      </var-tooltip>
                      <var-input v-model="config.flags.dev_name" placeholder="留空自动生成随机名称" variant="outlined" size="small" />
                    </div>
                    <div class="input-section">
                      <var-tooltip trigger="click">
                        <div class="section-subtitle">MTU
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                        <template #content>
                          <div class="tooltip-multiline">
                            TUN设备的MTU，取值范围 400 ~ 1380<br/>默认加密: 1360，不加密: 1380。
                          </div>
                        </template>
                      </var-tooltip>
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
                      <var-tooltip content="仅当开启多线程时生效，取值必须大于2" trigger="click">
                        <div class="section-subtitle">线程数
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                      </var-tooltip>
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
                      <var-tooltip content="仅转发白名单网络的流量，支持通配*符字符串。多个网络名称间可以使用英文空格间隔" trigger="click">
                          <div class="section-subtitle">转发白名单网络
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                      </var-tooltip>
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
                        <var-option v-for="(e, index) in proxyNetworkOptions" :key="index" :label="e" :value="e" />
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
                      <var-tooltip content="部分协议需要较高版本支持" trigger="click">
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

    <var-popup v-model:show="showCodePage" class="code-editor-popup" :close-on-click-overlay="false" :style="{ width: '100vw', height: '100vh', position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, margin: 0, padding: 0, maxWidth: 'none', maxHeight: 'none' }">
      <div class="code-editor-wrapper">
        <div class="code-editor-header">
          <span class="editor-title">编辑配置【{{ currentConfigData.name }}】</span>
          <var-space>
            <var-button type="primary" size="mini" round @click="saveToml" auto-loading>
              <var-icon name="check"/>
            </var-button>
            <var-button type="info" size="mini" round @click="showCodePage = false">
              <var-icon name="window-close"/>
            </var-button>
          </var-space>
        </div>
        <div class="code-editor-content-area">
          <CodeEditor v-model="configToml" language="toml" class="code-editor-inner" />
        </div>
      </div>
    </var-popup>

    <var-dialog v-model:show="showRenameDialog" @before-close="confirmEditName"
      confirmButtonText="确认" cancelButtonText="取消">
      <template #title>
        <span>重命名配置名称</span>
      </template>
      <var-input
        size="small"
        variant="outlined"
        placeholder="请输入新名称"
        v-model="editNameValue"
        :rules="[v => !!v || '名称不能为空']"
      />
    </var-dialog>

    <var-dialog v-model:show="showCreateDialog" @confirm="confirmCreateConfig" @cancel="exitAddMode"
      confirmButtonText="确认" cancelButtonText="取消">
      <template #title>
        <span>新增配置名称</span>
      </template>
      <var-input
        size="small"
        variant="outlined"
        placeholder="请输入配置名称"
        v-model="newConfigName"
        :rules="[v => !!v || '配置名称不能为空']"
      />
    </var-dialog>

    <var-dialog v-model:show="showShareConfigType" title="选择分享类型"
      confirmButtonText="下载文件"  @confirm="downloadConfig" 
      cancelButtonText="复制到剪贴板" @cancel="copyConfig">
    </var-dialog>

    <var-dialog v-model:show="showDeleteDialog" :title="`确认删除配置【${currentConfigData.name}】?`"
      confirmButtonText="确认"  @confirm="deleteCurrentConfig" 
      cancelButtonText="取消" @cancel="showDeleteDialog = false">
    </var-dialog>

    <var-popup position="top" v-model:show="showPublicPeerTip">
      <div class="help-content">
        <p class="help-paragraph"><span class="help-bold">初始节点</span>：用于发现组网设备，数据来自网络社区</p>
        <p class="help-paragraph"><span class="help-bold">动态节点</span>：原始节点经过TXT协议转换而来。为后续支持社区节点下线时，在不重启服务情况下，持续组网</p>
        <p class="help-paragraph"><span class="help-bold">节点刷新</span>：在线获取易组网维护的初始节点数据</p>
        <p class="help-paragraph"><span class="help-bold">节点检测</span>：基于易组网本地设备网络，检测节点的是否可用、延迟、是否可转发</p>
        <div style="margin-top: 20px;">
          <p class="help-paragraph"><span class="help-bold">感谢以下社区节点服务提供者</span></p>
          <var-table scroller-height="280px">
            <thead>
              <tr>
                <th>社区节点</th>
                <th>提供者</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in publicPeerOptions" :key="item.uri">
                <td v-if="item.owner !== ''">{{ item.uri }}</td>
                <td v-if="item.owner !== ''">{{ item.owner }}</td>
              </tr>
            </tbody>
          </var-table>
        </div>
      </div>
  </var-popup>
  </div>
</template>

<script setup>
import { copyToClipboard } from '../utils/clipboard.js'
import { ref, computed, inject, onMounted, nextTick } from 'vue'
import toast from '../components/toast.js'
import { api } from '../utils/api.js'
import CodeEditor from '../components/CodeEditor.vue'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiEye, mdiEyeOff, mdiHomeEdit, mdiShieldEdit, mdiCircle } from '@mdi/js'
import { mdilPencil, mdilAccount, mdilLock } from '@mdi/light-js'


// 显示模式： 0 编辑 1 快速新增 2 普通新增
const showMode = ref(0)
const fastSettingMode = inject('fastSettingMode', ref(false))
const publicPeerOptions = ref([])
const customPeer = ref('')
const customProxyNetwork = ref('')
const customListener = ref('')
const flagsOpen = ref(['flags'])
const form = ref(null)
const showShareConfigType = ref(false)
const showCodePage = ref(false)
const isLoadingConfig = ref(false)
const isLoadingConfigList = ref(true)
const configToml = ref('')
const isRefreshingPublicPeerOptions = ref(false)
const showPassword = ref(false)
const isPeerChecking = ref(false)
const changingAutostart = ref(false)
const isRenaming = ref(false)
const showDeleteDialog = ref(false)
const isDeletingConfig = ref(false)
const showPublicPeerTip = ref(false)
const lanIps = ref([])

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
  hostname: '',
  dhcp: true,
  ipv4: '',
  network_identity: { network_name: '', network_secret: '' },
  listeners: [],
  peer: [],
  proxy_network: [],
  flags: { 
    bind_device: true, 
    multi_thread: true, 
    enable_ipv6: true,
    private_mode: true,
    // latency_first: true,
    // dev_name: '',
    // compression: '',
  },
})

const currentConfigData = computed(() => configList.value.find(c => c.profile === selectedConfig.value) || {})
const currentConfigAutostart = computed(() => currentConfigData.value.autostart || false)
const proxyNetworkOptions = computed(() => 
  [...new Set([
    ...(config.value.proxy_network || []), 
    ...(lanIps.value || [])
  ])]
)

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
  { key: 'accept_dns', label: '启用魔法 DNS', tooltip: '启用魔法DNS，可使用域名访问其他节点，例如：<主机名>.et.net。魔法 DNS 目前仅支持在 Windows 和 MacOS 上自动配置系统 DNS，Linux 上需要手动配置 DNS 服务器为 100.100.100.101 才可正常使用' },
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
  publicPeerOptions.value.unshift({ uri: peer, src_uri: peer, latency: -1, status: -1 })
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

const saveConfig = () => {
  return new Promise(async (resolve, reject) => {
    const valid = await form.value.validate()
    if (!valid) {
      reject();
      return
    }      

    const checkStatus = async () => {
      return await api.services.status(selectedConfig.value).then(resp => resp.data).catch(e => {
        console.error('检查服务状态失败: ' + e.message)
        return false
      })
    }
    const autoStart = async () => {
      return await api.services.autoStart(selectedConfig.value, true)
        .then(() => {
          toast.success('设置服务开机启动成功')
          currentConfigData.value.autostart = true
          currentConfigAutostart.value = true
        }).catch(e => {
          toast.error('设置服务开机启动失败: ' + e.message)
        })
    }
    let data = { ...config.value }
    if (fastSettingMode.value) {
      // 快速设置模式，配置文件名同网络名称
      const networkName = data.network_identity.network_name || '默认'
      selectedConfig.value = networkName + '.toml'
      currentConfigData.value.name = selectedConfig.value 
      configList.value.push({ 'profile': selectedConfig.value, 'name': networkName, 'autostart': false })
    }
    data._profile = selectedConfig.value
    data.peer = data.peer.map(e => ({ uri: e }))
    data.proxy_network = data.proxy_network.map(e => ({ cidr: e }))
    data.dhcp = !data.ipv4 || !(data.ipv4.trim())
    if (data.flags.enable_ipv6 === undefined) data.flags.enable_ipv6 = true
    if (data.flags.enable_encryption === undefined) data.flags.enable_encryption = true
    api.configs.save(data).then(async res => {
      toast.success('保存配置成功')
      if (fastSettingMode.value) {
        // 快速设置模式，自动开启启动服务
        await autoStart()
      }
      if (fastSettingMode.value || await checkStatus()) {
        const restartLoading = toast.loading(fastSettingMode.value ? '服务启动中...' : '服务重启中...')
            await api.services.restart(selectedConfig.value).then(() => {
              toast.success('服务启动成功')
            }).finally(() => {
              restartLoading.clear()
            })
      }      
      if (fastSettingMode.value) {
        toast.info('退出引导设置模式')
        fastSettingMode.value = false
      }
      if (showMode.value != 0) {
        exitAddMode()
      }
    }).catch(e => {
      toast.error('保存配置失败: ' + e.message)
      reject(e)
    }).finally(() => {
      resolve()
    })
  })
}

const downloadConfig = () => {
  const url = api.configs.getShareConfigDownloadUrl(selectedConfig.value)
  window.open(url, '_blank')
}

const copyConfig = () => {
  api.configs.getShareConfigStr(selectedConfig.value).then(resp => {
    copyToClipboard(resp.data)
    toast.success('已复制配置到剪贴板')
  })
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
      toast.success('保存配置成功')
      // 先检查服务状态，只有运行中才重启
      api.services.status(selectedConfig.value).then(resp => {
        if (resp.data) {
          const restartLoading = toast.loading('服务重启中...')
          api.services.restart(selectedConfig.value).then(() => {
            toast.success('服务重启成功')
            loadConfig(selectedConfig.value)
          }).finally(() => {
            restartLoading.clear()
            resolve()
          })
        } else {
          // 服务未运行，跳过重启
          loadConfig(selectedConfig.value)
          resolve()
        }
      }).catch(e => {
        console.error('检查服务状态失败:', e)
        loadConfig(selectedConfig.value)
        resolve()
      })
    }).catch(e => reject(e))
  })
}

const refreshPublicPeerOptions = (refresh = false, doCheck = false) => {
  isRefreshingPublicPeerOptions.value = true
  return new Promise((resolve, reject) => {
    api.peers.publicPeers({ 'profile': selectedConfig.value, 'refresh': refresh }).then(async (data) => {
      publicPeerOptions.value = data.data
      if (refresh) {
        toast.success('已获取最新节点')
      }
      const hasAvailable = data.data.filter(e => e.status == 1).length > 0
      if (doCheck || !hasAvailable) {
        await checkPeers()
      }
    }).finally(() => {
      isRefreshingPublicPeerOptions.value = false
      resolve()
    })
  })
}

const checkPeers = () => {
  return new Promise((resolve, reject) => {
    if (isPeerChecking.value) {
      toast.warning('检测节点可用状态中，请稍后...')
      return
    }
    const checkToast = toast.info('开始检测节点可用状态，这可能需要一些时间，请稍后...', 30000)
    isPeerChecking.value = true
    api.peers.checkPeers({ 'profile': selectedConfig.value, 'refresh': true }).then(data => {
      publicPeerOptions.value = data.data
      toast.success('检测节点可用状态成功')
      publicPeerOptions.value.sort((a, b) => {
        const aIn = config.value.peer.includes(a.uri);
        const bIn = config.value.peer.includes(b.uri);
        return bIn - aIn;
      });
    }).catch(() => {
      toast.error('检测节点可用状态失败')
    }).finally(() => {
      isPeerChecking.value = false
      checkToast.clear()
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
    flagsOpen.value = ['']
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

const onConfigSwitch = async (profile) => {
  const cfg = configList.value.find(c => c.profile === profile)
  if (cfg) {
    try {
      await loadConfig(cfg.profile)
    } catch (error) {
      toast.error('加载配置失败: ' + (error.message || '未知错误'))
    }
  }
}

const deleteCurrentConfig = async () => {
  const cfg = currentConfigData.value
  if (!cfg || !cfg.profile) return
  isDeletingConfig.value = true
  return new Promise(async(resolve, reject) => {
    try {
      const isRunning = await api.services.status(selectedConfig.value).then(resp => resp.data)
      if (isRunning) {
        const stoping = toast.loading('停止服务中...')
        await api.services.stop(selectedConfig.value).then(() => toast.success('服务已停止')).finally(() => {
          stoping.clear()
        })
        // 停止et服务可能本地网络会有波动，导致下一次请求被被阻断
        await new Promise(r => setTimeout(r, 2000));
      }
      await api.configs.delete(cfg.profile)
      toast.success('配置已删除')
      await loadConfigs()
      if (configList.value.length > 0) {
        selectedConfig.value = configList.value[0].profile
        await loadConfig(configList.value[0].profile)
      } else {
        selectedConfig.value = ''
      }
      resolve()
    } catch (error) {
      toast.error('删除配置失败: ' + error.message)
      reject(error)
    } finally {
      isDeletingConfig.value = false
    }
  })
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
  config.value.flags = { ...config.value.flags, bind_device: true, multi_thread: true, enable_ipv6: true }
  config.value.proxy_network = []
  configList.value.push({ 'profile': profile, 'name': name, 'autostart': false })
  selectedConfig.value = profile
  newConfigName.value = ''
}

const startEditName = () => {
  const cfg = currentConfigData.value
  editNameValue.value = cfg.name || ''
  showRenameDialog.value = true
}

const confirmEditName = async (action, done) => {
  if (action !== 'confirm') {
    return done()
  }
  const newName = editNameValue.value.trim()
  if (!newName) {
    toast.warning('请输入新名称')
    return done()
  }
  if (newName === currentConfigData.value.name) {
    showRenameDialog.value = false
    return done()
  }
  isRenaming.value = true
  const loadingToast = toast.loading('重命名中...')
  try {
    const isRunning = await api.services.status(selectedConfig.value).then(resp => resp.data)
    if (isRunning) {
      const stoping = toast.loading('停止服务中...')
      await api.services.stop(selectedConfig.value).then(() => toast.success('服务已停止')).finally(() => {
        stoping.clear()
      })
      // 停止et服务可能本地网络会有波动，导致下一次请求被被阻断
      await new Promise(r => setTimeout(r, 2000));
    }
    const res = await api.configs.rename(selectedConfig.value, newName+'.toml').catch(error => {
      toast.error('重命名失败: ' + error.message)
      throw error
    })
    toast.success('重命名成功')
    await loadConfigs()
    selectedConfig.value = res.data.profile
    currentConfigData.value.name = res.data.name
    showRenameDialog.value = false
    if (isRunning) {
      const starting = toast.loading('启动服务中...')
      await api.services.start(selectedConfig.value).then(() => toast.success('服务已启动'))
      .finally(() => {
        starting.clear()
      })
    }
  } finally {
    isRenaming.value = false
    loadingToast.clear()
    return done()
  }
}

const handleSwitchChange = async (cfg, field, val) => {
  cfg[field] = val
  if (field === 'autostart') {
    try {
      changingAutostart.value = true
      await api.services.autoStart(cfg.profile, val)
      toast.success(val ? '已开机自启' : '已关闭开机自启')
    } catch (error) {
      cfg[field] = !val
    } finally {
      changingAutostart.value = false
    }
  }
}

const setupShowMode = async (mode) => {
  return new Promise(async(resolve, reject) => {
    showMode.value = mode
    if (mode === 1) {
      config.value.network_identity.network_name = ''
      config.value.network_identity.network_secret = ''
      fastSettingMode.value = true
      if (publicPeerOptions.value.length == 0 || publicPeerOptions.value[0].status != 1) {
        isLoadingConfig.value = true
        await refreshPublicPeerOptions(true, true)
        isLoadingConfig.value = false
      }
      const peers = publicPeerOptions.value.slice(0, 3).map(e => e.uri)
      config.value.peer.unshift(...peers)
    } else if (mode === 2) {
      refreshPublicPeerOptions(false, false)
      showCreateDialog.value = true
    }
  }).finally(() => {
    resolve()
  })
}

const exitAddMode = async () => {
  showMode.value = 0
  showCreateDialog.value = false
  newConfigName.value = ''
  await loadConfigs()
  selectedConfig.value = configList.value?.[0]?.profile || ''
}

const getLanIps = () => {
  api.configs.getLanIps().then(data => {
    lanIps.value = data.data
  })
}

onMounted(async () => {
  // 如果是用户版（非管理员权限），则开启no_tun
  if (window.location.href.includes('/cgi/ThirdParty/EasyTier-EUI.User/index.cgi')) {
    config.value.flags.no_tun = true
  }
  getLanIps()
  await loadConfigs()
  if (configList.value.length == 0) {
    return
  }
  selectedConfig.value = configList.value[0].profile
  await loadConfig(configList.value[0].profile)
  api.peers.publicPeers({'profile': selectedConfig.value}).then(async data => {
    publicPeerOptions.value = data.data
  })
})
</script>

<style scoped>
.config-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
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
  margin: 24px 16px 8px;
  padding: 16px 20px;
  border-radius: 12px;
  background: var(--color-surface-container) !important;
}

.toolbar-divider {
  display: none;
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
  gap: 1px;
  margin-left: 4px;
}

.config-actions-group .var-button {
  margin-left: 3px;
  margin-right: 3px;
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
  padding: 0 16px 10px;
  margin-top: 4px;
  position: relative;
}

.config-section {
  margin: 0 0 16px;
  padding: 20px;
  border-radius: 16px;
  /* background: var(--color-surface-container) !important; */
  background: var(--color-surface) !important;
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

/* ===== 节点下拉框优化样式 ===== */
.peer-cell {
  padding: 8px 0;
}

.peer-cell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.peer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}


/* ===== 已选中 chip 区域限制高度：最多显示 2.5 个，超出滚动 ===== */
.peer-select {
  max-width: 100%;
}

/* 限制 chip 容器高度 */
.peer-select :deep(.var-select__chips) {
  max-height: 72px;
  overflow-y: auto;
}

/* chip 容器滚动条美化 */
.peer-select :deep(.var-select__chips)::-webkit-scrollbar {
  width: 4px;
}

.peer-select :deep(.var-select__chips)::-webkit-scrollbar-track {
  background: transparent;
}

.peer-select :deep(.var-select__chips)::-webkit-scrollbar-thumb {
  background: var(--color-text-disabled);
  border-radius: 2px;
}

/* 调整 chip 间距，让 2.5 个刚好能被截断 */
.peer-select :deep(.var-chip) {
  margin: 2px 4px 2px 0;
}
/* .var-option .var-checkbox--unchecked {
  background: var(--color-text) !important;
  color: var(--color-text) !important;
} */

/* 自定义输入区域 */
.peer-custom-input {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  /* background: var(--color-surface-container-high); */
}

.peer-custom-field {
  flex: 1;
}

/* 选项列表容器 */
.peer-options-list {
  max-height: 320px;
  /* overflow-y: auto; */
}

/* 单个选项卡片 */
.peer-option-wrapper {
  padding: 4 !important;
  margin: 0 !important;
  height: auto !important;
  min-height: auto !important;

}

.peer-option-wrapper :deep(.var-option__cover) {
  padding: 0 !important;
}

.peer-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  margin: 4px 8px;
  border-radius: 10px;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 1px solid transparent;
}

.peer-card:hover {
  background: var(--color-surface-container-high);
  border-color: var(--color-outline-variant);
}

/* 左侧信息区 */
.peer-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.peer-primary-uri {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.peer-secondary-uri {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 标签样式 */
.peer-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  margin-right: 4px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.5;
  white-space: nowrap;
}

.relay-tag {
  background: var(--color-info-container);
  color: var(--color-on-info-container);
}

.latency-good {
  background: var(--snackbar-success-background);
  color: var(--color-on-success-container);
}

.latency-normal {
  background: var(--color-info-container);
  color: var(--color-on-info-container);
}

.latency-bad {
  background: var(--color-danger-container);
  color: var(--color-on-danger-container);
}

.dynamic-tag {
  background: var(--color-success-container);
  color: var(--color-on-success-container);
}

/* 右侧状态区 */
.peer-status-area {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-top: 2px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-online {
  background: var(--color-success);
  box-shadow: 0 0 0 2px rgba(var(--color-success-rgb, 76, 175, 80), 0.2);
}

.status-offline {
  background: var(--color-danger);
  opacity: 0.8;
}

/* 下拉面板滚动条优化 */
.peer-options-list::-webkit-scrollbar {
  width: 6px;
}

.peer-options-list::-webkit-scrollbar-track {
  background: transparent;
}

.peer-options-list::-webkit-scrollbar-thumb {
  background: var(--color-text-disabled);
  border-radius: 3px;
}

/* 选中态优化 */
.peer-option-wrapper :deep(.var-option--selected) .peer-card {
  background: var(--color-primary-container);
  border-color: var(--color-primary);
}

/* ===== 高级设置样式 ===== */
.flags-section-paper {
  /* margin-top: 8px; */
  border-radius: 16px;
  overflow: hidden;
  /* background: var(--color-surface-container) !important; */
  background: var(--color-surface) !important;
}

:deep(.flags-section .var-collapse-item) {
  border-radius: 16px;
  overflow: hidden;
  background: var(--color-surface-container) !important;
}

:deep(.flags-section-inner .var-collapse-item) {
  border-radius: 12px;
  overflow: hidden;
  background: transparent !important;
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

.tooltip-multiline {
  white-space: pre-line;   /* 识别 \n 换行 */
  line-height: 1.6;        /* 行间距 */
  max-width: 300px;
}

/* ===== 代码编辑器 ===== */
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

/* ===== 内联样式迁移 ===== */
.fast-setting-hint {
  font-size: 13px;
  color: var(--color-warning);
  margin-top: 8px;
}

.fast-setting-mode-hint {
  font-size: 12px;
  color: var(--color-warning);
  margin-top: 8px;
}

.eye-icon {
  cursor: pointer;
  opacity: 0.54;
}

.code-editor-popup-container {
  width: 100vw;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: 0;
  padding: 0;
  max-width: none;
  max-height: none;
}

.code-editor-wrapper {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
}

.code-editor-content-area {
  flex: 1;
  overflow: auto;
  margin: 0;
  padding: 0;
}

.code-editor-inner {
  height: 100%;
  width: 100%;
}

.help-content {
  padding: 24px;
  max-width: 100%;
  font-size: 14px;
  margin-top: 10px;
}

.help-paragraph {
  margin: 10px 0;
}

.help-bold {
  font-weight: bold;
}

.help-content :deep(.var-table__main),
.help-content :deep(.var-table) {
  border-radius: 16px 16px 16px 16px !important;
}

.help-content th {
  position: sticky;
  top: 0;
  z-index: 10;
  color: var(--color-text) !important;
  background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 1) !important;
}

.help-content tr {
  --table-tbody-td-text-color: var(--color-text) !important;
  background: rgba(var(--color-surface-container-rgb, 224, 242, 254), 0.1) !important;
}

/* ===== Deep 覆盖 ===== */
:deep(.var-form) {
  display: flex;
  flex-direction: column;
  /* gap: 16px; */
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

:deep(.var-menu.var--box.var-select__menu) {
  background: var(--color-surface) !important;
}

:deep(.config-switcher .var-menu.var--box.var-select__menu) {
  background: var(--color-surface-container) !important;
}

/* ===== 响应式 ===== */
@media (max-width: 767px) {
  .config-page {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 64px);
    overflow: hidden;
  }

  .toolbar {
    flex-shrink: 0;
    margin: 16px 12px 4px;
    padding: 12px;
    border-radius: 10px;
  }

  .toolbar-divider {
    display: flex;
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
    padding: 8px 12px;
    margin-top: 0;
  }

  .config-section {
    margin: 0 0 12px;
    padding: 16px;
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

  .peer-card {
    padding: 8px 10px;
    margin: 2px 4px;
  }

  .peer-primary-uri {
    font-size: 15px;
  }

  .peer-secondary-uri {
    font-size: 11px;
  }

  .peer-tag {
    font-size: 10px;
    padding: 1px 4px;
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
  
  :global(.var-tooltip__content-container.var-tooltip--default) {
    margin-left: 20px !important;
    --tooltip-border-radius: 10px
  }
}

@media (max-width: 480px) {
  .feature-grid {
    grid-template-columns: 1fr;
  }
  
  .peer-status-area {
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }
}
</style>

<!-- 全局样式 - 解决 Varlet 下拉菜单样式穿透问题 -->
<style>
/* 节点选择下拉菜单样式 */
.var-select-dropdown .peer-option-wrapper {
  padding: 0;
  margin: 0;
}

.var-select-dropdown .var-cell {
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border);
}

.var-select-dropdown .var-cell__title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.var-select-dropdown .var-cell__description {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.var-select-dropdown .peer-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.var-select-dropdown .peer-primary-uri {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.var-select-dropdown .peer-secondary-uri {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.var-select-dropdown .peer-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.var-select-dropdown .latency-tag {
  background-color: var(--color-primary-container);
  color: var(--color-on-primary-container);
}

.var-select-dropdown .latency-good {
  background-color: var(--color-success);
  color: #fff;
}

.var-select-dropdown .latency-normal {
  background-color: var(--color-warning);
  color: #fff;
}

.var-select-dropdown .latency-bad {
  background-color: var(--color-danger);
  color: #fff;
}

.var-select-dropdown .relay-tag {
  background-color: var(--color-info);
  color: #fff;
}

.var-select-dropdown .dynamic-tag {
  background-color: var(--color-primary);
  color: #fff;
}

.var-select-dropdown .var-cell__extra {
  display: flex;
  align-items: center;
  gap: 6px;
}

.var-select-dropdown .status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.var-select-dropdown .status-online {
  background-color: var(--color-success);
}

.var-select-dropdown .status-offline {
  background-color: var(--color-danger);
}

.var-select-dropdown .peer-status-area {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 移动端适配 */
@media (max-width: 767px) {
  .var-select-dropdown .var-cell {
    padding: 6px 10px;
  }
  
  .var-select-dropdown .var-cell__title {
    font-size: 13px;
  }
  
  .var-select-dropdown .peer-primary-uri {
    font-size: 13px;
  }
  
  .var-select-dropdown .peer-secondary-uri {
    font-size: 11px;
    gap: 4px;
  }
  
  .var-select-dropdown .peer-tag {
    font-size: 10px;
    padding: 1px 4px;
  }
  
  .var-select-dropdown .var-cell__extra {
    gap: 4px;
  }
  
  .var-select-dropdown .peer-status-area {
    gap: 4px;
  }
}
</style>