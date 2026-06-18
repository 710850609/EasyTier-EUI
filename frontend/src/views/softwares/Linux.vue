<template>
  <div class="platform-page">
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            易组网
            <var-badge type="primary">
               <template #value>新手推荐</template>
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
        <var-divider />
        <var-space class="eui-download-btn-group" :size="[20, 20]" justify="center">
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'x86_64')" :loading="downloadingKey === 'linux-x86_64'">
            <template #default>
              <var-icon name="download"/>
              x86_64版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'aarch64')" :loading="downloadingKey === 'linux-aarch64'">
            <template #default>
              <var-icon name="download"/>
              arm64版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'armv7')" :loading="downloadingKey === 'linux-armv7'">
            <template #default>
              <var-icon name="download"/>
              armv7版
            </template>
          </var-button>
          <var-button type="primary" size="normal" block @click="downloadEasyTierEui('linux', 'riscv64')" :loading="downloadingKey === 'linux-riscv64'">
            <template #default>
              <var-icon name="download"/>
              riscv64版
            </template>
          </var-button>
        </var-space>
        <div v-if="progress" class="download-progress">
          <var-progress :value="progress.current_progress" :track="true" />
          <p class="progress-desc">{{ progress.description }}</p>
        </div>
        <var-cell>
          <p style="margin-bottom: 12px;">使用简介</p>
        </var-cell>
        <div class="eui-opt-desc-table-container">
          <var-table class="eui-opt-desc-table">
            <thead>
              <tr>
                <th align="center">操作</th>
                <th align="center">有桌面环境</th>
                <th align="center">无桌面环境</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td align="center">启动命令</td>
                <td colspan="2" align="center"><code>./start.sh</code></td>
              </tr>
              <tr>
                <td align="center">停止命令</td>
                <td colspan="2" align="center"><code>./stop.sh</code></td>
              </tr>
              <tr>
                <td align="center">启动操作</td>
                <td align="center">双击<code>EasyTier-EUI</code></td>
                <td align="center">❌不支持</td>
              </tr>
              <tr>
                <td align="center">停止操作</td>
                <td colspan="2" align="center">点击【设置】界面最底部的“关闭易组网”按钮</td>
              </tr>
            </tbody>
          </var-table>
        </div>
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
import { useAsyncDownload } from '../../utils/downloadProgress.js'

const { startDownload, progress, downloadingKey } = useAsyncDownload(
  api.etEui.startDownload,
  api.etEui.getDownloadProgress,
  api.etEui.getDownloadResultUrl,
)

const download = (type, arch, prerelease) => {
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
  if (downloadingKey.value) {
    toast.warning(`当前 ${downloadingKey.value} 正在下载中，请稍后`)
    return
  }
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
  startDownload(`${platform}-${arch}`, { platform, arch, profile }).catch(err => {
    console.error('下载失败:', err)
  })
}

const handleConfigConfirm = async () => {
  if (selectedConfig.value) {
    startDownload(`${selectedPlatform.value}-${selectedArch.value}`, { platform: selectedPlatform.value, arch: selectedArch.value, profile: selectedConfig.value || '' }).catch(err => {
      console.error('下载失败:', err)
    })
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
  background: var(--color-surface-container) !important;
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
  background: var(--color-surface-container-high) !important;
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

/* 操作说明表格样式 */
.eui-opt-desc-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
}

.eui-opt-desc-table :deep(th) {
  background: var(--color-surface-container);
  color: var(--color-on-surface-container);
  font-weight: 600;
  padding: 14px 16px;
  text-align: center;
  border-bottom: 2px solid var(--color-outline);
  border-left: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(th:first-child) {
  border-left: none;
}

.eui-opt-desc-table :deep(th:last-child) {
  border-right: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(td) {
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  border-left: 1px solid var(--color-outline-variant);
  background: var(--color-surface);
  color: var(--color-on-surface);
  text-align: center;
}

.eui-opt-desc-table :deep(td:first-child) {
  border-left: none;
}

.eui-opt-desc-table :deep(td:last-child) {
  border-right: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(tr:last-child td) {
  border-bottom: none;
}

.eui-opt-desc-table :deep(tr:hover td) {
  background: var(--color-surface-container-low);
}

.eui-opt-desc-table :deep(code) {
  background: rgba(var(--color-primary-rgb), 0.18);
  color: var(--color-primary);
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
}

/* 移动端响应式优化 */
@media (max-width: 768px) {
  .eui-opt-desc-table-container {
    overflow-x: auto;
    border-radius: 12px;
  }

  .eui-opt-desc-table {
    min-width: 500px;
    font-size: 12px;
  }

  .eui-opt-desc-table :deep(th),
  .eui-opt-desc-table :deep(td) {
    padding: 8px 10px;
    font-size: 13px;
  }

  .eui-opt-desc-table :deep(code) {
    font-size: 12px;
    padding: 2px 6px;
  }

  /* 下载按钮移动端优化 */
  .eui-download-btn-group {
    display: grid !important;
    grid-template-columns: repeat(2, 120px) !important;
    gap: 12px !important;
    width: 100% !important;
  }

  .eui-download-btn-group :deep(.var-button) {
    width: 120px !important; 
  }
}

.download-progress {
  margin-top: 16px;
  text-align: center;
}

.progress-desc {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-on-surface-variant);
}
</style>