import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.js'
import enUS from './en-US.js'
import { use as varletUse } from '@varlet/ui/es/locale'

const STORAGE_KEY = 'language'

const TITLES = {
  zh: '易组网',
  en: 'EasyTier-EUI'
}

function getSavedLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && (saved === 'zh' || saved === 'en')) {
      return saved
    }
  } catch (e) {
    // localStorage 不可用时忽略
  }

  const browserLang = navigator.language || navigator.userLanguage || ''
  if (browserLang.startsWith('zh')) {
    return 'zh'
  }
  if (browserLang.startsWith('en')) {
    return 'en'
  }
  return 'zh'
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
      varletUse(lang === 'zh' ? 'zh-CN' : 'en-US')
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
    en: enUS
  }
})

document.title = TITLES[i18n.global.locale.value] || TITLES.zh

export default i18n