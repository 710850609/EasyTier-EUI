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

    <template v-else>
      <var-paper class="toolbar" :elevation="2" v-if="!fastSettingMode">
        <!-- 桌面端布局 -->
        <div class="toolbar-row toolbar-desktop">
          <div class="toolbar-group toolbar-main">
            <var-select
              class="config-switcher"
              v-model="selectedConfig"
              :placeholder="$t('config.selectConfig')"
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
              <var-button size="small" type="primary" @click="showCreateDialog = true; showMode = 1;" v-if="showMode === 0">{{ $t('config.add') }}</var-button>
              <var-button size="small" type="primary" @click="startEditName" :loading="isRenaming" v-if="showMode === 0">{{ $t('config.rename') }}</var-button>
              <var-button type="primary" size="small" @click="showShareConfigType = true" v-if="showMode === 0">{{ $t('config.shareNetwork') }}</var-button>
              <var-button size="small" type="danger" @click="showDeleteDialog = true" :loading="isDeletingConfig" v-if="showMode === 0">{{ $t('config.delete') }}</var-button>
              <label class="toggle-item" v-if="showMode === 0">
                <var-loading v-if="changingAutostart" size="small" />
                <label class="switch-wrapper" v-if="!changingAutostart">
                  <input type="checkbox" :checked="currentConfigAutostart" @change="(e) => handleSwitchChange(currentConfigData, 'autostart', e.target.checked)" />
                  <span class="switch-slider"></span>
                </label>
              </label>
              <span class="toggle-label" v-if="showMode === 0">{{ $t('config.autostart') }}</span>
            </div>
          </div>
          <var-divider class="toolbar-divider" />
          <div class="toolbar-group toolbar-status" v-if="selectedConfig">
            <div class="toolbar-toggles">
              <div class="toggle-item">
                <var-button size="small" type="danger" @click="exitAddMode" :loading="isDeletingConfig" v-if="showMode !== 0">{{ $t('config.exitAdd') }}</var-button>
                <var-button type="primary" size="small" @click="saveConfig" auto-loading>{{ $t('config.saveConfig') }}</var-button>
                <var-button type="primary" size="small" @click="openCodePage" auto-loading v-if="showMode === 0">{{ $t('config.editFile') }}</var-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 移动端布局 -->
        <div class="toolbar-mobile">
          <div class="toolbar-mobile-top">
            <var-select
              class="config-switcher"
              v-model="selectedConfig"
              :placeholder="$t('config.selectConfig')"
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
            <div class="toolbar-mobile-actions" v-if="selectedConfig">
              <label class="toggle-item" v-if="showMode === 0">
                <var-loading v-if="changingAutostart" size="small" />
                <label class="switch-wrapper" v-if="!changingAutostart">
                  <input type="checkbox" :checked="currentConfigAutostart" @change="(e) => handleSwitchChange(currentConfigData, 'autostart', e.target.checked)" />
                  <span class="switch-slider"></span>
                </label>
              </label>
              <span class="toggle-label" v-if="showMode === 0">{{ $t('config.autostart') }}</span>
              <var-button variant="outlined" size="small" type="danger" @click="exitAddMode" :loading="isDeletingConfig" v-if="showMode !== 0">
                <var-icon name="close" :size="16" />
                {{ $t('config.exitAdd') }}
              </var-button>
              <var-button type="primary" size="small" @click="saveConfig" auto-loading>{{ $t('config.save') }}</var-button>
              <var-button size="small" icon round text @click="toggleToolbarMore" v-if="showMode === 0">
                <var-icon :name="toolbarMoreOpen.length ? 'menu-open' : 'menu'" :size="20" />
              </var-button>
            </div>
          </div>
          <Transition name="panel">
          <div class="toolbar-more-panel" v-if="toolbarMoreOpen.length && selectedConfig">
            <div class="toolbar-more-content">
              <div class="toolbar-more-row">
                <var-button variant="outlined" size="small" type="primary" @click="showCreateDialog = true; showMode = 1;toggleToolbarMore()" v-if="showMode === 0">
                  {{ $t('config.add') }}
                </var-button>
                <var-button variant="outlined" size="small" type="primary" @click="startEditName();toggleToolbarMore()" :loading="isRenaming" v-if="showMode === 0">
                  <var-icon name="pencil-outline" :size="16" />
                  {{ $t('config.rename') }}
                </var-button>
                <var-button variant="outlined" size="small" type="danger" @click="showDeleteDialog = true;toggleToolbarMore()" :loading="isDeletingConfig" v-if="showMode === 0">
                  <var-icon name="delete-outline" :size="16" />
                  {{ $t('config.delete') }}
                </var-button>
              </div>
              <div class="toolbar-more-row">
                <var-button variant="outlined" size="small" type="primary" @click="showShareConfigType = true;toggleToolbarMore()" v-if="showMode === 0">
                  <var-icon name="share-variant-outline" :size="16" />
                  {{ $t('config.shareNetwork') }}
                </var-button>
                <var-button variant="outlined" size="small" type="primary" @click="openCodePage();toggleToolbarMore()" auto-loading v-if="showMode === 0">
                  <var-icon name="file-edit-outline" :size="16" />
                  {{ $t('config.editFile') }}
                </var-button>
              </div>
            </div>
          </div>
        </Transition>
        </div>
      </var-paper>

      <div class="toolbar-more-backdrop" v-show="toolbarMoreOpen.length" @click="toolbarMoreOpen = ''"></div>

      <div class="content-area" v-if="selectedConfig || fastSettingMode">
        <var-form ref="form">
          <var-paper class="config-section merged-section" :elevation="2">
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

            <var-skeleton :loading="isLoadingConfig">
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
                  :placeholder="$t('config.nodeCountHint', { count: config.peer.length })"
                  :chip="true"
                  class="peer-select"
                >
                  <template #default>
                    <div class="peer-custom-input">
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
                            <div class="peer-sub-uri">{{ peer.uri }}</div>
                            <div class="peer-tags">
                              <span class="peer-tag latency-tag" :class="peer.latency < 500 ? (peer.latency < 100 ? 'latency-good' : 'latency-normal') : 'latency-bad'"  
                                v-if="peer.latency > 0">
                                {{ peer.latency }}ms
                              </span>
                              <span class="peer-tag relay-tag" v-if="peer.relay == 1">{{ $t('config.relay') }}</span>
                              <span class="peer-tag dynamic-tag" v-if="peer.dynamic">{{ $t('config.dynamic') }}</span>
                              <span style="font-size: 12px; color: var(--color-primary);">{{ peer.hostname || '' }}</span>
                            </div>
                          </div>
                        </template>
                        <template #extra>
                          <div class="status-dot" v-if="peer.status in [0, 1]" :class="peer.status == 1 ? 'status-online' : 'status-offline'"></div>
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
                    <span>{{ $t('config.fastSetupHintFooter') }}</span>
                    <var-icon name="help-circle-outline" size="12pt" @click="showPublicPeerTip = true" class="help-icon" />
                  </p>
                  <p>
                    <span>{{ $t('config.fastSetupReconfigHint') }}</span>
                    <var-button type="primary" size="mini" @click="fastSettingMode = false">{{ $t('config.normalAdd') }}</var-button>
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
                  <span class="section-title">{{ $t('config.advancedSettings') }}</span>
                </div>
              </template>
              <var-skeleton :loading="isLoadingConfig">
                <div class="flags-content">
                  <div class="feature-section">
                    <div class="section-subtitle">{{ $t('config.featureToggles') }}</div>
                    <div class="feature-grid">
                      <div
                        v-for="feature in featureSwitches"
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
                          <div class="tooltip-multiline" v-html="$t('config.tunMtuHint')">
                          </div>
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
                      >
                        <var-option v-for="(e, index) in encryptionAlgorithmList" :key="index" :label="e" :value="e" />
                      </var-select>
                    </div>
                  </div>

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
                  </div>

                  <div class="input-row">
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
                      :placeholder="$t('config.customListenerPlaceholder')"
                      variant="outlined"
                      :chip="true"
                      size="small"
                    >
                      <var-cell>
                        <template #icon>
                          <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                        </template>
                        <template #description>
                          <var-input :placeholder="$t('config.customListenerPlaceholder')" size="mini" v-model="customListener" blur-color="var(--color-primary)" />
                        </template>
                        <template #extra>
                          <var-button type="primary" size="small" @click="addListener">{{ $t('config.addListener') }}</var-button>
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

          <!-- 代理与转发 -->
          <var-paper v-if="!fastSettingMode" :elevation="3" class="forward-section-paper">
            <var-collapse v-model="forwardOpen" :accordion="true" class="forward-section-inner">
              <var-collapse-item name="forward">
                <template #title>
                  <div class="collapse-title">
                    <svg-icon type="mdi" :path="mdiRouterNetwork" width="24" height="24" color="var(--color-primary)" />
                    <span class="section-title">{{ $t('config.proxyForward') }}</span>
                  </div>
                </template>
                <var-skeleton :loading="isLoadingConfig">
                  <div class="forward-content">
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
                        >
                          <var-cell>
                            <template #icon>
                              <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                            </template>
                            <template #description>
                              <var-input :placeholder="$t('config.customExitNodePlaceholder')" size="mini" v-model="customExitNode" blur-color="var(--color-primary)" />
                            </template>
                            <template #extra>
                              <var-button type="primary" size="small" @click="addExitNode">{{ $t('config.addExitNode') }}</var-button>
                            </template>
                          </var-cell>
                          <var-option v-for="(e, index) in config.exit_nodes" :key="index" :label="e" :value="e" />
                        </var-select>
                      </div>
                    </div>
                    <div class="input-row">
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
                      <div class="input-section">
                        <div class="section-subtitle">{{ $t('config.subnetProxy') }}</div>
                        <var-select
                          v-model="config.proxy_network"
                          multiple
                          :placeholder="$t('config.subnetProxyPlaceholder')"
                          variant="outlined"
                          :chip="true"
                          size="small"
                        >
                          <var-cell>
                            <template #icon>
                              <svg-icon type="mdi" :path="mdilPencil" color="var(--color-primary)" />
                            </template>
                            <template #description>
                              <var-input :placeholder="$t('config.customProxyNetworkPlaceholder')" size="mini" v-model="customProxyNetwork" blur-color="var(--color-primary)" />
                            </template>
                            <template #extra>
                              <var-button type="primary" size="small" @click="addProxyNetwork">{{ $t('config.addProxyNetwork') }}</var-button>
                            </template>
                          </var-cell>
                          <var-option v-for="(e, index) in proxyNetworkOptions" :key="index" :label="e" :value="e" />
                        </var-select>
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
                          <div class="tooltip-multiline" v-html="$t('config.portForwardHint')">
                          </div>
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

    <var-dialog v-model:show="showCreateDialog" @before-close="beforeCloseCreateDilog"
      :confirm-button-text="$t('common.confirm')" :cancel-button-text="$t('common.cancel')">
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
    </var-dialog>

    <var-dialog v-model:show="showShareConfigType" :title="$t('config.selectShareType')"
      :confirm-button-text="$t('config.downloadFile')"  @confirm="downloadConfig" 
      :cancel-button-text="$t('config.copyClipboard')" @cancel="copyConfig">
    </var-dialog>

    <var-dialog v-model:show="showDeleteDialog" :title="$t('config.confirmDelete', { name: currentConfigData.name })"
      :confirm-button-text="$t('config.confirm')"  @confirm="deleteCurrentConfig" 
      :cancel-button-text="$t('config.cancel')" @cancel="showDeleteDialog = false">
    </var-dialog>

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
import { validateIP, validateIPPort } from '../utils/validate.js'
import { ref, computed, inject, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import toast from '../components/toast.js'
import { api } from '../utils/api.js'
import CodeEditor from '../components/CodeEditor.vue'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiEye, mdiEyeOff, mdiHomeEdit, mdiShieldEdit, mdiCircle, mdiRouterNetwork } from '@mdi/js'
import { mdilPencil, mdilAccount, mdilLock } from '@mdi/light-js'


