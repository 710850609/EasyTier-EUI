<template>
  <div class="platform-page">
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            易组网
            <var-badge type="primary">
               <template #value>预览</template>
            </var-badge>
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>
          <p>集成当前配置，解压启动后启动服务即可组网</p>
          <p>自建初始节点，请自行修改配置</p>
        </var-cell>
        <var-cell>
          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-EUI/releases" target="_blank"><img src="https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue&logo=github&label=稳定版" /></var-link>
        </var-cell>
      </div>
      <div>
        <var-divider />
        <var-space :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'x86_64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              x86_64版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'aarch64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              arm64版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'riscv64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              armv7版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'riscv64')" auto-loading>
            <template #default>
              <var-icon name="download"/>
              riscv64版
            </template>
          </var-button>
        </var-space>
      </div>
    </var-paper>

    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>EasyTier Linux GUI 版本</h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>安装应用，并导出飞牛上配置toml文件后。把toml配置文件导入到easytier中，并启动网络即可。</var-cell>
        <var-cell>
          其他使用说明，请访问 
          <var-link type="primary" href="https://easytier.cn/" target="_blank" underline="none">
            EasyTier官网
          </var-link>
        </var-cell>
        <var-space :size="[20, 20]" justify="center">
          <var-cell>
            <var-link type="primary" underline="none" href="https://github.com/EasyTier/EasyTier/releases" target="_blank">
              <img src="https://img.shields.io/github/v/tag/EasyTier/EasyTier?color=blue&logo=github&label=最新版" />
            </var-link>
          </var-cell>
          <var-cell>
            <var-link type="primary" underline="none" href="https://github.com/EasyTier/EasyTier/releases" target="_blank">
              <img src="https://img.shields.io/github/v/release/EasyTier/EasyTier?color=blue&logo=github&label=稳定版" />
            </var-link>
          </var-cell>
        </var-space>
      </div>
      <var-divider />
      <!-- 下载卡片网格 -->
      <div class="download-grid">
        <!-- amd64 deb -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64 deb</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('deb', 'amd64', true)" auto-loading>
              <var-icon name="download"  />
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('deb', 'amd64', false)" auto-loading>
              <var-icon name="download"  />
              稳定版
            </var-button>
          </div>
        </var-paper>
        <!-- amd64 rpm -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64 rpm</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('rpm', 'x86_64', true)" auto-loading>
              <var-icon name="download"  />
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('rpm', 'x86_64', false)" auto-loading>
              <var-icon name="download"  />
              稳定版
            </var-button>
          </div>
        </var-paper>
        <!-- amd64 AppImage -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">x86_64 AppImage</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('AppImage', 'amd64', true)" auto-loading>
              <var-icon name="download"  />
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('AppImage', 'amd64', false)" auto-loading>
              <var-icon name="download"  />
              稳定版
            </var-button>
          </div>
        </var-paper>
        <!-- arm64 deb -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">arm64 deb</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('deb', 'arm64', true)" auto-loading>
              <var-icon name="download"  />
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('deb', 'arm64', false)" auto-loading>
              <var-icon name="download"  />
              稳定版
            </var-button>
          </div>
        </var-paper>
        <!-- aarch64 rpm -->
        <var-paper class="download-item" :elevation="3">
          <div class="item-header">
            <var-icon name="package" size="24" />
            <span class="item-title">arm64 rpm</span>
          </div>
          <div class="item-actions">
            <var-button type="primary" size="normal" @click="download('rpm', 'aarch64', true)" auto-loading>
              <var-icon name="download"  />
              最新版
            </var-button>
            <var-button type="primary" size="normal" @click="download('rpm', 'aarch64', false)" auto-loading>
              <var-icon name="download"  />
              稳定版
            </var-button>
          </div>
        </var-paper>
      </div>
    </var-paper>

    <var-dialog v-model:show="showConfigSelectDialog" title="选择内置配置" @confirm="handleConfigConfirm">
      <var-select
        v-model="selectedConfig"
        variant="outlined"
        class="config-select"
        size="small"
      >
        <var-option
          v-for="config in configFiles"
          :key="config.profile"
          :label="config.name"
          :value="config.profile"
        >
        </var-option>
      </var-select>
    </var-dialog>
  </div>
</template>

<script setup>
import toast from '../../components/toast.js'
import { api } from '../../utils/api.js'
// import { downloadEasyTierGUI } from '../../utils/github.js'

const download = (type, arch, prerelease) => {
  // return downloadEasyTierGUI(type, arch, prerelease)  
  return new Promise((resolve, reject) => {
    api.etApp.getDownloadUrl({type: type, arch: arch, prerelease: prerelease}).then((resp) => {
      window.open(resp.data, '_blank')
    }).finally(() => {
      resolve()
    })
  })
}


const showConfigSelectDialog = ref(false)
const configFiles = ref([])
const selectedConfig = ref(null)
const selectedPlatform = ref(null)
const selectedArch = ref(null)

const downloadEasyTierEui = async (platform, arch) => {
  const configs = await api.configs.listConfigFiles().then(resp => resp.data).catch(error => toast.error('获取配置失败:', error))
  let profile = ''
  selectedPlatform.value = platform
  selectedArch.value = arch
  if (configs.length === 0) {
    toast.info('当前系统无内置配置，将下载无配置版本')
  } else if (configs.length === 1) {
    profile =  configs[0].profile
  } else {
    configFiles.value = configs 
    selectedConfig.value = configs[0]?.profile
    showConfigSelectDialog.value = true
    return
  }
  const url = api.etEui.getDownloadEasyTierEuiUrl({platform: platform, 'arch': arch, profile: profile})
  window.open(url, '_blank')
}

const handleConfigConfirm = async () => {
  if (selectedConfig.value) {
    const url = api.etEui.getDownloadEasyTierEuiUrl({platform: selectedPlatform.value, 'arch': selectedArch.value, profile: selectedConfig.value || ''})
    window.open(url, '_blank')
  }
  selectedConfig.value = null
}
</script>

<style scoped>
.platform-page {
  padding: 16px;
  max-width: 900px;
  margin: 0 auto;
}

.download-card {
  padding: 24px;
  border-radius: 16px;
  margin-bottom: 20px;
  text-align: center;
}

.platform-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}

.platform-info h2 {
  margin: 0;
  color: var(--color-on-surface);
}

.platform-info p {
  margin: 4px 0 0;
  color: var(--color-on-surface-variant);
}

.version-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-outline-variant);
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

/* 下载卡片网格 */
.download-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-top: 16px;
}

.download-item {
  padding: 20px;
  border-radius: 12px;
  background: var(--color-surface-container) !important;
  display: flex;
  flex-direction: column;
}

.item-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0px;
  margin-bottom: 16px;
  color: var(--color-on-surface);
}

.item-title {
  font-weight: 600;
  font-size: 15px;
  text-align: center;
}

.item-actions {
  display: flex;
  gap: 12px;
  margin-top: auto;
}

.item-actions .var-button {
  flex: 1;
  min-width: 90px;
}
</style>