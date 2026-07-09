import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.js'
import zhTW from './zh-TW.js'
import enUS from './en-US.js'
import deDE from './de-DE.js'
import frFR from './fr-FR.js'
import jaJP from './ja-JP.js'
import { use as varletUse } from '@varlet/ui/es/locale'

const STORAGE_KEY = 'language'

const TITLES = {
  zh: '易组网',
  zhtw: '易組網',
  en: 'EasyTier-EUI',
  de: 'EasyTier-EUI',
  fr: 'EasyTier-EUI',
  ja: 'EasyTier-EUI'
}

const SUPPORTED_LANGS = ['zh', 'zhtw', 'en', 'de', 'fr', 'ja']

function getSavedLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && SUPPORTED_LANGS.includes(saved)) {
      return saved
    }
  } catch (e) {
    // localStorage 不可用时忽略
  }

  const browserLang = navigator.language || navigator.userLanguage || ''
  if (browserLang.startsWith('zh')) {
    // 区分简繁体
    if (browserLang.includes('TW') || browserLang.includes('HK') || browserLang.includes('Hant')) {
      return 'zhtw'
    }
    return 'zh'
  }
  if (browserLang.startsWith('en')) {
    return 'en'
  }
  if (browserLang.startsWith('de')) {
    return 'de'
  }
  if (browserLang.startsWith('fr')) {
    return 'fr'
  }
  if (browserLang.startsWith('ja')) {
    return 'ja'
  }
  return 'zh'
}

const VARLET_LOCALE_MAP = {
  zh: 'zh-CN',
  zhtw: 'zh-TW',
  en: 'en-US',
  de: 'en-US',
  fr: 'en-US',
  ja: 'ja-JP'
}

export function setLanguage(lang) {
  i18n.global.locale.value = lang
  document.title = TITLES[lang] || TITLES.zh
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch (e) {
    // localStorage 不可用时忽略
  }
  if (varletUse) {
    try {
      const varletLang = VARLET_LOCALE_MAP[lang] || 'en-US'
      varletUse(varletLang)
    } catch (e) {
      // Varlet UI locale 切换失败时忽略
    }
  }
}

export function getLanguage() {
  return i18n.global.locale.value
}

const i18n = createI18n({
  legacy: false,
  locale: getSavedLanguage(),
  fallbackLocale: 'zh',
  messages: {
    zh: zhCN,
    zhtw: zhTW,
    en: enUS,
    de: deDE,
    fr: frFR,
    ja: jaJP
  }
})

document.title = TITLES[i18n.global.locale.value] || TITLES.zh

export default i18n