// 显示模式： 0 修改 1 快速新增 2 普通新增
const { t } = useI18n()
const showMode = ref(0)
const fastSettingMode = inject('fastSettingMode', ref(false))
const publicPeerOptions = ref([])
const customPeer = ref('')
const customProxyNetwork = ref('')
const customListener = ref('')
const flagsOpen = ref(['flags'])
const forwardOpen = ref(['forward'])
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
const toolbarMoreOpen = ref([])
const toggleToolbarMore = () => {
  toolbarMoreOpen.value = toolbarMoreOpen.value.length ? [] : ['more']
}
const lanIps = ref([])

const configList = ref([])
const selectedConfig = ref('')
const showCreateDialog = ref(false)
const showRenameDialog = ref(false)
const newConfigName = ref('')
const editNameValue = ref('')
const customExitNode = ref('')
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
  socks5_proxy: null,
  port_forward: [],
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
  { key: 'latency_first', label: 'config.flags.latency_first.label', tooltip: 'config.flags.latency_first.tooltip' },
  { key: 'multi_thread', label: 'config.flags.multi_thread.label', tooltip: 'config.flags.multi_thread.tooltip' },
  { key: 'private_mode', label: 'config.flags.private_mode.label', tooltip: 'config.flags.private_mode.tooltip' },
  { key: 'enable_kcp_proxy', label: 'config.flags.enable_kcp_proxy.label', tooltip: 'config.flags.enable_kcp_proxy.tooltip' },
  { key: 'disable_kcp_input', label: 'config.flags.disable_kcp_input.label', tooltip: 'config.flags.disable_kcp_input.tooltip' },
  { key: 'enable_quic_proxy', label: 'config.flags.enable_quic_proxy.label', tooltip: 'config.flags.enable_quic_proxy.tooltip' },
  { key: 'disable_quic_input', label: 'config.flags.disable_quic_input.label', tooltip: 'config.flags.disable_quic_input.tooltip' },
  { key: 'p2p_only', label: 'config.flags.p2p_only.label', tooltip: 'config.flags.p2p_only.tooltip' },
  { key: 'disable_p2p', label: 'config.flags.disable_p2p.label', tooltip: 'config.flags.disable_p2p.tooltip' },
  { key: 'lazy_p2p', label: 'config.flags.lazy_p2p.label', tooltip: 'config.flags.lazy_p2p.tooltip' },
  { key: 'need_p2p', label: 'config.flags.need_p2p.label', tooltip: 'config.flags.need_p2p.tooltip' },
  { key: 'disable_tcp_hole_punching', label: 'config.flags.disable_tcp_hole_punching.label', tooltip: 'config.flags.disable_tcp_hole_punching.tooltip' },
  { key: 'disable_udp_hole_punching', label: 'config.flags.disable_udp_hole_punching.label', tooltip: 'config.flags.disable_udp_hole_punching.tooltip' },
  { key: 'disable_sym_hole_punching', label: 'config.flags.disable_sym_hole_punching.label', tooltip: 'config.flags.disable_sym_hole_punching.tooltip' },
  { key: 'disable_upnp', label: 'config.flags.disable_upnp.label', tooltip: 'config.flags.disable_upnp.tooltip' },
  { key: 'use_smoltcp', label: 'config.flags.use_smoltcp.label', tooltip: 'config.flags.use_smoltcp.tooltip' },
  { key: 'proxy_forward_by_system', label: 'config.flags.proxy_forward_by_system.label', tooltip: 'config.flags.proxy_forward_by_system.tooltip' },
  { key: 'enable_exit_node', label: 'config.flags.enable_exit_node.label', tooltip: 'config.flags.enable_exit_node.tooltip' },
  { key: 'relay_all_peer_rpc', label: 'config.flags.relay_all_peer_rpc.label', tooltip: 'config.flags.relay_all_peer_rpc.tooltip' },
  { key: 'enable_encryption', label: 'config.flags.enable_encryption.label', tooltip: 'config.flags.enable_encryption.tooltip' },
  { key: 'enable_ipv6', label: 'config.flags.enable_ipv6.label', tooltip: 'config.flags.enable_ipv6.tooltip' },
  { key: 'no_tun', label: 'config.flags.no_tun.label', tooltip: 'config.flags.no_tun.tooltip' },
  { key: 'accept_dns', label: 'config.flags.accept_dns.label', tooltip: 'config.flags.accept_dns.tooltip' },
  { key: 'bind_device', label: 'config.flags.bind_device.label', tooltip: 'config.flags.bind_device.tooltip' },
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
      toast.error(t('config.validationFailed'))
      return
    }
    const pfError = validatePortForward()
    if (pfError) {
      reject();
      toast.error(pfError)
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
    data.peer = data.peer.map(e => ({ uri: e }))
    data.proxy_network = data.proxy_network.map(e => ({ cidr: e }))
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
    api.configs.save(data).then(async res => {
      toast.success(t('config.saveSuccess'))
      if (fastSettingMode.value) {
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
        exitAddMode()
      }
    }).catch(e => {
      toast.error(t('config.saveFailed', { error: e.message }))
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

const loadConfig = (profile) => {
  isLoadingConfig.value = true
  return api.configs.get(profile).then(data => {
    flagsOpen.value = ['']
    forwardOpen.value = ['']
    const json = data.data
    json.peer = (json.peer || []).map(e => e.uri)
    json.proxy_network = (json.proxy_network || []).map(e => e.cidr)
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
    config.value = {
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

const beforeCloseCreateDilog = (action, done) => {
  if (action === 'confirm') {
    if (confirmCreateConfig()) {
      done()
    }
  } else {
    exitAddMode()
    done()
  }
}

const confirmCreateConfig = () => {
  if (!newConfigName.value.trim()) {
    toast.warning(t('config.profileNameRequired'))
    return false
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

.toolbar-desktop {
  display: flex;
}

.toolbar-mobile {
  display: none;
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
  background: rgba(var(--color-surface-container-rgb, 221, 231, 245), 0.08) !important;
}

html.dark .merged-section {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.1) !important;
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
  background: rgba(var(--color-surface-container-rgb, 221, 231, 245), 0.08) !important;
}

html.dark .flags-section-paper {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.1) !important;
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

/* ===== 代理与转发样式 ===== */
.forward-section-paper {
  margin-top: 16px;
  border-radius: 16px;
  overflow: hidden;
  color: var(--color-text);
  background: rgba(var(--color-surface-container-rgb, 221, 231, 245), 0.08) !important;
}

html.dark .forward-section-paper {
  background: rgba(var(--color-surface-container-rgb, 51, 65, 85), 0.1) !important;
}

:deep(.forward-section-inner .var-collapse-item) {
  border-radius: 12px;
  overflow: hidden;
  color: var(--color-text);
  background: transparent !important;
}

:deep(.forward-section-inner .var-collapse-item__header) {
  padding: 12px 16px;
  color: var(--color-text);
}

:deep(.forward-section-inner .var-divider) {
  margin: 8px 0;
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

.port-forward-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
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
  background: rgba(var(--color-surface-container-rgb, 221, 231, 245), 0.4) !important;
}

.help-content tr {
  --table-tbody-td-text-color: var(--color-text) !important;
  background: rgba(var(--color-surface-container-rgb, 221, 231, 245), 0.1) !important;
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
    height: calc(100vh - 64px);
    overflow: hidden;
  }

  .toolbar {
    flex-shrink: 0;
    margin: 16px 12px 4px;
    padding: 12px;
    border-radius: 10px;
    position: relative;
    z-index: 10;
    overflow: visible !important;
  }

  .toolbar-desktop {
    display: none;
  }

  .toolbar-mobile {
    display: flex;
    flex-direction: column;
  }

  .toolbar-mobile-top {
    display: flex;
    align-items: center;
    gap: 4px;
    width: 100%;
  }

  .toolbar-mobile-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-left: auto;
    min-width: 0;
  }

  .toolbar-mobile-actions .toggle-item {
    gap: 3px;
  }

  .toolbar-mobile-actions .toggle-label {
    font-size: 11px;
  }

  .toolbar-more-panel {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    margin-top: 6px;
    background: rgba(var(--color-surface-container-rgb, 255, 255, 255), 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 12px;
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    padding: 12px 14px 14px;
    z-index: 11;
    border: none;
    overflow: hidden;
  }

  .toolbar-more-panel::after {
    content: '';
    position: absolute;
    top: 0;
    left: 20%;
    right: 20%;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.35),
      transparent
    );
    pointer-events: none;
    z-index: 1;
  }

  .toolbar-more-content {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .toolbar-more-row {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
  }

  .toolbar-more-row .var-button {
    flex: 1;
    min-width: 0;
    font-size: 14px;
    justify-content: center;
    border-radius: 10px;
    padding: 10px 12px;
  }

  .panel-enter-active,
  .panel-leave-active {
    transition: all 0.25s ease;
  }
  .panel-enter-from,
  .panel-leave-to {
    opacity: 0;
    transform: translateY(-6px);
  }

  .toolbar-divider {
    display: flex;
  }

  .toolbar-more-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(
      ellipse 70% 55% at 50% 50%,
      rgba(0, 0, 0, 0.3) 0%,
      transparent 70%
    );
    backdrop-filter: blur(2px);
    -webkit-backdrop-filter: blur(2px);
    z-index: 9;
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

  .forward-section-paper {
    margin-top: 12px;
  }

  .port-forward-row {
    grid-template-columns: 1fr;
    gap: 4px;
    padding: 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: rgba(var(--color-surface-container-rgb, 221, 231, 245), 0.08);
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
</style>