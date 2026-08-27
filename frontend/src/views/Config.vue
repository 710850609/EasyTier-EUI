<template>
  <div class="config-page">
    <div v-if="isLoadingConfigList" class="config-skeleton">
      <div class="sk-toolbar">
        <div class="sk-pill sk-pill-select"><div class="sk-breathe"></div></div>
        <div class="sk-pill sk-pill-btn"><div class="sk-breathe"></div></div>
        <div class="sk-pill sk-pill-btn"><div class="sk-breathe"></div></div>
        <div class="sk-pill sk-pill-btn"><div class="sk-breathe"></div></div>
        <div class="sk-pill sk-pill-btn sk-pill-btn-sm"><div class="sk-breathe"></div></div>
      </div>
      <div class="sk-content">
        <div class="sk-section" v-for="section in 5" :key="section" :style="{ animationDelay: `${section * 0.08}s` }">
          <div class="sk-section-title" :class="{ 'sk-section-title--only': section > 1 }">
            <div class="sk-pill sk-pill-title"><div class="sk-breathe"></div></div>
          </div>
          <div class="sk-fields" v-if="section === 1">
            <div class="sk-field" v-for="field in 5" :key="field">
              <div class="sk-pill sk-pill-label"><div class="sk-breathe"></div></div>
              <div class="sk-pill sk-pill-input"><div class="sk-breathe"></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!fastSettingMode && configList.length === 0" class="empty-state-full">
      <var-icon name="file-document-outline" size="56" color="var(--color-text-disabled)" />
      <p class="empty-title">{{ $t('config.noConfig') }}</p>
      <p class="empty-hint">{{ $t('config.noConfigHint') }}</p>
      <var-button type="primary" size="large" @click="setupShowMode(1);" auto-loading>
        <var-icon name="plus" size="18" />
        {{ $t('config.quickAdd') }}
      </var-button>
      <var-button type="primary" size="large" @click="setupShowMode(2);" auto-loading>
        <var-icon name="plus" size="18" />
        {{ $t('config.normalAdd') }}
      </var-button>
    </div>

    <div v-else class="config-else-wrapper">
      <var-paper class="toolbar" :elevation="1" v-if="!fastSettingMode">
        <div class="toolbar-row">
          <div class="toolbar-left">
            <var-select
              class="config-switcher"
              v-model="selectedConfig"
              :placeholder="$t('config.selectConfig')"
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
              <label class="toggle-item" v-if="showMode === 0 && platform !== 'android'">
                <var-switch variant size="18" :loading="changingAutostart" v-model="currentConfigAutostart" @change="(val) => handleSwitchChange(currentConfigData, 'autostart', val)" />
              </label>
              <span class="toggle-label" v-if="showMode === 0 && platform !== 'android'">{{ $t('config.autostart') }}</span>
            </div>
          </div>
          <div class="toolbar-right" v-if="selectedConfig">
            <var-button size="small" type="danger" @click="exitAddMode()" :loading="isDeletingConfig" v-if="showMode !== 0">{{ $t('config.exitAdd') }}</var-button>
            <var-button type="primary" size="small" @click="saveConfig" auto-loading>{{ $t('config.save') }}</var-button>
            <var-menu v-model:show="showMoreMenu" trigger="manual" placement="bottom-end" :offset-y="10" :offset-x="12" v-if="showMode === 0" popover-class="more-menu-popover">
              <var-button text round class="column-btn" @click="showMoreMenu = !showMoreMenu">
                <var-icon name="menu" size="20" color="var(--color-on-surface)" />
              </var-button>
              <template #menu>
                <div class="more-menu">
                  <var-button text block @click="showCreateDialog = true; showMode = 1; showMoreMenu = false">
                    <svg-icon type="mdi" :path="mdiPlus" class="menu-icon"></svg-icon>
                    <span>{{ $t('config.add') }}</span>
                  </var-button>
                  <var-button text block @click="startEditName(); showMoreMenu = false" :loading="isRenaming">
                    <svg-icon type="mdi" :path="mdiSquareEditOutline" class="menu-icon"></svg-icon>
                    <span>{{ $t('config.rename') }}</span>
                  </var-button>
                  <var-button text block @click="showShareConfigType = true; showMoreMenu = false">
                    <svg-icon type="mdi" :path="mdiShareOutline" class="menu-icon"></svg-icon>
                    <span>{{ $t('config.shareNetwork') }}</span>
                  </var-button>
                  <var-button text block @click="openCodePage(); showMoreMenu = false" auto-loading>
                    <svg-icon type="mdi" :path="mdiDrawPen" class="menu-icon"></svg-icon>
                    <span>{{ $t('config.editFile') }}</span>
                  </var-button>
                  <var-divider class="menu-divider" />
                  <var-button text block @click="showDeleteDialog = true; showMoreMenu = false" :loading="isDeletingConfig" class="delete-btn">
                    <svg-icon type="mdi" :path="mdiTrashCanOutline" class="menu-icon"></svg-icon>
                    <span>{{ $t('config.delete') }}</span>
                  </var-button>
                </div>
              </template>
            </var-menu>
          </div>
        </div>
      </var-paper>

      <div class="content-area" v-if="selectedConfig || fastSettingMode">
        <var-form ref="form">
          <!-- 骨架屏遮罩层：覆盖在内容上方 -->
          <div v-if="isLoadingConfig" class="sk-overlay"></div>
          <var-paper class="config-section merged-section" :elevation="0">
            <!-- 基础设置 -->
            <div class="section-header">
              <div class="section-header-left">
                <svg-icon type="mdi" :path="mdiHomeEdit" width="24" height="24" color="var(--color-primary)" />
                <span class="section-title">{{ fastSettingMode ? $t('config.fastSetup') : $t('config.basicSettings') }}</span>
              </div>
              <div v-if="fastSettingMode && !isLoadingConfig && publicPeerOptions.length > 0">
                <span class="fast-setting-hint">{{ $t('config.fastSetupHint') }} -&gt; </span>
                <var-button type="primary" size="small" @click="saveConfig" auto-loading>{{ $t('config.saveAndStart') }}</var-button>
              </div>
            </div>

              <div class="input-row">
                <var-cell>
                  <var-input
                    v-model="config.network_identity.network_name"
                    :placeholder="$t('config.networkName')"
                    size="small"
                    :rules="[(v) => !!v || $t('config.networkNameRequired')]"
                    variant="outlined"
                  >
                    <template #prepend-icon>
                      <svg-icon type="mdi" :path="mdilAccount"></svg-icon>
                    </template>
                    <template #label>{{ $t('config.networkName') }}</template>
                  </var-input>
                </var-cell>
                <var-cell>
                  <var-input
                    v-model="config.network_identity.network_secret"
                    :placeholder="$t('config.networkSecret')"
                    :type="showPassword ? 'text' : 'password'"
                    :rules="[(v) => !!v || $t('config.networkSecretRequired')]"
                    size="small"
                    variant="outlined"
                  >
                    <template #prepend-icon>
                      <svg-icon type="mdi" :path="mdilLock" />
                    </template>
                    <template #label>{{ $t('config.networkSecret') }}</template>
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
                    {{ $t('config.initialPeers') }}
                    <var-icon name="information-outline" size="12pt" @click="showPublicPeerTip = true" color="var(--color-primary)" />
                  </div>
                </div>
                
                <var-select
                  variant="outlined"
                  size="small"
                  v-model="config.peer"
                  multiple
                  :placeholder="$t('config.nodeCountHint', { count: config.peer.length })"
                  :chip="true"
                  class="peer-select"
                  @focus="onSelectFocus('peer')"
                >
                  <template #default>
                    <div class="peer-custom-input" :key="selectInputRenderKey.peer">
                      <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" size="20" />
                      <var-input 
                        :placeholder="$t('config.customNodePlaceholder')" 
                        size="small" 
                        v-model="customPeer" 
                        class="peer-custom-field"
                      />
                      <var-button type="primary" size="small" @click="addPeer">{{ $t('config.add') }}</var-button>
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
                        <template #title>
                          {{ peer.hostname || peer.uri }}
                        </template>
                        <template #description>
                          <div class="peer-info">
                            <div class="peer-sub-uri">
                              <!-- <span class="status-dot" v-if="peer.status in [1]" :class="peer.status == 1 ? 'status-online' : 'status-offline'"></span> -->
                              {{ peer.uri }}
                            </div>
                            <div class="peer-tags">
                              <span class="peer-tag latency-tag" :class="peer.latency < 500 ? (peer.latency < 100 ? 'latency-good' : 'latency-normal') : 'latency-bad'"  
                                v-if="peer.latency > 0">
                                {{ peer.latency }}ms
                              </span>
                              <span class="peer-tag unavailable-tag" v-if="peer.status === 0">✕</span>
                              <span class="peer-tag relay-tag" v-if="peer.relay == 1">{{ $t('config.relay') }}</span>
                              <span class="peer-tag dynamic-tag" v-if="peer.dynamic">{{ $t('config.dynamic') }}</span>
                              <span style="font-size: 12px; color: var(--color-primary);">{{ peer.hostname || '' }}</span>
                            </div>
                          </div>
                        </template>
                        <!-- <template #extra>
                          <div class="status-dot" v-if="peer.status in [0, 1]" :class="peer.status == 1 ? 'status-online' : 'status-offline'"></div>
                        </template> -->
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
                    <span>{{ $t('config.fastSetupHintFooter') }}</span>
                    <var-icon name="help-circle-outline" size="12pt" @click="showPublicPeerTip = true" class="help-icon" />
                  </p>
                  <p>
                    <span>{{ $t('config.fastSetupReconfigHint') }}</span>
                    <var-button type="primary" size="mini" @click="fastSettingMode = false">{{ $t('config.normalAdd') }}</var-button>
                  </p>
                </div>
              </var-cell>
          </var-paper>

          <!-- 本机信息 -->
          <var-paper v-if="!fastSettingMode" :elevation="0" class="config-section-panel">
            <var-collapse v-model="advancedOpen" class="panel-section-inner">
              <var-collapse-item name="hostInfo">
              <template #title>
                <div class="collapse-title">
                  <svg-icon type="mdi" :path="mdiMonitor" width="24" height="24" color="var(--color-primary)" />
                  <span class="section-title">{{ $t('config.hostInfo') }}</span>
                </div>
              </template>
                <div class="flags-content" :key="'hostInfo-' + selectedConfig + '-' + advancedRenderKeys.hostInfo">
                  <div class="feature-section">
                    <div class="feature-grid">
                      <div
                        v-for="feature in hostInfoSwitches"
                        :key="feature.key"
                        class="feature-item"
                      >
                        <var-checkbox v-model="config.flags[feature.key]">
                          {{ $t(feature.label) }}
                        </var-checkbox>
                        <var-tooltip v-if="feature.tooltip" teleport="body">
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          <template #content>
                            <div class="tooltip-multiline">
                              {{ $t(feature.tooltip) }}
                            </div>
                          </template>
                        </var-tooltip>
                      </div>
                    </div>
                  </div>
                  <var-divider />

                  <div class="input-row">
                    <div class="input-section">
                      <div class="section-subtitle">{{ $t('config.hostname') }}</div>
                      <var-input v-model="config.hostname" :placeholder="$t('config.hostnamePlaceholder')" variant="outlined" size="small" />
                    </div>
                    <div class="input-section">
                      <div class="section-subtitle">{{ $t('config.virtualIpv4') }}</div>
                      <var-input v-model="config.ipv4" :placeholder="$t('config.virtualIpv4Placeholder')" variant="outlined" size="small" />
                    </div>
                  </div>

                  <div class="input-row">
                    <div class="input-section">
                      <var-tooltip trigger="click">
                        <div class="section-subtitle">{{ $t('config.tunName') }}
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                        <template #content>
                          <div class="tooltip-multiline">
                            {{ $t('config.tunNameHint') }}
                          </div>
                        </template>
                      </var-tooltip>
                      <var-input v-model="config.flags.dev_name" :placeholder="$t('config.tunNamePlaceholder')" variant="outlined" size="small" />
                    </div>
                    <div class="input-section">
                      <var-tooltip trigger="click">
                        <div class="section-subtitle">{{ $t('config.tunMtu') }}
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                        <template #content>
                          <div class="tooltip-multiline">{{ $t('config.tunMtuHint') }}</div>
                        </template>
                      </var-tooltip>
                      <var-input
                        v-model="mtuStr"
                        type="number"
                        :rules="(v) => (v === '' || v >= 400 && v <= 1380) || $t('config.mtuRangeError')"
                        :placeholder="$t('config.tunMtuPlaceholder')"
                        variant="outlined"
                        size="small"
                      />
                    </div>
                  </div>
              </div>
            </var-collapse-item>
          </var-collapse>
          </var-paper>

          <!-- 连接方式 -->
          <var-paper v-if="!fastSettingMode" :elevation="0" class="config-section-panel">
            <var-collapse v-model="advancedOpen" class="panel-section-inner">
              <var-collapse-item name="connection">
              <template #title>
                <div class="collapse-title">
                  <svg-icon type="mdi" :path="mdiLanConnect" width="24" height="24" color="var(--color-primary)" />
                  <span class="section-title">{{ $t('config.connectionMethod') }}</span>
                </div>
              </template>
                <div class="flags-content" :key="'connection-' + selectedConfig + '-' + advancedRenderKeys.connection">
                  <div class="feature-section">
                    <div class="feature-grid">
                      <div
                        v-for="feature in connectionSwitches"
                        :key="feature.key"
                        class="feature-item"
                      >
                        <var-checkbox v-model="config.flags[feature.key]">
                          {{ $t(feature.label) }}
                        </var-checkbox>
                        <var-tooltip v-if="feature.tooltip" teleport="body">
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          <template #content>
                            <div class="tooltip-multiline">
                              {{ $t(feature.tooltip) }}
                            </div>
                          </template>
                        </var-tooltip>
                      </div>
                    </div>
                  </div>
                  <var-divider />

                  <div class="input-row">
                    <div class="input-section">
                      <div class="section-subtitle">{{ $t('config.defaultProtocol') }}</div>
                      <var-select
                        v-model="config.flags.default_protocol"
                        :placeholder="$t('config.defaultProtocol')"
                        variant="outlined"
                        :chip="true"
                        size="small"
                      >
                        <var-option v-for="(e, index) in defaultProtocolList" :key="index" :label="e.label" :value="e.value" />
                      </var-select>
                    </div>
                    <div class="input-section">
                    </div>
                  </div>

                  <div class="input-section">
                    <div class="section-subtitle">{{ $t('config.listeners') }}
                      <var-tooltip :content="$t('config.listenersHint')" trigger="click">
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                      </var-tooltip>
                    </div>
                    <var-select
                      v-model="config.listeners"
                      multiple
                      :placeholder="$t('config.listenersCount', { n: config.listeners.length })"
                      variant="outlined"
                      :chip="true"
                      size="small"
                      @focus="onSelectFocus('listener')"
                    >
                      <var-cell :key="selectInputRenderKey.listener">
                        <template #icon>
                          <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                        </template>
                        <template #description>
                          <var-input :placeholder="$t('config.customListenerPlaceholder')" size="small" v-model="customListener" blur-color="var(--color-primary)" />
                        </template>
                        <template #extra>
                          <var-button type="primary" size="small" @click="addListener">{{ $t('config.addListener') }}</var-button>
                        </template>
                      </var-cell>
                      <var-option v-for="(e, index) in listenerOptions" :key="index" :label="e" :value="e" />
                    </var-select>
                  </div>
              </div>
            </var-collapse-item>
          </var-collapse>
          </var-paper>

          <!-- 性能安全 -->
          <var-paper v-if="!fastSettingMode" :elevation="0" class="config-section-panel">
            <var-collapse v-model="advancedOpen" class="panel-section-inner">
              <var-collapse-item name="performance">
              <template #title>
                <div class="collapse-title">
                  <svg-icon type="mdi" :path="mdiTuneVariant" width="24" height="24" color="var(--color-primary)" />
                  <span class="section-title">{{ $t('config.performanceSecurity') }}</span>
                </div>
              </template>
                <div class="flags-content" :key="'performance-' + selectedConfig + '-' + advancedRenderKeys.performance">
                  <div class="feature-section">
                    <div class="feature-grid">
                      <div
                        v-for="feature in performanceSwitches"
                        :key="feature.key"
                        class="feature-item"
                      >
                        <var-checkbox v-model="config.flags[feature.key]">
                          {{ $t(feature.label) }}
                        </var-checkbox>
                        <var-tooltip v-if="feature.tooltip" teleport="body">
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          <template #content>
                            <div class="tooltip-multiline">
                              {{ $t(feature.tooltip) }}
                            </div>
                          </template>
                        </var-tooltip>
                      </div>
                    </div>
                  </div>
                  <var-divider />

                  <div class="input-row">
                    <div class="input-section">
                      <var-tooltip :content="$t('config.workerCountHint')" trigger="click">
                        <div class="section-subtitle">{{ $t('config.workerCount') }}
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                      </var-tooltip>
                      <var-input
                        v-model="multiThreadCountStr"
                        :placeholder="$t('config.workerCountPlaceholder')"
                        variant="outlined"
                        type="number"
                        :rules="(v) => (v === '' || v >= 2) || $t('config.workerCountError')"
                        size="small"
                      />
                    </div>
                    <div class="input-section">
                      <div class="section-subtitle">{{ $t('config.cipher') }}</div>
                      <var-select
                        v-model="config.flags.encryption_algorithm"
                        :placeholder="$t('config.cipherPlaceholder')"
                        variant="outlined"
                        :chip="true"
                        size="small"
                        :line="true"
                      >
                        <var-option v-for="(e, index) in encryptionAlgorithmList" :key="index" :label="e" :value="e" />
                      </var-select>
                    </div>
                  </div>

                  <div class="input-row">
                    <div class="input-section">
                      <div class="section-subtitle">{{ $t('config.compression') }}</div>
                      <var-select
                        v-model="config.flags.compression"
                        :placeholder="$t('config.compressionPlaceholder')"
                        variant="outlined"
                        :chip="true"
                        size="small"
                      >
                        <var-option v-for="(e, index) in compressionOptions" :key="index" :label="e.label" :value="e.value" />
                      </var-select>
                    </div>
                    <div class="input-section">
                      <var-tooltip :content="$t('config.rateLimitRxHint')" trigger="click">
                        <div class="section-subtitle">{{ $t('config.rateLimitRx') }}
                          <var-icon name="help-circle-outline" size="16" class="help-icon" />
                        </div>
                      </var-tooltip>
                      <var-input
                        v-model="config.flags.instance_recv_bps_limit"
                        :placeholder="$t('config.rateLimitRxPlaceholder')"
                        variant="outlined"
                        type="number"
                        size="small"
                      />
                    </div>
                  </div>
              </div>
            </var-collapse-item>
          </var-collapse>
          </var-paper>

          <!-- 代理与转发 -->
          <var-paper v-if="!fastSettingMode" :elevation="0" class="config-section-panel">
            <var-collapse v-model="forwardOpen" class="panel-section-inner">
              <var-collapse-item name="forward">
                <template #title>
                  <div class="collapse-title">
                    <svg-icon type="mdi" :path="mdiRouterNetwork" width="24" height="24" color="var(--color-primary)" />
                    <span class="section-title">{{ $t('config.proxyForward') }}</span>
                  </div>
                </template>
                  <div class="forward-content" :key="'forward-' + selectedConfig + '-' + forwardRenderKey">
                    <div class="feature-section">
                      <div class="feature-grid">
                        <div class="feature-item">
                          <var-checkbox v-model="config.flags.enable_exit_node">
                            {{ $t('config.flags.enable_exit_node.label') }}
                          </var-checkbox>
                          <var-tooltip teleport="body">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                            <template #content>
                              <div class="tooltip-multiline">
                                {{ $t('config.flags.enable_exit_node.tooltip') }}
                              </div>
                            </template>
                          </var-tooltip>
                        </div>
                        <div class="feature-item">
                          <var-checkbox v-model="config.flags.relay_all_peer_rpc">
                            {{ $t('config.flags.relay_all_peer_rpc.label') }}
                          </var-checkbox>
                          <var-tooltip teleport="body">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                            <template #content>
                              <div class="tooltip-multiline">
                                {{ $t('config.flags.relay_all_peer_rpc.tooltip') }}
                              </div>
                            </template>
                          </var-tooltip>
                        </div>
                        <div class="feature-item">
                          <var-checkbox v-model="config.flags.proxy_forward_by_system">
                            {{ $t('config.flags.proxy_forward_by_system.label') }}
                          </var-checkbox>
                          <var-tooltip teleport="body">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                            <template #content>
                              <div class="tooltip-multiline">
                                {{ $t('config.flags.proxy_forward_by_system.tooltip') }}
                              </div>
                            </template>
                          </var-tooltip>
                        </div>
                      </div>
                    </div>
                    <var-divider />
                    <div class="input-row">
                      <div class="input-section">
                        <div class="section-subtitle">{{ $t('config.socks5Port') }}
                          <var-tooltip :content="$t('config.socks5PortHint')" trigger="click">
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </var-tooltip>
                        </div>
                        <var-input
                          v-model="config.socks5_proxy"
                          :placeholder="$t('config.socks5Placeholder')"
                          variant="outlined"
                          type="number"
                          size="small"
                          :rules="(v) => (!v || (v >= 2 && v <= 65535)) || $t('config.portRangeError')"
                        />
                      </div>
                      <div class="input-section">
                        <var-tooltip :content="$t('config.forwardWhitelistHint')" trigger="click">
                          <div class="section-subtitle">{{ $t('config.forwardWhitelist') }}
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </div>
                        </var-tooltip>
                        <var-input
                          v-model="config.flags.relay_network_whitelist"
                          multiple
                          :placeholder="$t('config.forwardWhitelistPlaceholder')"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        />
                      </div>
                      </div>
                    <div class="input-row">
                      <div class="input-section">
                        <var-tooltip :content="$t('config.exitNodesHint')" trigger="click">
                          <div class="section-subtitle">{{ $t('config.exitNodes') }}
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </div>
                        </var-tooltip>
                        <var-select
                          v-model="config.exit_nodes"
                          :placeholder="$t('config.exitNodesPlaceholder')"
                          :multiple="true"
                          variant="outlined"
                          :chip="true"
                          size="small"
                          @focus="onSelectFocus('exitNode')"
                        >
                          <var-cell :key="selectInputRenderKey.exitNode">
                            <template #icon>
                              <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                            </template>
                            <template #description>
                              <var-input :placeholder="$t('config.customExitNodePlaceholder')" size="small" v-model="customExitNode" blur-color="var(--color-primary)" />
                            </template>
                            <template #extra>
                              <var-button type="primary" size="small" @click="addExitNode">{{ $t('config.addExitNode') }}</var-button>
                            </template>
                          </var-cell>
                          <var-option v-for="(e, index) in config.exit_nodes" :key="index" :label="e" :value="e" />
                        </var-select>
                      </div>
                      <div class="input-section">
                        <var-tooltip :content="$t('config.customRoutesHint')" trigger="click">
                          <div class="section-subtitle">{{ $t('config.customRoutes') }}
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </div>
                        </var-tooltip>
                        <var-select
                          v-model="config.routes"
                          :placeholder="$t('config.customRoutesPlaceholder')"
                          :multiple="true"
                          variant="outlined"
                          :chip="true"
                          size="small"
                          @focus="onSelectFocus('route')"
                        >
                          <var-cell :key="selectInputRenderKey.route">
                            <template #icon>
                              <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                            </template>
                            <template #description>
                              <var-input :placeholder="$t('config.customRoutePlaceholder')" size="small" v-model="customRoute" blur-color="var(--color-primary)" />
                            </template>
                            <template #extra>
                              <var-button type="primary" size="small" @click="addRoute">{{ $t('config.addCustomRoute') }}</var-button>
                            </template>
                          </var-cell>
                          <var-option v-for="(r, index) in config.routes" :key="index" :label="r" :value="r" />
                        </var-select>
                      </div>
                    </div>
                    <var-divider />
                    <div class="forward-section">
                      <var-tooltip teleport="body" trigger="click" :offset-x="80">
                        <template #default>
                          <div class="section-subtitle">{{ $t('config.subnetProxy') }}
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </div>
                        </template>
                        <template #content>
                          <div class="tooltip-multiline">{{ $t('config.subnetProxyHint') }}</div>
                        </template>
                      </var-tooltip>
                      <div class="port-forward-table">
                        <div class="port-forward-row port-forward-header subnet-proxy-row">
                          <div class="port-forward-cell">{{ $t('config.subnetCidr') }}</div>
                          <div class="port-forward-cell">{{ $t('config.mappedCidr') }}</div>
                          <div class="port-forward-cell port-forward-actions">{{ $t('config.subnetProxyAction') }}</div>
                        </div>
                        <div class="port-forward-row subnet-proxy-row" v-for="(item, index) in config.proxy_network" :key="index">
                          <div class="port-forward-cell">
                            <span class="port-forward-label">{{ $t('config.subnetCidr') }}</span>
                            <var-input
                              v-model="item.subnet_cidr"
                              :placeholder="$t('config.subnetCidrPlaceholder')"
                              variant="outlined"
                              size="small"
                              :rules="[(v) => validateCidr(v, index, 'subnet')]"
                            />
                          </div>
                          <div class="port-forward-cell">
                            <span class="port-forward-label">{{ $t('config.mappedCidr') }}</span>
                            <var-input
                              v-model="item.mapped_cidr"
                              :placeholder="$t('config.mappedCidrPlaceholder')"
                              variant="outlined"
                              size="small"
                              :rules="[(v) => validateCidr(v, index, 'mapped')]"
                            />
                          </div>
                          <div class="port-forward-cell port-forward-actions">
                            <var-button
                              type="danger"
                              size="small"
                              @click="removeProxyNetwork(index)"
                              icon
                            >
                              <var-icon name="trash-can-outline" />
                            </var-button>
                          </div>
                        </div>
                        <div class="port-forward-add-row">
                          <var-button type="primary" size="small" @click="addProxyNetwork">
                            <var-icon name="plus" />
                            {{ $t('config.addSubnetProxy') }}
                          </var-button>
                        </div>
                      </div>
                    </div>
                    <var-divider />
                    <div class="forward-section">
                      <var-tooltip teleport="body" trigger="click" :offset-x="80">
                        <template #default>
                          <div class="section-subtitle">{{ $t('config.portForward') }}
                            <var-icon name="help-circle-outline" size="16" class="help-icon" />
                          </div>
                        </template>
                        <template #content>
                          <div class="tooltip-multiline">{{ $t('config.portForwardHint') }}</div>
                        </template>
                      </var-tooltip>
                      <div class="port-forward-table">
                        <div class="port-forward-row port-forward-header">
                          <div class="port-forward-cell">{{ $t('config.protocol') }}</div>
                          <div class="port-forward-cell">{{ $t('config.localAddress') }}</div>
                          <div class="port-forward-cell">{{ $t('config.remoteAddress') }}</div>
                          <div class="port-forward-cell port-forward-actions">{{ $t('config.portForwardAction') }}</div>
                        </div>
                        <div class="port-forward-row" v-for="(item, index) in config.port_forward" :key="index">
                          <div class="port-forward-cell">
                            <span class="port-forward-label">{{ $t('config.protocol') }}</span>
                            <var-select
                              v-model="item.proto"
                              variant="outlined"
                              size="small"
                            >
                              <var-option label="TCP" value="tcp" />
                              <var-option label="UDP" value="udp" />
                            </var-select>
                          </div>
                          <div class="port-forward-cell">
                            <span class="port-forward-label">{{ $t('config.localAddress') }}</span>
                            <var-input
                              v-model="item.bind_addr"
                              :placeholder="$t('config.localPlaceholder')"
                              variant="outlined"
                              size="small"
                            />
                          </div>
                          <div class="port-forward-cell">
                            <span class="port-forward-label">{{ $t('config.remoteAddress') }}</span>
                            <var-input
                              v-model="item.dst_addr"
                              :placeholder="$t('config.remotePlaceholder')"
                              variant="outlined"
                              size="small"
                            />
                          </div>
                          <div class="port-forward-cell port-forward-actions">
                            <var-button
                              type="danger"
                              size="small"
                              @click="removePortForward(index)"
                              icon
                            >
                              <var-icon name="trash-can-outline" />
                            </var-button>
                          </div>
                        </div>
                        <div class="port-forward-add-row">
                          <var-button type="primary" size="small" @click="addPortForward">
                            <var-icon name="plus" />
                            {{ $t('config.addPortForward') }}
                          </var-button>
                        </div>
                      </div>
                    </div>
                  </div>
              </var-collapse-item>
            </var-collapse>
          </var-paper>
        </var-form>
      </div>
    </div>

    <!-- 编辑配置弹窗 -->
    <var-popup v-model:show="showCodePage" class="code-editor-popup" :close-on-click-overlay="false" :style="{ width: '100vw', height: '100vh', position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, margin: 0, padding: 'var(--sat, 0px) 0 0 0', maxWidth: 'none', maxHeight: 'none' }">
      <div class="code-editor-wrapper">
        <div class="code-editor-header">
          <span class="editor-title">{{ $t('config.editConfigTitle', { name: currentConfigData.name }) }}</span>
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

    <!-- 重命名配置弹窗 -->
    <var-dialog v-model:show="showRenameDialog" @before-close="confirmEditName"
      :confirm-button-text="$t('common.confirm')" :cancel-button-text="$t('common.cancel')">
      <template #title>
        <span>{{ $t('config.renameTitle') }}</span>
      </template>
      <var-input
        size="small"
        variant="outlined"
        :placeholder="$t('config.renamePlaceholder')"
        v-model="editNameValue"
        :rules="[v => !!v || $t('config.nameRequired')]"
      />
    </var-dialog>

    <!-- 创建新配置弹窗 -->
    <var-dialog v-model:show="showCreateDialog" @before-close="beforeCloseCreateDilog"
      @closed="onCreateDialogClosed" width="340px">
      <template #title>
        <span>{{ $t('config.newConfigTitle') }}</span>
      </template>
      <var-input
        size="small"
        variant="outlined"
        :placeholder="$t('config.profileNameHint')"
        v-model="newConfigName"
        :rules="[v => !!v || $t('config.nameRequired')]"
      />
      <div v-if="showQrScanner" class="qr-scanner-area">
        <div id="qr-reader" class="qr-reader-box"></div>
        <p class="qr-scan-hint">{{ $t('config.scanHint') }}</p>
      </div>
      <template #actions="{ slotClass, cancel, confirm }">
        <div :class="slotClass" style="gap: 8px;">
          <var-button size="small" text @click="onCreateCancel(cancel)">{{ $t('common.cancel') }}</var-button>
          <var-button size="small" text type="primary" @click="onClipboardAdd">{{ $t('config.clipboardAdd') }}</var-button>
          <var-button size="small" text type="primary" @click="onStartScan" :loading="isScanning">{{ $t('config.scanAdd') }}</var-button>
          <var-button size="small" text type="primary" @click="onCreateConfirm">{{ $t('config.editAdd') }}</var-button>
        </div>
      </template>
    </var-dialog>

    <!-- 分享配置弹窗 -->
    <var-dialog v-model:show="showShareConfigType" :title="$t('config.selectShareType')"
      :confirm-button-text="$t('config.downloadFile')"  @confirm="downloadConfig" 
      :cancel-button-text="$t('config.copyClipboard')" @cancel="copyConfig"
      width="320px">
      <div class="share-qr-area">
        <img v-if="shareQrDataUrl" :src="shareQrDataUrl" class="share-qr-img" alt="QR Code" />
        <var-loading v-else size="small" />
        <p class="share-qr-hint">{{ $t('config.shareQrHint') }}</p>
      </div>
    </var-dialog>

    <!-- 删除配置弹窗 -->
    <var-dialog v-model:show="showDeleteDialog" :title="$t('config.confirmDelete', { name: currentConfigData.name })"
      :confirm-button-text="$t('config.confirm')"  @confirm="deleteCurrentConfig" 
      :cancel-button-text="$t('config.cancel')" @cancel="showDeleteDialog = false">
    </var-dialog>

    <!-- 公共节点帮助弹窗 -->
    <var-popup position="top" v-model:show="showPublicPeerTip">
      <div class="help-content">
        <p class="help-paragraph"><span class="help-bold">{{ $t('config.peerHelp.publicPeer') }}</span>：{{ $t('config.peerHelp.publicPeerDesc') }}</p>
        <p class="help-paragraph"><span class="help-bold">{{ $t('config.peerHelp.dynamicPeer') }}</span>：{{ $t('config.peerHelp.dynamicPeerDesc') }}</p>
        <p class="help-paragraph"><span class="help-bold">{{ $t('config.peerHelp.peerRefresh') }}</span>：{{ $t('config.peerHelp.peerRefreshDesc') }}</p>
        <p class="help-paragraph"><span class="help-bold">{{ $t('config.peerHelp.peerCheck') }}</span>：{{ $t('config.peerHelp.peerCheckDesc') }}</p>
        <div style="margin-top: 20px;">
          <p class="help-paragraph"><span class="help-bold">{{ $t('config.peerHelp.thanks') }}</span></p>
          <var-table scroller-height="280px">
            <thead>
              <tr>
                <th>{{ $t('config.peerHelp.communityNode') }}</th>
                <th>{{ $t('config.peerHelp.provider') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in publicPeerOptions" :key="item.uri">
                <td v-if="item.owner !== ''" style="font-size: 10pt;">{{ item.uri }}</td>
                <td v-if="item.owner !== ''" style="font-size: 10pt;">{{ item.owner }}</td>
              </tr>
            </tbody>
          </var-table>
        </div>
      </div>
  </var-popup>
  </div>
</template>

<script setup>
import { copyToClipboard, readFromClipboard } from '../utils/clipboard.js'
import { openDownloadUrl } from '../utils/download.js'
import { validateIP, validateIPPort } from '../utils/validate.js'
import { ref, computed, inject, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import toast from '../components/toast.js'
import { api } from '../utils/api.js'
import CodeEditor from '../components/CodeEditor.vue'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiEye, mdiEyeOff, mdiHomeEdit, mdiRouterNetwork, mdiMonitor, mdiLanConnect, mdiTuneVariant, mdiPlus, mdiDrawPen, mdiShareOutline, mdiSquareEditOutline, mdiTrashCanOutline  } from '@mdi/js'
import { mdilPencil, mdilAccount, mdilLock } from '@mdi/light-js'
import { Html5Qrcode } from 'html5-qrcode'
import QRCode from 'qrcode'


// 显示模式： 0 修改 1 快速新增 2 普通新增
const { t } = useI18n()
const showMode = ref(0)
const fastSettingMode = inject('fastSettingMode', ref(false))
const publicPeerOptions = ref([])
const customPeer = ref('')
const customListener = ref('')
const advancedOpen = ref([])
const forwardOpen = ref(['forward'])
const forwardRenderKey = ref(0)
const advancedRenderKeys = ref({
  hostInfo: 0,
  connection: 0,
  performance: 0
})
// 下拉菜单内 var-input 渲染键，用于下拉打开后强制重建以正确显示 placeholder
const selectInputRenderKey = ref({
  peer: 0,
  listener: 0,
  exitNode: 0,
  route: 0
})

const onSelectFocus = (name) => {
  nextTick(() => {
    setTimeout(() => {
      selectInputRenderKey.value[name]++
    }, 150)
  })
}
const form = ref(null)
const showShareConfigType = ref(false)
const shareQrDataUrl = ref('')
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
const showMoreMenu = ref(false)
const lanIps = ref([])
const platform = ref('android')
const configList = ref([])
const selectedConfig = ref('')
const showCreateDialog = ref(false)
const showRenameDialog = ref(false)
const showQrScanner = ref(false)
const isScanning = ref(false)
const html5QrCode = ref(null)
const newConfigName = ref('')
const editNameValue = ref('')
const customExitNode = ref('')
const customRoute = ref('')
const encryptionAlgorithmList = ref(['aes-gcm','xor','chacha20','aes-gcm','aes-gcm-256','openssl-aes128-gcm','openssl-aes256-gcm','openssl-chacha20'])
const defaultProtocolList = computed(() => [{label: t('config.defaultOption'), value: ''}, {label: 'tcp', value: 'tcp'}, {label: 'udp', value: 'udp'}, {label: 'quic', value: 'quic'}, {label: 'wg', value: 'wg'}, {label: 'ws', value: 'ws'}, {label: 'wss', value: 'wss'}, {label: 'faketcp', value: 'faketcp'}])
const compressionOptions = computed(() => [{label: t('config.noCompression'), value: 'none'}, {label: 'zstd', value: 'zstd'}])

const config = ref({
  hostname: '',
  dhcp: true,
  ipv4: '',
  network_identity: { network_name: '', network_secret: '' },
  listeners: [],
  peer: [],
  proxy_network: [],
  exit_nodes: [],
  routes: [],
  socks5_proxy: null,
  port_forward: [],
  flags: {
    bind_device: true,
    enable_ipv6: true,
    proxy_forward_by_system: true,
    enable_encryption: true,
    private_mode: true,
    multi_thread: true,
    latency_first: true,
  },
})

const currentConfigData = computed(() => configList.value.find(c => c.profile === selectedConfig.value) || {})
const currentConfigAutostart = computed(() => currentConfigData.value.autostart || false)

const hostInfoSwitches = [
  { key: 'enable_ipv6', label: 'config.flags.enable_ipv6.label', tooltip: 'config.flags.enable_ipv6.tooltip' },
  { key: 'no_tun', label: 'config.flags.no_tun.label', tooltip: 'config.flags.no_tun.tooltip' },
  { key: 'bind_device', label: 'config.flags.bind_device.label', tooltip: 'config.flags.bind_device.tooltip' },
  { key: 'accept_dns', label: 'config.flags.accept_dns.label', tooltip: 'config.flags.accept_dns.tooltip' },
  { key: 'use_smoltcp', label: 'config.flags.use_smoltcp.label', tooltip: 'config.flags.use_smoltcp.tooltip' },
]

const connectionSwitches = [
  { key: 'p2p_only', label: 'config.flags.p2p_only.label', tooltip: 'config.flags.p2p_only.tooltip' },
  { key: 'disable_p2p', label: 'config.flags.disable_p2p.label', tooltip: 'config.flags.disable_p2p.tooltip' },
  { key: 'lazy_p2p', label: 'config.flags.lazy_p2p.label', tooltip: 'config.flags.lazy_p2p.tooltip' },
  { key: 'need_p2p', label: 'config.flags.need_p2p.label', tooltip: 'config.flags.need_p2p.tooltip' },
  { key: 'disable_tcp_hole_punching', label: 'config.flags.disable_tcp_hole_punching.label', tooltip: 'config.flags.disable_tcp_hole_punching.tooltip' },
  { key: 'disable_udp_hole_punching', label: 'config.flags.disable_udp_hole_punching.label', tooltip: 'config.flags.disable_udp_hole_punching.tooltip' },
  { key: 'disable_sym_hole_punching', label: 'config.flags.disable_sym_hole_punching.label', tooltip: 'config.flags.disable_sym_hole_punching.tooltip' },
  { key: 'disable_upnp', label: 'config.flags.disable_upnp.label', tooltip: 'config.flags.disable_upnp.tooltip' },
  { key: 'enable_kcp_proxy', label: 'config.flags.enable_kcp_proxy.label', tooltip: 'config.flags.enable_kcp_proxy.tooltip' },
  { key: 'disable_kcp_input', label: 'config.flags.disable_kcp_input.label', tooltip: 'config.flags.disable_kcp_input.tooltip' },
  { key: 'enable_quic_proxy', label: 'config.flags.enable_quic_proxy.label', tooltip: 'config.flags.enable_quic_proxy.tooltip' },
  { key: 'disable_quic_input', label: 'config.flags.disable_quic_input.label', tooltip: 'config.flags.disable_quic_input.tooltip' },
]

const performanceSwitches = [
  { key: 'latency_first', label: 'config.flags.latency_first.label', tooltip: 'config.flags.latency_first.tooltip' },
  { key: 'multi_thread', label: 'config.flags.multi_thread.label', tooltip: 'config.flags.multi_thread.tooltip' },
  { key: 'private_mode', label: 'config.flags.private_mode.label', tooltip: 'config.flags.private_mode.tooltip' },
  { key: 'enable_encryption', label: 'config.flags.enable_encryption.label', tooltip: 'config.flags.enable_encryption.tooltip' },
]

const listenerOptions = ref([
  'tcp://0.0.0.0:11010', 'tcp://[::]:11010',
  'udp://0.0.0.0:11010', 'udp://[::]:11010',
  'wg://0.0.0.0:11011', 'wg://[::]:11011',
  'ws://0.0.0.0:11011', 'ws://[::]:11011',
  'wss://0.0.0.0:11012', 'wss://[::]:11012',
  'quic://0.0.0.0:11012', 'quic://[::]:11012',
  'faketcp://0.0.0.0:11013', 'faketcp://[::]:11013',
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
  if (!config.value.proxy_network) {
    config.value.proxy_network = []
  }
  const entries = config.value.proxy_network
  for (let i = 0; i < entries.length; i++) {
    const item = entries[i]
    if (!item.subnet_cidr || !item.subnet_cidr.trim()) {
      toast.warning(t('config.subnetCidrRequired', { index: i + 1 }))
      return
    }
    if (!cidrRegex.test(item.subnet_cidr.trim())) {
      toast.warning(t('config.subnetCidrInvalid', { index: i + 1 }))
      return
    }
    if (item.mapped_cidr && item.mapped_cidr.trim() && !cidrRegex.test(item.mapped_cidr.trim())) {
      toast.warning(t('config.mappedCidrInvalid', { index: i + 1 }))
      return
    }
  }
  config.value.proxy_network.push({ subnet_cidr: '', mapped_cidr: '' })
}

const removeProxyNetwork = (index) => {
  config.value.proxy_network.splice(index, 1)
}

function getCidrPrefixLength(cidr) {
  if (!cidr || !cidr.includes('/')) return -1
  const parts = cidr.split('/')
  const prefix = parseInt(parts[1], 10)
  if (isNaN(prefix) || prefix < 0 || prefix > 32) return -1
  return prefix
}

const cidrRegex = /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/
const routeRegex = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/

const validateCidr = (v, index, field) => {
  if (!v) return true
  if (!cidrRegex.test(v)) {
    return t('config.invalidCidrFormat')
  }
  const prefix = getCidrPrefixLength(v)
  if (prefix < 0) {
    return t('config.invalidCidrFormat')
  }
  const item = config.value.proxy_network[index]
  if (item) {
    const otherField = field === 'subnet' ? item.mapped_cidr : item.subnet_cidr
    if (otherField && otherField.includes('/')) {
      const otherPrefix = getCidrPrefixLength(otherField)
      if (otherPrefix >= 0 && prefix !== otherPrefix) {
        return t('config.cidrPrefixMismatch')
      }
    }
  }
  return true
}

const validateSubnetProxy = () => {
  if (!config.value.proxy_network) return null
  const entries = config.value.proxy_network
  for (let i = 0; i < entries.length; i++) {
    const item = entries[i]
    if (!item.subnet_cidr || !item.subnet_cidr.trim()) {
      return t('config.subnetCidrRequired', { index: i + 1 })
    }
    if (!cidrRegex.test(item.subnet_cidr.trim())) {
      return t('config.subnetCidrInvalid', { index: i + 1 })
    }
    if (item.mapped_cidr && item.mapped_cidr.trim()) {
      if (!cidrRegex.test(item.mapped_cidr.trim())) {
        return t('config.mappedCidrInvalid', { index: i + 1 })
      }
      const subnetPrefix = getCidrPrefixLength(item.subnet_cidr.trim())
      const mappedPrefix = getCidrPrefixLength(item.mapped_cidr.trim())
      if (subnetPrefix !== mappedPrefix) {
        return t('config.cidrPrefixSizeMismatch', { index: i + 1 })
      }
    }
  }
  return null
}

const validateRoutes = () => {
  if (!config.value.routes || config.value.routes.length === 0) return null
  const entries = config.value.routes
  for (let i = 0; i < entries.length; i++) {
    if (!routeRegex.test(entries[i])) {
      return t('config.routeInvalid', { index: i + 1 })
    }
  }
  return null
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
      toast.error(t('config.validationFailed'))
      return
    }
    const pfError = validatePortForward()
    if (pfError) {
      reject();
      toast.error(pfError)
      return
    }
    const spError = validateSubnetProxy()
    if (spError) {
      reject();
      toast.error(spError)
      return
    }
    const rtError = validateRoutes()
    if (rtError) {
      reject();
      toast.error(rtError)
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
          toast.success(t('config.autostartSuccess'))
          currentConfigData.value.autostart = true
          currentConfigAutostart.value = true
        }).catch(e => {
          toast.error(t('config.autostartFailed', { error: e.message }))
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
    data._new_config = showMode.value != 0
    data.peer = data.peer.map(e => ({ uri: e }))
    data.proxy_network = data.proxy_network
      .filter(e => e.subnet_cidr && e.subnet_cidr.trim())
      .map(e => {
        const result = { cidr: e.subnet_cidr.trim() }
        const mapped = e.mapped_cidr ? e.mapped_cidr.trim() : ''
        if (mapped) result.mapped_cidr = mapped
        return result
      })
    data.dhcp = !data.ipv4 || !(data.ipv4.trim())
    if (data.flags.enable_ipv6 === undefined) data.flags.enable_ipv6 = true
    if (data.flags.enable_encryption === undefined) data.flags.enable_encryption = true
    data.socks5_proxy = ensureInt(data.socks5_proxy)
    if (data.socks5_proxy && !isNaN(data.socks5_proxy) && data.socks5_proxy > 0) {
      data.socks5_proxy = `socks5://0.0.0.0:${data.socks5_proxy}`
    } else {
      delete data.socks5_proxy
    }
    if (data.flags.instance_recv_bps_limit > 0) {
      data.flags.instance_recv_bps_limit = ensureInt(data.flags.instance_recv_bps_limit)
    } else {
      delete data.flags.instance_recv_bps_limit
    }
    // 删除 flags 中 空 字段
    ['dev_name', 'encryption_algorithm', 'default_protocol', 'compression', 'relay_network_whitelist'].forEach(key => {
      if (config.value.flags[key] == null || config.value.flags[key].trim() === '') {
        data.flags[key] = null
      }
    });
    // 删除config一级属性， 空值 字段
    ['hostname', 'ipv4', 'rpc_portal'].forEach(key => {
      if (config.value[key] == null || config.value[key].trim() === '') {
        data[key] = null
      }
    });
    // 删除空数组字段
    ['peer', 'listeners', 'proxy_network', 'exit_nodes', 'port_forward', 'routes'].forEach(key => {
      if (data[key] == null || data[key].length === 0) {
        data[key] = null
      }
    });

    api.configs.save(data).then(async res => {
      toast.success(t('config.saveSuccess'))
      if (fastSettingMode.value && platform.value !== 'android') {
        // 快速设置模式，自动开启启动服务
        await autoStart()
      }
      if (fastSettingMode.value || await checkStatus()) {
        const restartLoading = toast.loading(fastSettingMode.value ? t('config.serviceStarting') : t('config.serviceRestarting'))
            await api.services.restart(selectedConfig.value).then(() => {
              toast.success(t('config.serviceStarted'))
            }).finally(() => {
              restartLoading.clear()
            })
      }      
      if (fastSettingMode.value) {
        toast.info(t('config.exitSetupMode'))
        fastSettingMode.value = false
      }
      if (showMode.value != 0) {
        exitAddMode(res.data.profile)
      }
    }).catch(e => {
      toast.error(t('config.saveFailed', { error: e.message }))
      reject(e)
    }).finally(() => {
      resolve()
    })
  }).catch(e => {
    console.error('保存配置失败:', e.message)
    reject(e)
  })
}

const downloadConfig = () => {
  const url = api.configs.getShareConfigDownloadUrl(selectedConfig.value)
  openDownloadUrl(url)
}

const copyConfig = () => {
  api.configs.getShareConfigStr(selectedConfig.value).then(resp => {
    copyToClipboard(resp.data)
    toast.success(t('config.copied'))
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
      toast.success(t('config.saveSuccess'))
      // 先检查服务状态，只有运行中才重启
      api.services.status(selectedConfig.value).then(resp => {
        if (resp.data) {
          const restartLoading = toast.loading(t('config.serviceRestarting'))
          api.services.restart(selectedConfig.value).then(() => {
            toast.success(t('config.serviceStarted'))
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
        toast.success(t('config.gotLatestNodes'))
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
      toast.warning(t('config.checkingNodes'))
      return
    }
    const checkToast = toast.info(t('config.checkingNodesStart'), 30000)
    isPeerChecking.value = true
    api.peers.checkPeers({ 'profile': selectedConfig.value, 'refresh': true }).then(data => {
      publicPeerOptions.value = data.data
      toast.success(t('config.checkSuccess'))
      publicPeerOptions.value.sort((a, b) => {
        const aIn = config.value.peer.includes(a.uri);
        const bIn = config.value.peer.includes(b.uri);
        return bIn - aIn;
      });
    }).catch(() => {
      toast.error(t('config.checkFailed'))
    }).finally(() => {
      isPeerChecking.value = false
      checkToast.clear()
      resolve()
    })
  })
}

const formatBackendConfigToConfig = (json) => {
  json.peer = (json.peer || []).map(e => e.uri)
    json.proxy_network = (json.proxy_network || []).map(e => ({
      subnet_cidr: e.cidr || '',
      mapped_cidr: e.mapped_cidr || ''
    }))
    if (json.socks5_proxy) {
      json.socks5_proxy = json.socks5_proxy.replace('socks5://0.0.0.0:', '')
    }
    if (json.listeners) {
      json.listeners.forEach(e => {
        if (!listenerOptions.value.includes(e)) listenerOptions.value.unshift(e)
      })
    }
    if (json.flags?.mtu) json.flags.mtu = ensureInt(json.flags.mtu)
    if (json.flags?.multi_thread_count) json.flags.multi_thread_count = ensureInt(json.flags.multi_thread_count)
    if (json.flags?.instance_recv_bps_limit) json.flags.instance_recv_bps_limit = ensureInt(json.flags.instance_recv_bps_limit)
    return  {
      ...json,
      hostname: json.hostname ?? '',
      ipv4: json.ipv4 ?? '',
      routes: json.routes || [],
      listeners: json.listeners || [],
      exit_nodes: json.exit_nodes || [],
      port_forward: json.port_forward || [],
      peer: json.peer || [],
      socks5_proxy: json.socks5_proxy ?? null,
      flags: {
        ...config.value.flags,
        ...json.flags,
        mtu: json.flags?.mtu ?? undefined,
        multi_thread_count: json.flags?.multi_thread_count ?? undefined,
      }
    }
}

const loadConfig = (profile) => {
  isLoadingConfig.value = true
  advancedOpen.value = []
  forwardOpen.value = []
  return api.configs.get(profile).then(data => {
    const json = data.data
    config.value = formatBackendConfigToConfig(json)
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
      console.log("configList.value:", configList.value)
    } else {
      configList.value = []
    }
  } catch (error) {
    toast.error(t('config.loadConfigListFailed', { error: error.message || t('config.unknown') }))
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
      toast.error(t('config.loadConfigFailed', { error: error.message || t('config.unknown') }))
    }
  }
}

watch(advancedOpen, (newVal) => {
  if (newVal?.includes('hostInfo')) {
    nextTick(() => {
      setTimeout(() => {
        advancedRenderKeys.value.hostInfo++
      }, 350)
    })
  }
  if (newVal?.includes('connection')) {
    nextTick(() => {
      setTimeout(() => {
        advancedRenderKeys.value.connection++
      }, 350)
    })
  }
  if (newVal?.includes('performance')) {
    nextTick(() => {
      setTimeout(() => {
        advancedRenderKeys.value.performance++
      }, 350)
    })
  }
})

watch(forwardOpen, (newVal) => {
  if (newVal?.includes('forward')) {
    nextTick(() => {
      setTimeout(() => {
        forwardRenderKey.value++
      }, 350)
    })
  }
})

watch(showShareConfigType, async (newVal) => {
  if (newVal) {
    shareQrDataUrl.value = ''
    try {
      const resp = await api.configs.getShareConfigStr(selectedConfig.value)
      const configStr = resp.data
      shareQrDataUrl.value = await QRCode.toDataURL(configStr, {
        width: 280,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#ffffff'
        }
      })
    } catch (err) {
      console.error('Generate QR code failed:', err)
    }
  } else {
    shareQrDataUrl.value = ''
  }
})

const deleteCurrentConfig = async () => {
  const cfg = currentConfigData.value
  if (!cfg || !cfg.profile) return
  isDeletingConfig.value = true
  return new Promise(async(resolve, reject) => {
    try {
      const isRunning = await api.services.status(selectedConfig.value).then(resp => resp.data)
      if (isRunning) {
        const stoping = toast.loading(t('config.serviceStopping'))
        await api.services.stop(selectedConfig.value).then(() => toast.success(t('config.serviceStopped'))).finally(() => {
          stoping.clear()
        })
        // 停止et服务可能本地网络会有波动，导致下一次请求被被阻断
        await new Promise(r => setTimeout(r, 2000));
      }
      await api.configs.delete(cfg.profile)
      toast.success(t('config.configDeleted'))
      await loadConfigs()
      if (configList.value.length > 0) {
        selectedConfig.value = configList.value[0].profile
        await loadConfig(configList.value[0].profile)
      } else {
        selectedConfig.value = ''
      }
      resolve()
    } catch (error) {
      toast.error(t('config.configDeleteFailed', { error: error.message }))
      reject(error)
    } finally {
      isDeletingConfig.value = false
    }
  })
}

const beforeCloseCreateDilog = async (action, done) => {
  try {
    stopQrScanner()
    if (action === 'confirm') {
      if (confirmCreateConfig()) {
        done()
      }
    } else {
      await exitAddMode()
      done()
    }
  } catch {
    done()
  }
}

const onCreateCancel = async (cancel) => {
  stopQrScanner()
  await exitAddMode()
  cancel()
}

const onCreateConfirm = () => {
  stopQrScanner()
  if (confirmCreateConfig()) {
    showCreateDialog.value = false
  }
}

const onCreateDialogClosed = () => {
  stopQrScanner()
}

const onStartScan = async () => {
  if (isScanning.value) {
    stopQrScanner()
    return
  }
  try {
    const devices = await Html5Qrcode.getCameras()
    if (!devices || devices.length === 0) {
      toast.error(t('config.cameraNotSupported'))
      return
    }
    showQrScanner.value = true
    isScanning.value = true
    await nextTick()
    const qrCodeScanner = new Html5Qrcode('qr-reader')
    html5QrCode.value = qrCodeScanner
    let cameraId = ''
    if (devices.length >= 2) {
      cameraId = devices[1].id
    } else {
      cameraId = devices[0].id
    }
    await qrCodeScanner.start(
      cameraId ? { deviceId: { exact: cameraId } } : { facingMode: 'environment' },
      {
        fps: 10,
        qrbox: (viewfinderWidth, viewfinderHeight) => {
          const minEdge = Math.min(viewfinderWidth, viewfinderHeight)
          const size = Math.floor(minEdge * 0.85)
          return { width: size, height: size }
        },
      },
      (decodedText) => {
        onQrScanSuccess(decodedText)
      },
      () => {}
    )
  } catch (err) {
    console.error('QR scan error:', err)
    isScanning.value = false
    showQrScanner.value = false
    if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
      toast.error(t('config.cameraPermissionDenied'))
    } else if (err?.name === 'NotFoundError') {
      toast.error(t('config.cameraNotSupported'))
    } else {
      toast.error(t('config.scanFailed'))
    }
  }
}

const processTomlConfig = async (tomlText) => {
  try {
    const res = await api.configs.parseToml({ toml: tomlText })
    const parsedData = res.data
    if (parsedData && typeof parsedData === 'object') {
      if (!newConfigName.value.trim()) {
        const networkName = parsedData.network_identity?.network_name
        if (networkName) {
          newConfigName.value = networkName
        } else {
          newConfigName.value = t('config.scanConfig')
        }
      }
      if (confirmCreateConfig()) {
        config.value = formatBackendConfigToConfig(parsedData)
        config.value._profile = selectedConfig.value
        toast.success(t('config.scanSuccess'))
        showCreateDialog.value = false
        await nextTick()
        await saveConfig()
      }
    }
  } catch (err) {
    toast.error(t('config.parseTomlFailed') + ': ' + (err.message || ''))
  }
}

const onQrScanSuccess = async (decodedText) => {
  stopQrScanner()
  await processTomlConfig(decodedText)
}

const onClipboardAdd = async () => {
  try {
    const text = await readFromClipboard()
    if (!text || !text.trim()) {
      toast.warning(t('config.clipboardEmpty'))
      return
    }
    await processTomlConfig(text.trim())
  } catch (err) {
    if (err?.name === 'NotAllowedError') {
      toast.error(t('config.clipboardPermissionDenied'))
    } else {
      toast.error(t('config.clipboardReadFailed'))
    }
  }
}

const stopQrScanner = () => {
  if (html5QrCode.value) {
    const scanner = html5QrCode.value
    html5QrCode.value = null
    isScanning.value = false
    showQrScanner.value = false
    scanner.stop().then(() => scanner.clear()).catch(() => {})
  } else {
    isScanning.value = false
    showQrScanner.value = false
  }
}

const confirmCreateConfig = () => {
  if (!newConfigName.value.trim()) {
    toast.warning(t('config.profileNameRequired'))
    return false
  }
  const name = newConfigName.value.trim()
  const profile = name ? `${name}.toml` : ''
  config.value = {}
  config.value._profile = profile
  config.value.dhcp = true,
  config.value.listeners = [],
  config.value.peer = [],
  config.value.proxy_network = [],
  config.value.network_identity = { network_name: '', network_secret: '' },
  config.value.flags = {
    bind_device: true,
    enable_ipv6: true,
    proxy_forward_by_system: true,
    enable_encryption: true,
    private_mode: true,
    multi_thread: true,
    latency_first: true,
  }
  configList.value.push({ 'profile': profile, 'name': name, 'autostart': false })
  selectedConfig.value = profile
  newConfigName.value = ''
  return true
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
    toast.warning(t('config.nameRequired'))
    return done()
  }
  if (newName === currentConfigData.value.name) {
    showRenameDialog.value = false
    return done()
  }
  isRenaming.value = true
  const loadingToast = toast.loading(t('config.renaming'))
  try {
    const isRunning = await api.services.status(selectedConfig.value).then(resp => resp.data)
    if (isRunning) {
      const stoping = toast.loading(t('config.serviceStopping'))
      await api.services.stop(selectedConfig.value).then(() => toast.success(t('config.serviceStopped'))).finally(() => {
        stoping.clear()
      })
      // 停止et服务可能本地网络会有波动，导致下一次请求被被阻断
      await new Promise(r => setTimeout(r, 2000));
    }
    const res = await api.configs.rename(selectedConfig.value, newName+'.toml').catch(error => {
      toast.error(t('config.configRenameFailed', { error: error.message }))
      throw error
    })
    toast.success(t('config.configRenamed'))
    await loadConfigs()
    selectedConfig.value = res.data.profile
    currentConfigData.value.name = res.data.name
    showRenameDialog.value = false
    if (isRunning) {
      const starting = toast.loading(t('config.serviceStarting'))
      await api.services.start(selectedConfig.value).then(() => toast.success(t('config.serviceStarted')))
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
      toast.success(val ? t('config.autostartEnabled') : t('config.autostartDisabled'))
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

const exitAddMode = async (showProfile) => {
  stopQrScanner()
  showMode.value = 0
  showCreateDialog.value = false
  newConfigName.value = ''
  await loadConfigs()
  selectedConfig.value = showProfile || selectedConfig.value
  // selectedConfig.value = showProfile || configList.value?.[0]?.profile || ''
  await loadConfig(selectedConfig.value)
}

const getLanIps = () => {
  api.configs.getLanIps().then(data => {
    lanIps.value = data.data
  })
}

const addExitNode = () => {
  if (!customExitNode.value.trim()) {
    toast.warning(t('config.exitNodeRequired'))
    return
  }
  const error = validateIP(customExitNode.value.trim(), t('config.exitNodes'))
  if (error) {
    toast.warning(error)
    return
  }
  if (!config.value.exit_nodes) {
    config.value.exit_nodes = []
  }
  if (config.value.exit_nodes.includes(customExitNode.value.trim())) {
    toast.warning(t('config.exitNodeExists', { name: customExitNode.value.trim() }))
    return
  }
  config.value.exit_nodes.push(customExitNode.value.trim())
  customExitNode.value = ''
}

const addRoute = () => {
  if (!customRoute.value.trim()) {
    toast.warning(t('config.routeRequired'))
    return
  }
  if (!routeRegex.test(customRoute.value.trim())) {
    toast.warning(t('config.invalidRouteFormat'))
    return
  }
  if (!config.value.routes) {
    config.value.routes = []
  }
  if (config.value.routes.includes(customRoute.value.trim())) {
    toast.warning(t('config.routeExists', { name: customRoute.value.trim() }))
    return
  }
  config.value.routes.push(customRoute.value.trim())
  customRoute.value = ''
}

const validatePortForward = () => {
  if (!config.value.port_forward) return null
  const entries = config.value.port_forward
  for (let i = 0; i < entries.length; i++) {
    const item = entries[i]
    if (!item.bind_addr || !item.bind_addr.trim()) {
      return `端口转发[${i + 1}]本地IP端口不能为空`
    }
    const error1 = validateIPPort(item.bind_addr.trim(), `端口转发[${i + 1}]本地IP端口`)
    if (error1) return error1
    if (!item.dst_addr || !item.dst_addr.trim()) {
      return `端口转发[${i + 1}]虚拟网络IP端口不能为空`
    }
    const error2 = validateIPPort(item.dst_addr.trim(), `端口转发[${i + 1}]虚拟网络IP端口`)
    if (error2) return error2
  }
  return null
}

const addPortForward = () => {
  if (!config.value.port_forward) {
    config.value.port_forward = []
  }
  const error = validatePortForward()
  if (error) {
    toast.warning(error)
    return
  }
  config.value.port_forward.push({ proto: 'tcp', bind_addr: '', dst_addr: '' })
}

const removePortForward = (index) => {
  config.value.port_forward.splice(index, 1)
}

onMounted(async () => {
  // 如果是用户版（非管理员权限），则开启no_tun
  if (window.location.href.includes('/cgi/ThirdParty/EasyTier-EUI.User/index.cgi')) {
    config.value.flags.no_tun = true
  }
  api.settings.getEuiInfo().then(data => {
    platform.value = data.data.platform
  })
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

onUnmounted(() => {
  fastSettingMode.value = false
})
</script>

<style scoped>
.config-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.config-else-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.config-skeleton {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ── 工具栏骨架 ── */
.sk-toolbar {
  flex-shrink: 0;
  margin: 12px 16px 0;
  padding: 12px 20px;
  border-radius: 20px;
  background: var(--color-surface-container);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 通用圆角条 */
.sk-pill {
  border-radius: 7px;
  background: rgba(var(--color-on-surface-rgb, 0, 0, 0), 0.05);
  overflow: hidden;
  position: relative;
}

html.dark .sk-pill {
  background: rgba(255, 255, 255, 0.05);
}

.sk-pill-select {
  height: 32px;
  width: 160px;
  border-radius: 8px;
}

.sk-pill-btn {
  height: 28px;
  width: 56px;
  border-radius: 6px;
}

.sk-pill-btn-sm {
  width: 40px;
}

/* 呼吸微光 */
.sk-breathe {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(99, 132, 255, 0.12) 20%,
    rgba(127, 90, 240, 0.18) 40%,
    rgba(99, 132, 255, 0.12) 60%,
    transparent 80%
  );
  animation: sk-breathe 2.4s ease-in-out infinite;
  will-change: opacity;
}

html.dark .sk-breathe {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(99, 132, 255, 0.2) 20%,
    rgba(167, 139, 250, 0.28) 40%,
    rgba(99, 132, 255, 0.2) 60%,
    transparent 80%
  );
}

@keyframes sk-breathe {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

/* ── 内容骨架 ── */
.sk-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sk-section {
  padding: 12px 16px;
  border-radius: 14px;
  background: var(--color-surface-container);
  display: flex;
  flex-direction: column;
  gap: 10px;
  animation: sk-slideUp 0.4s ease both;
}

@keyframes sk-slideUp {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.sk-section-title {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-outline-variant);
}

.sk-section-title--only {
  padding-bottom: 0;
  border-bottom: none;
}

.sk-pill-title {
  height: 18px;
  width: 120px;
  border-radius: 9px;
}

.sk-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sk-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sk-pill-label {
  height: 12px;
  width: 64px;
  border-radius: 6px;
}

.sk-pill-input {
  height: 28px;
  width: 100%;
  max-width: 420px;
  border-radius: 8px;
}

/* ── 骨架屏遮罩层（切换配置时） ── */
.sk-overlay {
  position: absolute;
  inset: 0;
  z-index: 100;
  background: var(--color-surface);
  opacity: 0.6;
  border-radius: 16px;
  cursor: wait;
}

/* ── 表单骨架（切换配置时） ── */
.sk-config-section {
  margin: 0 16px;
  padding: 18px 20px;
  border-radius: 14px;
  background: var(--color-surface-container);
  display: flex;
  flex-direction: column;
  gap: 14px;
  animation: sk-slideUp 0.4s ease both;
}

.sk-config-section + .sk-config-section {
  margin-top: 14px;
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
  border-radius: 20px;
  background: var(--color-surface-container) !important;
}

.toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: nowrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  flex-wrap: nowrap;
  min-width: 0;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
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

.column-btn {
  margin-left: auto;
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
  flex-wrap: wrap;
  min-width: 0;
}

.toggle-label {
  display: inline-block;
  font-size: 12px;
  color: var(--color-on-surface-variant);
  max-width: 120px;
  word-break: break-word;
  line-height: 1.3;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 10px;
  margin-top: 4px;
  position: relative;
  padding-bottom: calc(64px + var(--sab, 0px) + 16px);
}

.config-section {
  margin: 0 0 16px;
  padding: 20px;
  border-radius: 20px;
  background: var(--color-surface-container-low) !important;
}

.merged-section {
  display: flex;
  flex-direction: column;
  padding-bottom: 20px;
  background: var(--color-surface-container-low) !important;
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

.unavailable-tag {
  background: var(--color-danger);
  color: #fff;
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
  display: inline-block;
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

/* ===== 配置面板通用样式 ===== */
.config-section-panel {
  margin-top: 12px;
  border-radius: 20px;
  overflow: hidden;
  background: var(--color-surface-container-low) !important;
}

:deep(.panel-section-inner .var-collapse-item) {
  border-radius: 12px;
  overflow: hidden;
  background: transparent !important;
}

:deep(.panel-section-inner .var-collapse-item__header) {
  padding: 12px 16px;
}

:deep(.panel-section-inner .var-divider) {
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
  min-width: 0;
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

.forward-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 8px 0;
}

.forward-section {
  margin-bottom: 8px;
}

.port-forward-table {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.port-forward-row {
  display: grid;
  grid-template-columns: 100px 1fr 1fr 60px;
  gap: 12px;
  align-items: center;
}

.subnet-proxy-row {
  display: grid;
  grid-template-columns: 1fr 1fr 60px;
  gap: 12px;
  align-items: center;
}

.port-forward-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  padding: 0 4px;
}

.port-forward-cell {
  min-width: 0;
}

.port-forward-label {
  display: none;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.port-forward-actions {
  display: flex;
  align-items: center;
  justify-content: center;
}

.port-forward-add-row {
  display: flex;
  justify-content: flex-start;
  padding-top: 4px;
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

  :deep(.var-popup__content::before),
  :deep(.var-popup__content::after) {
    display: none !important;
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
  background: var(--color-surface-container) !important;
}

.help-content tr {
  --table-tbody-td-text-color: var(--color-text) !important;
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.1) !important;
}

/* ===== Deep 覆盖 ===== */
:deep(.var-form) {
  display: flex;
  flex-direction: column;
  /* gap: 16px; */
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

/* ===== 响应式 ===== */
@media (max-width: 767px) {
  .config-page {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    /*padding-bottom: calc(64px + var(--sab, 0px) + 16px);*/
  }

  .config-else-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 0;
  }

  .toolbar {
    flex-shrink: 0;
    margin: 16px 12px 4px;
    padding: 12px;
    border-radius: 16px;
    position: relative;
    z-index: 10;
    overflow: visible !important;
  }

  .toolbar-row {
    gap: 6px;
  }

  .toolbar-left {
    flex: 0 1 auto;
  }

  .toolbar-right {
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
    padding-bottom: calc(64px + var(--sab, 0px) + 16px);
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

    :deep(.var-popup__content::before),
    :deep(.var-popup__content::after) {
      display: none !important;
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

  /* 端口转发移动端卡片布局 */
  .port-forward-header {
    display: none;
  }

  .config-section-panel {
    margin-top: 12px;
  }

  .port-forward-row {
    grid-template-columns: 1fr;
    gap: 4px;
    padding: 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.08);
    color: var(--color-text);
  }

  .port-forward-label {
    display: block;
  }

  .port-forward-cell {
    display: flex;
    flex-direction: column;
  }

  .port-forward-actions {
    flex-direction: row;
    justify-content: flex-end;
    padding-top: 4px;
  }
}

/* 移动端端口转发暗色模式 */
html.dark .port-forward-row {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.1);
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

  .port-forward-row {
    padding: 10px;
    border-radius: 10px;
  }

  .port-forward-label {
    font-size: 11px;
  }
}

/* QR 扫描区域 */
.qr-scanner-area {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qr-reader-box {
  width: 300px;
  border: 2px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
}

.qr-reader-box video {
  width: 100% !important;
  height: auto !important;
}

.qr-scan-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  text-align: center;
}

/* 分享配置二维码 */
.share-qr-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 16px 8px 16px;
}

.share-qr-img {
  width: 280px;
  height: 280px;
  border: 2px solid var(--color-border);
  border-radius: 12px;
}

.share-qr-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
  text-align: center;
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
  font-weight: 600;
  color: var(--color-text);
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

.var-select-dropdown .peer-sub-uri {
  font-size: 12px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.var-select-dropdown .peer-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.var-select-dropdown .peer-tag {
  font-size: 11px;
  padding: 2px 8px;
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

/* ========== 更多菜单弹出层 ========== */
.more-menu {
  min-width: 170px;
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: transparent !important;
  border-left: 1px solid transparent;
  border-right: 1px solid transparent;
  border-image: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.5), transparent) 1;
}

.more-menu .var-button {
  display: inline-flex !important;
  justify-content: flex-start;
  padding: 10px 14px;
  font-size: 14px;
  border-radius: 10px;
  gap: 98px;
  color: var(--color-on-surface);
  min-height: 44px;
  background: transparent !important;
}

.more-menu .var-button:hover {
  background: rgba(128, 128, 128, 0.15) !important;
}

.more-menu .menu-icon {
  width: 24px;
  height: 24px;
  margin-right: 12px;
  flex-shrink: 0;
}

.more-menu .menu-divider {
  margin: 4px 0;
}

.more-menu .delete-btn {
  color: var(--color-danger) !important;
}

/* 更多菜单弹出层毛玻璃 */
.more-menu-popover,
.more-menu-popover .var-popover__content {
  background: rgba(var(--color-surface-container-rgb, 226, 236, 250), 0.25) !important;
  backdrop-filter: blur(24px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(24px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.25) !important;
  border-radius: 14px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
}

html.dark .more-menu-popover,
html.dark .more-menu-popover .var-popover__content {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.05) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
}
</style>