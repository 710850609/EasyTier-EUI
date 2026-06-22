/**
 * 异步下载进度轮询通用工具
 * 用法:
 *   const { startDownload, progress, downloadingKey, downloading } = useAsyncDownload(
 *     async (params) => { ... },  // startDownloadFunc, 返回 { download_id }
 *     async ({download_id}) => { ... }, // queryProgressFunc, 返回进度
 *     (download_id) => { ... },  // buildResultUrl, 完成时打开
 *     3000  // poll interval
 *   )
 *   await startDownload(key, params)
 */
import { ref, computed, onUnmounted } from 'vue'
import toast from '../components/toast.js'

export function useAsyncDownload(startDownloadFunc, queryProgressFunc, buildResultUrl, pollInterval = 3000) {
  const downloadingKey = ref(null)
  const progress = ref(null)
  let pollTimer = null

  const downloading = computed(() => downloadingKey.value !== null)

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  onUnmounted(() => {
    if (pollTimer) {
      toast.info(`${downloadingKey.value} 将会继续后台下载`)
    }
    // stopPolling()
  })

  async function startDownload(key, params) {
    stopPolling()
    downloadingKey.value = key
    progress.value = { current_progress: 0, description: '正在初始化...', status: 0 }

    try {
      const resp = await startDownloadFunc(params)
      const downloadId = resp.data.download_id

      pollTimer = setInterval(async () => {
        try {
          const result = await queryProgressFunc({ download_id: downloadId })
          progress.value = result.data
          if (result.data.status !== 0) {
            stopPolling()
            downloadingKey.value = null
            if (result.data.status === 2) {
              toast.error(result.data.description || '下载失败')
              progress.value = null
            } else {
              toast.success(result.data.description + '\n开始下载')
              const downloadUrl = buildResultUrl({ download_id: downloadId })
              if (typeof window.pywebview !== 'undefined') {
                // pywebview 模式：委托给系统浏览器下载
                window.pywebview.api.window_open(downloadUrl)
              } else {
                // 浏览器模式：使用 <a> 标签点击触发下载，不会被 popup blocker 拦截
                const a = document.createElement('a')
                a.href = downloadUrl
                a.download = ''
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
              }
              progress.value = null
            }
          }
        } catch (e) {
          stopPolling()
          downloadingKey.value = null
          progress.value = null
          throw e
        }
      }, pollInterval)

    } catch (e) {
      downloadingKey.value = null
      progress.value = null
      throw e
    }
  }

  return { startDownload, progress, downloadingKey, downloading, stopPolling }
}