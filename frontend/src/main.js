import { createApp } from 'vue'
import App from './App.vue'
import '@varlet/ui/es/style'
import '@varlet/touch-emulator'
import './styles/glass-effect.css'
// import { api } from './utils/api.js'

const originalAddEventListener = EventTarget.prototype.addEventListener
EventTarget.prototype.addEventListener = function (type, listener, options) {
  // @varlet/touch-emulator 在全局添加 touchstart / touchmove 事件监听器时，没有设置 { passive: true } ，浏览器认为这些监听器可能会调用 preventDefault() 阻塞滚动，因此发出警告。
  let opts = options
  if (type === 'touchstart' || type === 'touchmove') {
    if (opts === undefined || opts === null) {
      opts = { passive: true }
    } else if (typeof opts === 'boolean') {
      opts = { capture: opts, passive: true }
    } else if (typeof opts === 'object' && opts.passive === undefined) {
      opts = { ...opts, passive: true }
    }
  }
  originalAddEventListener.call(this, type, listener, opts)
}

// const updateTitle = () => {
//   api.settings.getEuiInfo()
//   .then(res => document.title = `易组网 ${res.data.build_version}`)
// }

const app = createApp(App)
app.mount('#app')
// updateTitle()