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
        val line = "$ts [$level] [MainActivity] $msg"
        Log.println(
            when (level) { "ERROR" -> Log.ERROR; "WARN" -> Log.WARN; else -> Log.DEBUG },
            TAG, msg
        )
        try {
            crashLogFile.appendText(line + "\r\n")
        } catch (_: Exception) {}
    }

    private fun logError(msg: String, t: Throwable? = null) {
        log("ERROR", msg)
        if (t != null) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()).format(Date())
            try { crashLogFile.appendText("$ts [ERROR] [MainActivity] ${sw}\r\n") } catch (_: Exception) {}
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
            sw.write("$ts [FATAL] [MainActivity] Uncaught exception in thread ${thread.name}\n")
            throwable.printStackTrace(PrintWriter(sw))
            try {
                crashLogFile.appendText(sw.toString() + "\r\n")
            } catch (_: Exception) {}
            Log.e(TAG, "Uncaught exception in thread ${thread.name}", throwable)
            throwable.printStackTrace()
        }

        log("INFO", "=== App started ===")
        log("INFO", "Log file: ${crashLogFile.absolutePath}")
        log("INFO", "FilesDir: ${filesDir.absolutePath}")
        log("INFO", "ExternalFilesDir: ${getExternalFilesDir(null)?.absolutePath}")

        try {
            log("INFO", "onCreate: setting up UI")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                try {
                    WebView.setDataDirectorySuffix(applicationContext.packageName)
                    log("INFO", "WebView.setDataDirectorySuffix ok")
                } catch (e: IllegalStateException) {
                    log("WARN", "WebView.setDataDirectorySuffix failed (already initialized): ${e.message}")
                }
            }
            enableEdgeToEdge(
                statusBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT),
                navigationBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT)
            )
            setContentView(R.layout.activity_main)
            log("INFO", "setContentView done, finding WebView")
            webView = findViewById(R.id.webview)
            log("INFO", "WebView found, calling setupWebView")
            setupWebView()
            log("INFO", "setupWebView done, calling setupBackPress")
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
            log("INFO", "onCreate: done")
        } catch (e: Exception) {
            logError("onCreate failed", e)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        try {
            log("INFO", "setupWebView: configuring WebView")
            webView.apply {
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.allowFileAccess = true
                settings.allowContentAccess = true
                settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

                if (WebViewFeature.isFeatureSupported(WebViewFeature.ALGORITHMIC_DARKENING)) {
                    WebSettingsCompat.setAlgorithmicDarkeningAllowed(settings, false)
                }
                setBackgroundColor(getWebViewBackgroundColor())
                overScrollMode = android.view.View.OVER_SCROLL_NEVER

                webChromeClient = WebChromeClient()
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean = false
                    override fun onPageFinished(view: WebView?, url: String?) {
                        super.onPageFinished(view, url)
                        log("INFO", "WebView page finished: $url")
                        injectDarkMode()
                    }
                    override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: android.webkit.WebResourceError?) {
                        log("ERROR", "WebView error: ${error?.description} for ${request?.url}")
                    }
                }

                addJavascriptInterface(AndroidBridge(), "AndroidBridge")
            }
            log("INFO", "setupWebView: done")
        } catch (e: Exception) {
            logError("setupWebView failed", e)
        }
    }

    private fun setupBackPress() {
        log("INFO", "setupBackPress: registering callback")
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
        try {
            val isDark = (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
            val js = """
                (function() {
                    if (${isDark}) {
                        document.documentElement.classList.add('dark');
                    } else {
                        document.documentElement.classList.remove('dark');
                    }
                    document.documentElement.style.setProperty('--system-dark', '${if (isDark) "1" else "0"}');
                })();
            """.trimIndent()
            webView.evaluateJavascript(js, null)
        } catch (e: Exception) {
            logError("injectDarkMode failed", e)
        }
    }

    private suspend fun startPythonBackend() {
        log("INFO", "Starting Python backend...")

        try {
            log("INFO", "Pre-loading libeasytier_ffi.so...")
            System.loadLibrary("easytier_ffi")
            log("INFO", "libeasytier_ffi.so pre-loaded for Python ctypes")
        } catch (e: UnsatisfiedLinkError) {
            log("WARN", "libeasytier_ffi.so not found: ${e.message}")
        } catch (e: Exception) {
            log("WARN", "libeasytier_ffi.so load failed: ${e.message}")
        }

        log("INFO", "Copying frontend assets...")
        copyAssetDir("frontend", File(filesDir, "frontend"))
        log("INFO", "Frontend assets copied")

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
        log("INFO", "start_android_server: externalDir=$externalDir")
        val result = module.callAttr("start_android_server", filesDir.absolutePath, externalDir)
        log("INFO", "start_android_server returned: $result, type=${result::class.java.simpleName}")

        val portPyObj = result.callAttr("get", "port")
        httpServerPort = portPyObj.toJava(Int::class.java) as Int
        log("INFO", "HTTP server port: $httpServerPort")

        withContext(Dispatchers.Main) {
            log("INFO", "Loading WebView...")
            loadWebView()
            log("INFO", "Creating EasyTierManager...")
            easyTierManager = EasyTierManager(this@MainActivity, crashLogFile)
            log("INFO", "EasyTierManager created, starting monitoring...")
            easyTierManager?.startMonitoring()
            log("INFO", "VPN monitoring auto-started")
        }
    }

    private fun loadWebView() {
        try {
            val url = "http://127.0.0.1:$httpServerPort/cgi/ThirdParty/EasyTier-EUI/index.cgi"
            log("INFO", "Loading WebView from $url")
            webView.loadUrl(url)
        } catch (e: Exception) {
            logError("loadWebView failed", e)
        }
    }

    private fun copyAssetDir(assetPath: String, targetDir: File) {
        try {
            val list = try { assets.list(assetPath) } catch (_: Exception) { null }
            if (list == null || list.isEmpty()) {
                try {
                    targetDir.parentFile?.mkdirs()
                    assets.open(assetPath).use { input ->
                        targetDir.outputStream().use { output -> input.copyTo(output) }
                    }
                } catch (e: Exception) {
                    log("WARN", "copyAssetDir: failed to copy $assetPath: ${e.message}")
                }
                return
            }
            targetDir.mkdirs()
            for (name in list) {
                copyAssetDir("$assetPath/$name", File(targetDir, name))
            }
        } catch (e: Exception) {
            log("WARN", "copyAssetDir: failed for $assetPath: ${e.message}")
        }
    }

    override fun finish() {
        val sw = StringWriter()
        Thread.currentThread().stackTrace.forEach { sw.write("  $it\r\n") }
        log("WARN", "finish() called! Stack trace:\r\n${sw}")
        super.finish()
    }

    override fun onDestroy() {
        log("INFO", "onDestroy: stopping monitoring and cancelling scope")
        try {
            easyTierManager?.stopMonitoring()
        } catch (e: Exception) {
            logError("onDestroy: stopMonitoring failed", e)
        }
        scope.cancel()
        super.onDestroy()
        log("INFO", "onDestroy: done")
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        log("INFO", "onActivityResult: requestCode=$requestCode, resultCode=$resultCode")
        if (requestCode == EasyTierManager.VPN_REQUEST_CODE) {
            log("INFO", "VPN authorization result: $resultCode")
            easyTierManager?.onVpnAuthorizationResult(resultCode)
        }
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        try {
            val isDark = (newConfig.uiMode and Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES
            WindowInsetsControllerCompat(window, window.decorView).apply {
                isAppearanceLightStatusBars = !isDark
                isAppearanceLightNavigationBars = !isDark
            }
            webView.setBackgroundColor(getWebViewBackgroundColor())
            injectDarkMode()
        } catch (e: Exception) {
            logError("onConfigurationChanged failed", e)
        }
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
        fun getApiBaseUrl(): String {
            val url = "http://127.0.0.1:$httpServerPort"
            log("DEBUG", "AndroidBridge.getApiBaseUrl: $url")
            return url
        }

        @JavascriptInterface
        fun startVpn(): String {
            return try {
                log("INFO", "AndroidBridge.startVpn called")
                if (easyTierManager == null) {
                    log("INFO", "AndroidBridge.startVpn: creating EasyTierManager")
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
                log("INFO", "AndroidBridge.stopVpn called")
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