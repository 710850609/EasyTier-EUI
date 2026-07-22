package com.easytier.eui

import android.annotation.SuppressLint
import android.content.Intent
import android.content.res.Configuration
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.os.Build
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.SystemBarStyle
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowInsetsControllerCompat
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewFeature
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import com.easytier.jni.EasyTierManager
import kotlinx.coroutines.*
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.*

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "EasyTier"
    }

    private lateinit var webView: WebView
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var httpServerPort = 0
    private lateinit var crashLogFile: File
    private var easyTierManager: EasyTierManager? = null
    private var lastBackPressTime = 0L

    private fun log(level: String, msg: String) {
        val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()).format(Date())
        val line = "$ts [$level] $msg"
        Log.println(
            when (level) { "ERROR" -> Log.ERROR; "WARN" -> Log.WARN; else -> Log.DEBUG },
            TAG, msg
        )
        try {
            crashLogFile.appendText(line + "\n")
        } catch (_: Exception) {}
    }

    private fun logError(msg: String, t: Throwable? = null) {
        log("ERROR", msg)
        if (t != null) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            try { crashLogFile.appendText(sw.toString() + "\n") } catch (_: Exception) {}
            Log.e(TAG, msg, t)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        crashLogFile = File(getExternalFilesDir(null), "easytier_crash.log")
        crashLogFile.parentFile?.mkdirs()

        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()).format(Date())
            val sw = StringWriter()
            sw.write("$ts [FATAL] Uncaught exception in thread ${thread.name}\n")
            throwable.printStackTrace(PrintWriter(sw))
            try {
                crashLogFile.appendText(sw.toString() + "\n")
            } catch (_: Exception) {}
            Log.e(TAG, "Uncaught exception in thread ${thread.name}", throwable)
            throwable.printStackTrace()
        }

        log("INFO", "=== App started ===")
        log("INFO", "Log file: ${crashLogFile.absolutePath}")
        log("INFO", "FilesDir: ${filesDir.absolutePath}")
        log("INFO", "ExternalFilesDir: ${getExternalFilesDir(null)?.absolutePath}")

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                WebView.setDataDirectorySuffix(applicationContext.packageName)
            }
            enableEdgeToEdge(
                statusBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT),
                navigationBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT)
            )
            setContentView(R.layout.activity_main)
            webView = findViewById(R.id.webview)
            setupWebView()
            setupBackPress()

            scope.launch(Dispatchers.IO) {
                try {
                    startPythonBackend()
                } catch (e: Exception) {
                    logError("Python backend failed", e)
                    withContext(Dispatchers.Main) {
                        webView.loadData(
                            "<h2>Startup Error</h2><pre>${e.message}\n\n${e.stackTraceToString()}</pre>",
                            "text/html", "UTF-8"
                        )
                    }
                }
            }
        } catch (e: Exception) {
            logError("onCreate failed", e)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

            // 关闭 WebView 自带的暗黑渲染，由 JS 注入控制主题
            if (WebViewFeature.isFeatureSupported(WebViewFeature.ALGORITHMIC_DARKENING)) {
                WebSettingsCompat.setAlgorithmicDarkeningAllowed(settings, false)
            }
            // 设置 WebView 背景色匹配主题，避免启动闪白
            setBackgroundColor(getWebViewBackgroundColor())
            overScrollMode = android.view.View.OVER_SCROLL_NEVER

            webChromeClient = WebChromeClient()
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean = false
                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    injectDarkMode()
                }
            }

            addJavascriptInterface(AndroidBridge(), "AndroidBridge")
        }
    }

    private fun setupBackPress() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (System.currentTimeMillis() - lastBackPressTime < 2000) {
                    finish()
                } else {
                    lastBackPressTime = System.currentTimeMillis()
                    Toast.makeText(this@MainActivity, "再按一次退出", Toast.LENGTH_SHORT).show()
                }
            }
        })
    }

    private fun injectDarkMode() {
        val isDark = (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
        webView.evaluateJavascript("""
            (function() {
                if (${isDark}) {
                    document.documentElement.classList.add('dark');
                } else {
                    document.documentElement.classList.remove('dark');
                }
                document.documentElement.style.setProperty('--system-dark', '${if (isDark) "1" else "0"}');
            })();
        """.trimIndent(), null)
    }

    private suspend fun startPythonBackend() {
        log("INFO", "Starting Python backend...")

        try {
            System.loadLibrary("easytier_ffi")
            log("INFO", "libeasytier_ffi.so pre-loaded for Python ctypes")
        } catch (e: UnsatisfiedLinkError) {
            log("WARN", "libeasytier_ffi.so not found: ${e.message}")
        }

        log("INFO", "Copying frontend assets...")
        copyAssetDir("frontend", File(filesDir, "frontend"))

        if (!Python.isStarted()) {
            log("INFO", "Python not started, calling Python.start()...")
            Python.start(AndroidPlatform(this))
            log("INFO", "Python.start() succeeded")
        } else {
            log("INFO", "Python already started")
        }

        log("INFO", "Getting Python instance...")
        val python = Python.getInstance()
        log("INFO", "Python instance obtained")

        log("INFO", "Importing main_noui module...")
        val module = python.getModule("main_noui")
        log("INFO", "main_noui module imported successfully")

        log("INFO", "Calling start_android_server with data_dir=${filesDir.absolutePath}...")
        val externalDir = getExternalFilesDir(null)?.absolutePath ?: ""
        val result = module.callAttr("start_android_server", filesDir.absolutePath, externalDir)
        log("INFO", "start_android_server returned: $result, type=${result::class.java.simpleName}")

        val portPyObj = result.callAttr("get", "port")
        httpServerPort = portPyObj.toJava(Int::class.java) as Int
        log("INFO", "HTTP server port: $httpServerPort")

        withContext(Dispatchers.Main) {
            log("INFO", "Loading WebView...")
            loadWebView()
            easyTierManager = EasyTierManager(this@MainActivity, crashLogFile)
            easyTierManager?.startMonitoring()
            log("INFO", "VPN monitoring auto-started")
        }
    }

    private fun loadWebView() {
        val url = "http://127.0.0.1:$httpServerPort/cgi/ThirdParty/EasyTier-EUI/index.cgi"
        log("INFO", "Loading WebView from $url")
        webView.loadUrl(url)
    }

    private fun copyAssetDir(assetPath: String, targetDir: File) {
        val list = try { assets.list(assetPath) } catch (_: Exception) { null }
        if (list == null || list.isEmpty()) {
            try {
                targetDir.parentFile?.mkdirs()
                assets.open(assetPath).use { input ->
                    targetDir.outputStream().use { output -> input.copyTo(output) }
                }
            } catch (_: Exception) {}
            return
        }
        targetDir.mkdirs()
        for (name in list) {
            copyAssetDir("$assetPath/$name", File(targetDir, name))
        }
    }

    override fun onDestroy() {
        log("INFO", "onDestroy")
        easyTierManager?.stopMonitoring()
        scope.cancel()
        super.onDestroy()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == EasyTierManager.VPN_REQUEST_CODE) {
            log("INFO", "VPN authorization result: $resultCode")
            easyTierManager?.onVpnAuthorizationResult(resultCode)
        }
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        val isDark = (newConfig.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = !isDark
            isAppearanceLightNavigationBars = !isDark
        }
        webView.setBackgroundColor(getWebViewBackgroundColor())
        injectDarkMode()
    }

    private fun getWebViewBackgroundColor(): Int {
        return if ((resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES) {
            Color.parseColor("#121212")
        } else {
            Color.parseColor("#FFFFFF")
        }
    }

    inner class AndroidBridge {
        @JavascriptInterface
        fun getApiBaseUrl(): String = "http://127.0.0.1:$httpServerPort"

        @JavascriptInterface
        fun startVpn(): String {
            return try {
                if (easyTierManager == null) {
                    easyTierManager = EasyTierManager(this@MainActivity, crashLogFile)
                }
                easyTierManager?.startMonitoring()
                log("INFO", "VPN monitoring started via AndroidBridge")
                "{\"code\": 0}"
            } catch (e: Exception) {
                logError("startVpn failed", e)
                "{\"code\": -1, \"msg\": \"${e.message}\"}"
            }
        }

        @JavascriptInterface
        fun stopVpn(): String {
            return try {
                easyTierManager?.stopMonitoring()
                log("INFO", "VPN monitoring stopped via AndroidBridge")
                "{\"code\": 0}"
            } catch (e: Exception) {
                logError("stopVpn failed", e)
                "{\"code\": -1, \"msg\": \"${e.message}\"}"
            }
        }
    }
}