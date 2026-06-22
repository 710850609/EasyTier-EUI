import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { VarletUIResolver } from 'unplugin-vue-components/resolvers'
import { createHtmlPlugin } from 'vite-plugin-html'

// 生产环境配置
const DEFAULT_BASE_URI = '/cgi/ThirdParty/EasyTier-EUI/index.cgi'
const fnosToken = 'k/8Qbvscxmlur9xYlceJUssSS7ho0AM7CN4r/qM6p9U='

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  const BASE = process.env.BASE_URI?.trim() || DEFAULT_BASE_URI?.trim()
  const API_BASE = BASE + '/api'
  return ({
    base: isProduction ? BASE : './',
    plugins: [
      vue(),
      // 自动导入 Vue 相关 API
      AutoImport({
        imports: [
          'vue'
        ],
        dts: 'src/auto-imports.d.ts'
      }),
      // 自动导入组件
      Components({
        resolvers: [VarletUIResolver()],
        dts: 'src/components.d.ts'
      }),
      // HTML 压缩
      createHtmlPlugin({
        minify: true,
        inject: {
          data: {}
        }
      })
    ],
    define: {
      // 注入 API 基础路径（统一使用生产路径）
      __API_BASE__: JSON.stringify(API_BASE)
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    build: {
      rollupOptions: {
        output: {
          // 代码分割：只分离第三方库，业务代码合并
          manualChunks: {
            // 第三方库单独打包（变化少，长期缓存）
            'vendor': ['vue', '@varlet/ui', '@varlet/touch-emulator']
          },
          // 其他所有代码自动合并到 index.js
          // 入口文件
          entryFileNames: 'assets/[name]-[hash].js',
          // chunk 文件（只有 vendor）
          chunkFileNames: 'assets/[name]-[hash].js',
          // CSS 文件
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.')
            const ext = info[info.length - 1]
            if (/\.(css)$/i.test(assetInfo.name)) {
              return 'assets/[name]-[hash][extname]'
            }
            return 'assets/[name]-[hash][extname]'
          }
        }
      },
      // 压缩配置
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,
          drop_debugger: true
        }
      },
      // CSS 代码分割
      cssCodeSplit: true
    },
    server: {
      port: 5173,
      host: "0.0.0.0",
      watch: {
        usePolling: true,
        interval: 1000
      },
      proxy: {
        '/cgi': {
          // target: 'http://192.168.220.3:5666',
          target: 'http://localhost:5666',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            proxy.on('proxyReq', (proxyReq, req, res) => {
              proxyReq.setHeader('authorization', `trim ${fnosToken}`)
              console.log('Proxying to:', options.target + req.url)
            })
            proxy.on('error', (err, req, res) => {
              console.log('Proxy error:', err)
            })
          },
        },
      },
    }
  })
})