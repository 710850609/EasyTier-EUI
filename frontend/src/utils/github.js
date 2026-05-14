import toast from "../components/toast.js"
import { ET_VERSION_LIST_KEY } from "../config/storage-keys.js"
import api from './api.js'

// const GITHUB_PROXY = 'https://ghfast.top'

export function getLatestVersionWithCache(repo, useCache = true) {
  return new Promise((resolve, reject) => {
    if (useCache) {
      const rawData = localStorage.getItem(ET_VERSION_LIST_KEY);
      if (rawData) {
        const json = JSON.parse(rawData)
        if (json.createTime && Date.now() - json.createTime < 1000 * 60 * 60) {
          resolve(json.data)
          return
        }
      }
    }
    getVersionList(repo)
      .then(versionList => {
        const data = { createTime: Date.now(), data: versionList }
        localStorage.setItem(ET_VERSION_LIST_KEY, JSON.stringify(data))
        resolve(versionList)
      })
      .catch(reject)
  })
}

export function getVersionList(repo) {  
  const fetchUrl = `https://api.github.com/repos/${repo}/releases`
  return fetch(fetchUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`获取 releases 失败: ${response.status}`)
      }
      return response.json()
    })
    .then(release => {
      const versionList = []
      release.forEach(e => {
        versionList.push({ version: e.tag_name, prerelease: e.prerelease })
      })
      return versionList
    })
    .catch(error => {
      toast.error(`${error.message} \n${fetchUrl}`)
      throw error
    })
}

export async function getGithubMirror() {
  const { data } = await api.settings.getGithubMirrors()
  return data.selected
}

/**
 * 从 GitHub releases 下载资源
 * @param {string} repo - GitHub 仓库，格式：owner/repo
 * @param {Function} matcher - 匹配资源的函数 (asset) => boolean
 * @param {boolean} prerelease - 是否下载预发布版本
 * @returns {Promise<string>} 下载 URL
 */
export function downloadFromGithub(repo, matcher, prerelease = false) {
  const fetchUrl = `https://api.github.com/repos/${repo}/releases`
  
  return fetch(fetchUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error(`获取 releases 失败: ${response.status}`)
      }
      return response.json()
    })
    .then(releases => {
      const release = releases.find(r => r.prerelease === prerelease)
      if (!release) {
        throw new Error('未找到匹配的 release')
      }
      return release
    })
    .then(release => {
      const asset = release.assets.find(matcher)
      if (!asset) {
        throw new Error('未找到匹配的资源文件')
      }
      return asset.browser_download_url
    })
    .then(async url => {
      const githubMirror = await getGithubMirror()
      if (githubMirror) {
        url = `${githubMirror}/${url}`
      }
      window.open(url, '_blank')
      return url
    })
    .catch(error => {
      toast.error(`${error.message} \n${fetchUrl}`)
      throw error
    })
}

/**
 * 下载 EasyTier GUI
 * @param {string} arch - 架构，如 'amd64.deb', 'arm64.deb', 'amd64.AppImage'
 * @param {boolean} prerelease - 是否下载预发布版本
 */
export async function downloadEasyTierGUI(arch, prerelease = false) {
  return downloadFromGithub(
    'EasyTier/EasyTier',
    (asset) => asset.name.startsWith('easytier-gui_') && asset.name.endsWith(`_${arch}`),
    prerelease
  )
}

/**
 * 下载 EasyTier APK
 * @param {boolean} prerelease - 是否下载预发布版本
 */
export async function downloadEasyTierApk(arch, prerelease = false) {
  return downloadFromGithub(
    'EasyTier/EasyTier',
    (asset) => asset.name === `app-${arch}-release.apk`,
    prerelease
  )
}
