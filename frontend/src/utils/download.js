/**
 * 打开下载链接，Android 端优先使用系统下载器
 * @param {string} url - 下载链接
 */
export function openDownloadUrl(url) {
  if (window.AndroidBridge && window.AndroidBridge.downloadFile) {
    console.log(`AndroidBridge available, using downloadFile: ${url}`)
    window.AndroidBridge.downloadFile(url)
  } else {
    window.open(url, '_blank')
  }
}