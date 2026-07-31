package com.github.u710850609.easytiereui

import android.Manifest
import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.content.res.Configuration
import android.graphics.Color
import android.net.Uri
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
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowInsetsCompat
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewFeature
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.*
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import androidx.activity.SystemBarStyle
import androidx.activity.enableEdgeToEdge
import java.util.*

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "EasyTier"
        @JvmStatic
        var easyTierManager: EasyTierManager? = null
    }

    private lateinit var webView: WebView
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var httpServerPort = 0
    private lateinit var crashLogFile: File
    
    private var h5ThemeOverride: Boolean? = null // null = follow system, true = dark, false = light
    private val prefs: SharedPreferences by lazy { getSharedPreferences("easytier_prefs", MODE_PRIVATE) }

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
        crashLogFile = File(File(getExternalFilesDir(null), "logs"), "easytier_crash.log")
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
            log("INFO", "setupWebView done, calling applySavedTheme")
            applySavedTheme()
            log("INFO", "applySavedTheme done, calling setupBackPress")
            setupBackPress()
            requestNotificationPermission()

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
                settings.useWideViewPort = true
                settings.loadWithOverviewMode = true

                if (WebViewFeature.isFeatureSupported(WebViewFeature.ALGORITHMIC_DARKENING)) {
                    WebSettingsCompat.setAlgorithmicDarkeningAllowed(settings, false)
                }
                setBackgroundColor(Color.TRANSPARENT)
                overScrollMode = android.view.View.OVER_SCROLL_NEVER

                webChromeClient = object : WebChromeClient() {
                    override fun onCreateWindow(
                        view: WebView?,
                        isDialog: Boolean,
                        isUserGesture: Boolean,
                        resultMsg: android.os.Message?
                    ): Boolean {
                        val url = view?.hitTestResult?.extra
                        if (!url.isNullOrEmpty()) {
                            try {
                                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                            } catch (e: Exception) {
                                logError("onCreateWindow: failed to open $url", e)
                            }
                        }
                        return true
                    }
                }
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean = false
                    override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                        super.onPageStarted(view, url, favicon)
                        injectSafeArea()
                    }
                    override fun onPageFinished(view: WebView?, url: String?) {
                        super.onPageFinished(view, url)
                        log("INFO", "WebView page finished: $url")
                        injectSafeArea()
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

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) !=
                android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 0)
            }
        }
    }

    private fun setupBackPress() {
        log("INFO", "setupBackPress: registering callback")
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack()
                } else {
                    moveTaskToBack(true)
                }
            }
        })
    }

    private fun injectSafeArea() {
        try {
            val insets = WindowInsetsCompat.toWindowInsetsCompat(window.decorView.rootWindowInsets)
            val sat = insets.getInsetsIgnoringVisibility(WindowInsetsCompat.Type.statusBars()).top
            val sab = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom
            val sar = insets.getInsets(WindowInsetsCompat.Type.systemBars()).right
            val sal = insets.getInsets(WindowInsetsCompat.Type.systemBars()).left

            if (sat == 0 && sab == 0) {
                return
            }
            // 前端需要的是 CSS 像素（逻辑像素）。需要物理像素 除以 DPR
            val density = resources.displayMetrics.density
            val satDp = sat / density
            val sabDp = sab / density
            val sarDp = sar / density
            val salDp = sal / density
            log("DEBUG", "injectSafeArea: sat=$sat, sab=$sab, sar=$sar, sal=$sal, density=$density, satDp=${satDp}px, sabDp=${sabDp}px, sarDp=${sarDp}px, salDp=${salDp}px}")

            val js = """
                (function() {
                    document.documentElement.style.setProperty('--sat', '${satDp}px');
                    document.documentElement.style.setProperty('--sab', '${sabDp}px');
                    document.documentElement.style.setProperty('--sar', '${sarDp}px');
                    document.documentElement.style.setProperty('--sal', '${salDp}px');
                    console.log('[SafeArea] --sat=${satDp}px, --sab=${sabDp}px, --sar=${sarDp}px, --sal=${salDp}px');
                })();
            """.trimIndent()
            webView.evaluateJavascript(js, null)
        } catch (e: Exception) {
            logError("injectSafeArea failed", e)
        }
    }

    private fun downloadUsingSystemManager(url: String) {
        try {
            val downloadManager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            downloadManager.enqueue(DownloadManager.Request(Uri.parse(url)))
            log("INFO", "DownloadManager: enqueued $url")
        } catch (e: Exception) {
            logError("downloadUsingSystemManager failed", e)
            Toast.makeText(this, getString(com.github.u710850609.easytiereui.R.string.download_failed), Toast.LENGTH_SHORT).show()
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
            log("INFO", "EasyTierManager created (not auto-starting)")
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
        log("INFO", "onDestroy: stopping HTTP server, VPN, and cancelling scope")
        try {
            easyTierManager?.stop()
        } catch (e: Exception) {
            logError("onDestroy: stop failed", e)
        }
        scope.cancel()
        try {
            if (Python.isStarted()) {
                Python.getInstance().getModule("actions.settings").callAttr("shutdown")
                log("INFO", "onDestroy: Python shutdown signal sent")
            }
        } catch (e: Exception) {
            logError("onDestroy: shutdown failed", e)
        }
        super.onDestroy()
        log("INFO", "onDestroy: done")
    }

    override fun onPause() {
        super.onPause()
        log("INFO", "onPause: isFinishing=$isFinishing")
    }

    override fun onResume() {
        super.onResume()
        log("INFO", "onResume")
    }

    override fun onStop() {
        super.onStop()
        log("INFO", "onStop: isFinishing=$isFinishing")
    }

    override fun onStart() {
        super.onStart()
        log("INFO", "onStart")
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
            if (h5ThemeOverride == null) {
                enableEdgeToEdge(
                    statusBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT),
                    navigationBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT)
                )
                webView.setBackgroundColor(Color.TRANSPARENT)
            }
            injectSafeArea()
        } catch (e: Exception) {
            logError("onConfigurationChanged failed", e)
        }
    }

    private fun applySavedTheme() {
        val savedMode = prefs.getString("theme_mode", "system") ?: "system"
        when (savedMode) {
            "dark" -> {
                h5ThemeOverride = true
                enableEdgeToEdge(
                    statusBarStyle = SystemBarStyle.dark(Color.TRANSPARENT),
                    navigationBarStyle = SystemBarStyle.dark(Color.TRANSPARENT)
                )
            }
            "light" -> {
                h5ThemeOverride = false
                enableEdgeToEdge(
                    statusBarStyle = SystemBarStyle.light(Color.TRANSPARENT, Color.TRANSPARENT),
                    navigationBarStyle = SystemBarStyle.light(Color.TRANSPARENT, Color.TRANSPARENT)
                )
            }
            else -> {
                h5ThemeOverride = null
                enableEdgeToEdge(
                    statusBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT),
                    navigationBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT)
                )
            }
        }
        log("DEBUG", "applySavedTheme: mode=$savedMode, override=$h5ThemeOverride")
    }

    inner class AndroidBridge {
        @JavascriptInterface
        fun getApiBaseUrl(): String {
            val url = "http://127.0.0.1:$httpServerPort"
            log("DEBUG", "AndroidBridge.getApiBaseUrl: $url")
            return url
        }

        @JavascriptInterface
        fun setThemeMode(mode: String) {
            log("DEBUG", "AndroidBridge.setThemeMode: $mode")
            runOnUiThread {
                prefs.edit().putString("theme_mode", mode).apply()
                when (mode) {
                    "dark" -> {
                        h5ThemeOverride = true
                        enableEdgeToEdge(
                            statusBarStyle = SystemBarStyle.dark(Color.TRANSPARENT),
                            navigationBarStyle = SystemBarStyle.dark(Color.TRANSPARENT)
                        )
                    }
                    "light" -> {
                        h5ThemeOverride = false
                        enableEdgeToEdge(
                            statusBarStyle = SystemBarStyle.light(Color.TRANSPARENT, Color.TRANSPARENT),
                            navigationBarStyle = SystemBarStyle.light(Color.TRANSPARENT, Color.TRANSPARENT)
                        )
                    }
                    "system" -> {
                        h5ThemeOverride = null
                        enableEdgeToEdge(
                            statusBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT),
                            navigationBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT)
                        )
                    }
                }
            }
        }

        @JavascriptInterface
        fun downloadFile(url: String) {
            log("DEBUG", "AndroidBridge.downloadFile: $url")
            runOnUiThread {
                downloadUsingSystemManager(url)
            }
        }
    }
}