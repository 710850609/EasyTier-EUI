<template>
  <div class="platform-page">
    <!-- 易组网 Docker -->
    <var-paper class="download-card" :elevation="1">
      <div class="platform-header">
        <div class="platform-info">
          <h2>
            {{ $t('software.easyTierEui') }}
<!--            <var-badge type="primary">-->
<!--              <template #value>{{ $t('software.newbieRecommended') }}</template>-->
<!--            </var-badge>-->
          </h2>
        </div>
      </div>
      <div class="version-info">
        <var-cell>
          <p>{{ $t('software.dockerIntro') }}</p>
        </var-cell>
<!--        <var-cell>-->
<!--          <var-link type="primary" underline="none" href="https://github.com/710850609/EasyTier-EUI/releases" target="_blank"><img :src="stableBadgeUrl" /></var-link>-->
<!--        </var-cell>-->
        <var-divider />
        <var-cell>
          <p style="margin-bottom: 12px; font-weight: 600;">{{ $t('software.dockerStepTitle') }}</p>
        </var-cell>
        <!-- 步骤卡片 -->
        <div class="docker-steps">
          <var-paper class="step-item" :elevation="2">
            <div class="step-number">1</div>
            <div class="step-content">
              <p class="step-title">{{ $t('software.dockerStep1Title') }}</p>
              <p class="step-desc">{{ $t('software.dockerStep1Desc') }}</p>
              <code class="step-code">wget https://raw.githubusercontent.com/710850609/EasyTier-EUI/main/docker-compose.yml</code>
            </div>
          </var-paper>
          <var-paper class="step-item" :elevation="2">
            <div class="step-number">2</div>
            <div class="step-content">
              <p class="step-title">{{ $t('software.dockerStep2Title') }}</p>
              <p class="step-desc">{{ $t('software.dockerStep2Desc') }}</p>
              <code class="step-code">docker compose up -d</code>
            </div>
          </var-paper>
          <var-paper class="step-item" :elevation="2">
            <div class="step-number">3</div>
            <div class="step-content">
              <p class="step-title">{{ $t('software.dockerStep3Title') }}</p>
              <p class="step-desc">{{ $t('software.dockerStep3Desc') }}</p>
              <code class="step-code">http://{{ $t('software.dockerHostIP') }}:15666</code>
            </div>
          </var-paper>
        </div>
        <var-divider />
        <var-cell>
          <p style="margin-bottom: 8px; font-weight: 600;">{{ $t('software.dockerImageTags') }}</p>
          <p style="font-size: 13px; color: var(--color-on-surface-variant);">{{ $t('software.dockerImageTagsDesc') }}</p>
        </var-cell>
        <div class="eui-opt-desc-table-container">
          <var-table class="eui-opt-desc-table">
            <thead>
              <tr>
                <th align="center">{{ $t('software.dockerTag') }}</th>
                <th align="center">{{ $t('software.dockerArch') }}</th>
                <th align="center">{{ $t('software.dockerDesc') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td align="center"><code>latest</code></td>
                <td align="center">amd64 / arm64 / riscv64</td>
                <td align="center">{{ $t('software.dockerLatest') }}</td>
              </tr>
              <tr>
                <td align="center"><code>edge</code></td>
                <td align="center">amd64 / arm64 / riscv64</td>
                <td align="center">{{ $t('software.dockerEdge') }}</td>
              </tr>
              <tr>
                <td align="center"><code>dev</code></td>
                <td align="center">amd64 / arm64 / riscv64</td>
                <td align="center">{{ $t('software.dockerDev') }}</td>
              </tr>
            </tbody>
          </var-table>
        </div>
        <var-divider />
        <var-cell>
          <p style="margin-bottom: 8px; font-weight: 600;">{{ $t('software.dockerComposeTitle') }}</p>
          <p style="font-size: 13px; color: var(--color-on-surface-variant); margin-bottom: 12px;">{{ $t('software.dockerComposeDesc') }}</p>
        </var-cell>
        <div class="compose-code-block">
          <pre><code>services:
  easytier-eui:
    image: ghcr.io/710850609/easytier-eui:latest
    container_name: easytier-eui
    cap_add:
      - NET_ADMIN
      - NET_RAW
    devices:
      - /dev/net/tun:/dev/net/tun
    network_mode: host
    environment:
      - PORT=15666
      - TZ=Asia/Shanghai
    volumes:
      - /etc/machine-id:/etc/machine-id:ro
      - ./config:/app/config
      - ./logs:/app/logs</code></pre>
        </div>
      </div>
    </var-paper>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const stableBadgeUrl = computed(() => {
  const label = encodeURIComponent(t('software.stableLabel'))
  return `https://img.shields.io/github/v/release/710850609/EasyTier-EUI?color=blue&label=${label}`
})
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

.version-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-outline-variant);
  font-size: 14px;
  color: var(--color-on-surface-variant);
}

/* 步骤卡片 */
.docker-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 16px 0;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: var(--color-surface-container-high) !important;
  text-align: left;
}

.step-number {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-on-surface);
  margin: 0 0 4px 0;
}

.step-desc {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin: 0 0 8px 0;
}

.step-code {
  display: inline-block;
  background: rgba(var(--color-primary-rgb), 0.12);
  color: var(--color-primary);
  padding: 8px 14px;
  border-radius: 8px;
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 13px;
  word-break: break-all;
}

/* compose 代码块 */
.compose-code-block {
  background: var(--color-surface-container-high);
  border-radius: 12px;
  border: 1px solid var(--color-outline-variant);
  padding: 16px;
  text-align: left;
  overflow-x: auto;
}

.compose-code-block pre {
  margin: 0;
}

.compose-code-block code {
  font-family: 'Fira Code', 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-on-surface);
  white-space: pre;
}

/* 表格样式 */
.eui-opt-desc-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-surface-container-high);
  border: 1px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(th) {
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
  font-weight: 600;
  padding: 14px 16px;
  text-align: center;
  border-bottom: 2px solid var(--color-outline-variant);
}

.eui-opt-desc-table :deep(td) {
  padding: 14px 16px;
  border-bottom: 1px solid var(--color-outline-variant);
  background: var(--color-surface-container-high);
  color: var(--color-on-surface);
  text-align: center;
}

.eui-opt-desc-table :deep(tr:last-child td) {
  border-bottom: none;
}

.eui-opt-desc-table :deep(tr:hover td) {
  background: var(--color-surface-container);
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

/* 移动端 */
@media (max-width: 768px) {
  .eui-opt-desc-table-container {
    overflow-x: auto;
    border-radius: 12px;
  }

  .eui-opt-desc-table {
    min-width: 460px;
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

  .step-item {
    padding: 14px;
    gap: 12px;
  }

  .step-code {
    font-size: 11px;
    padding: 6px 10px;
  }

  .compose-code-block code {
    font-size: 10px;
  }
}
</style>