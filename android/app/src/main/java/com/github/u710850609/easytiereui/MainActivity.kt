package com.github.u710850609.easytiereui

import com.github.u710850609.easytiereui.BuildConfig
import android.Manifest
import android.animation.ObjectAnimator
import android.annotation.SuppressLint
import android.app.DownloadManager
import android.content.Context
import android.content.ClipboardManager
import android.content.Intent
import android.content.SharedPreferences
import android.content.res.Configuration
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.PermissionRequest
import android.webkit.WebResourceRequest
import android.os.Build
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.core.splashscreen.SplashScreenViewProvider
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.ViewCompat
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewFeature
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.*
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import org.json.JSONObject
import androidx.activity.SystemBarStyle
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.Lifecycle

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "EasyTier"
        @JvmStatic
        var easyTierManager: EasyTierManager? = null
        @JvmStatic
        var appConfig = AppConfig()

        @JvmStatic
        fun setWebviewDebug(enabled: Boolean) {
            appConfig = appConfig.copy(webviewDebug = enabled)
            WebView.setWebContentsDebuggingEnabled(enabled)
            AppLogger.info(TAG, "setWebviewDebug: $enabled")
        }

        @JvmStatic
        fun setIgnoreSslErrors(enabled: Boolean) {
            appConfig = appConfig.copy(ignoreSslErrors = enabled)
            AppLogger.info(TAG, "setIgnoreSslErrors: $enabled")
        }

        data class AppConfig(
            val logLevel: String = "warn",
            val webviewDebug: Boolean = false,
            val ignoreSslErrors: Boolean = false
        )
    }

    private lateinit var webView: WebView
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var httpServerPort = 0
    private var h5ThemeOverride: Boolean? = null // null = follow system, true = dark, false = light
    private val prefs: SharedPreferences by lazy { getSharedPreferences("easytier_prefs", MODE_PRIVATE) }
    private var splashContentLoaded = false
    private var pendingPermissionRequest: android.webkit.PermissionRequest? = null
    private var splashScreenView: SplashScreenViewProvider? = null
    private var splashIconView: View? = null
    private var splashFadeStarted = false

    private fun loadAppConfig() {
        try {
            val settingFile = File(filesDir, "data/setting.json")
            if (!settingFile.exists()) {
                AppLogger.info(TAG, "loadAppConfig: setting.json not found, using defaults")
                applyConfig()
                return
            }
            val json = settingFile.readText()
            val root = JSONObject(json)

            val levelStr = root.optString("log_level", "warn").lowercase()
            val webviewDebug = root.optBoolean("webview_debug", false)
            val ignoreSslErrors = root.optBoolean("ignore_ssl_errors", false)

            appConfig = AppConfig(
                logLevel = levelStr,
                webviewDebug = webviewDebug,
                ignoreSslErrors = ignoreSslErrors
            )
            AppLogger.info(TAG, "loadAppConfig: logLevel=$levelStr, webviewDebug=$webviewDebug, ignoreSslErrors=$ignoreSslErrors")
            applyConfig()
        } catch (e: Exception) {
            AppLogger.error(TAG, "loadAppConfig: failed to read setting.json: ${e.message}")
            applyConfig()
        }
    }

    private fun applyConfig() {
        AppLogger.minLevel = when (appConfig.logLevel) {
            "debug" -> AppLogger.Level.DEBUG
            "info" -> AppLogger.Level.INFO
            "warn" -> AppLogger.Level.WARN
            "error" -> AppLogger.Level.ERROR
            "fatal" -> AppLogger.Level.FATAL
            "off" -> AppLogger.Level.OFF
            else -> {
                AppLogger.warn(TAG, "applyConfig: unknown logLevel '${appConfig.logLevel}', using WARN")
                AppLogger.Level.WARN
            }
        }
        AppLogger.info(TAG, "applyConfig: minLevel=${AppLogger.minLevel}, webviewDebug=${appConfig.webviewDebug}, ignoreSslErrors=${appConfig.ignoreSslErrors}")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()

        splashScreen.setOnExitAnimationListener { provider ->
            splashScreenView = provider
            splashIconView = try { provider.iconView } catch (_: Exception) { null }
            if (splashIconView == null) {
                provider.remove()
                applySavedTheme()
                return@setOnExitAnimationListener
            }

            val moveDuration = 300L
            val slideUp = ObjectAnimator.ofFloat(
                splashIconView!!,
                View.TRANSLATION_Y,
                0f,
                -resources.displayMetrics.heightPixels * 0.25f
            ).apply {
                duration = moveDuration
                interpolator = AccelerateDecelerateInterpolator()
            }
            val scaleDownX = ObjectAnimator.ofFloat(splashIconView!!, View.SCALE_X, 1f, 0.7f).apply {
                duration = moveDuration
                interpolator = AccelerateDecelerateInterpolator()
            }
            val scaleDownY = ObjectAnimator.ofFloat(splashIconView!!, View.SCALE_Y, 1f, 0.7f).apply {
                duration = moveDuration
                interpolator = AccelerateDecelerateInterpolator()
            }

            slideUp.start()
            scaleDownX.start()
            scaleDownY.start()

            Handler(Looper.getMainLooper()).postDelayed({
                tryStartFade()
            }, 150)
        }

        Handler(Looper.getMainLooper()).postDelayed({
            splashContentLoaded = true
            tryStartFade()
        }, 4000)

        super.onCreate(savedInstanceState)
        AppLogger.logDir = File(getExternalFilesDir(null), "logs")
        AppLogger.logDir?.mkdirs()

        loadAppConfig()

        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            val sw = StringWriter()
            throwable.printStackTrace(PrintWriter(sw))
            AppLogger.fatal(TAG, "Uncaught exception in thread ${thread.name}: ${sw}")
            throwable.printStackTrace()
        }

        AppLogger.info(TAG, "=== App started ===")
        AppLogger.info(TAG, "Log dir: ${AppLogger.logDir?.absolutePath}")
        AppLogger.info(TAG, "FilesDir: ${filesDir.absolutePath}")
        AppLogger.info(TAG, "ExternalFilesDir: ${getExternalFilesDir(null)?.absolutePath}")

        try {
            AppLogger.info(TAG, "onCreate: setting up UI")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                try {
                    // WebView.setDataDirectorySuffix() 必须在对 任何 WebView 实例化之前调用
                    // 否则会报 IllegalStateException: WebView already initialized。
                    WebView.setDataDirectorySuffix(applicationContext.packageName)
                    AppLogger.info(TAG, "WebView.setDataDirectorySuffix ok")
                } catch (e: IllegalStateException) {
                    AppLogger.warn(TAG, "WebView.setDataDirectorySuffix failed (already initialized): ${e.message}")
                }
            }
            if (appConfig.webviewDebug) {
                // 调试地址 chrome://inspect
                WebView.setWebContentsDebuggingEnabled(true)
                AppLogger.info(TAG, "WebView remote debugging enabled")
            }
            // enableEdgeToEdge(
            //    statusBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT),
            //    navigationBarStyle = SystemBarStyle.auto(Color.TRANSPARENT, Color.TRANSPARENT)
            // )
            setContentView(R.layout.activity_main)
            AppLogger.info(TAG, "setContentView done, finding WebView")
            webView = findViewById(R.id.webview)
            AppLogger.info(TAG, "WebView found, calling setupWebView")
            setupWebView()
            AppLogger.info(TAG, "setupWebView done, calling applySavedTheme")
            applySavedTheme()
            AppLogger.info(TAG, "applySavedTheme done, calling setupBackPress")
            setupBackPress()
            requestNotificationPermission()

            scope.launch(Dispatchers.IO) {
                try {
                    startPythonBackend()
                } catch (e: Exception) {
                    AppLogger.error(TAG,"Python backend failed", e)
                    withContext(Dispatchers.Main) {
                        webView.loadData(
                            "<h2>Startup Error</h2><pre>${e.message}\n\n${e.stackTraceToString()}</pre>",
                            "text/html", "UTF-8"
                        )
                    }
                }
            }
            AppLogger.info(TAG, "onCreate: done")
        } catch (e: Exception) {
            AppLogger.error(TAG,"onCreate failed", e)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        try {
            AppLogger.info(TAG, "setupWebView: configuring WebView")
            webView.apply {
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.allowFileAccess = true
                settings.allowContentAccess = true
                settings.cacheMode = android.webkit.WebSettings.LOAD_NO_CACHE
                settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                settings.useWideViewPort = true
                settings.loadWithOverviewMode = true

                if (WebViewFeature.isFeatureSupported(WebViewFeature.ALGORITHMIC_DARKENING)) {
                    WebSettingsCompat.setAlgorithmicDarkeningAllowed(settings, false)
                }
                setBackgroundColor(Color.TRANSPARENT)
                overScrollMode = android.view.View.OVER_SCROLL_NEVER

                webChromeClient = object : WebChromeClient() {
                    override fun onPermissionRequest(request: PermissionRequest?) {
                        request?.let {
                            val resources = it.resources
                            for (resource in resources) {
                                if (resource == PermissionRequest.RESOURCE_VIDEO_CAPTURE) {
                                    if (checkSelfPermission(Manifest.permission.CAMERA) ==
                                        android.content.pm.PackageManager.PERMISSION_GRANTED) {
                                        it.grant(resources)
                                        return
                                    } else {
                                        pendingPermissionRequest?.deny()
                                        pendingPermissionRequest = it
                                        requestCameraPermission()
                                        return
                                    }
                                }
                            }
                            it.deny()
                        }
                    }

                    override fun onCreateWindow(
                        view: WebView?,
                        isDialog: Boolean,
                        isUserGesture: Boolean,
                        resultMsg: android.os.Message?
                    ): Boolean {
                        val url = view?.hitTestResult?.extra
                        if (!url.isNullOrEmpty()) {
                            val host = Uri.parse(url).host ?: ""
                            if (host != "127.0.0.1" && host != "localhost") {
                                openInSystemBrowser(url)
                            } else {
                                view?.loadUrl(url)
                            }
                        }
                        return true
                    }
                }
                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                        val url = request?.url?.toString() ?: return false
                        val host = request.url?.host ?: return false
                        val isDebug = request.url?.getQueryParameter("debug") == "true"
                        if (host == "127.0.0.1" || host == "localhost"
                            || host.startsWith("192.168.") || host.startsWith("10.")
                            || isDebug) {
                            return false
                        }
                        openInSystemBrowser(url)
                        return true
                    }
                    override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                        super.onPageStarted(view, url, favicon)
                        injectSafeArea()
                    }
                    override fun onPageFinished(view: WebView?, url: String?) {
                        super.onPageFinished(view, url)
                        AppLogger.info(TAG, "WebView page finished: $url")
                        splashContentLoaded = true
                        tryStartFade()
                        injectSafeArea()
                    }
                    override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: android.webkit.WebResourceError?) {
                        AppLogger.error(TAG, "WebView error: ${error?.description} for ${request?.url}")
                        splashContentLoaded = true
                        tryStartFade()
                    }
                    override fun onReceivedSslError(view: WebView?, handler: android.webkit.SslErrorHandler?, error: android.net.http.SslError?) {
                        // val host = Uri.parse(error?.url).host ?: ""
                        // val isLocal = host == "127.0.0.1" || host == "localhost"
                        //     || host.startsWith("192.168.") || host.startsWith("10.")
                        // AppLogger.info(TAG, "onReceivedSslError: url=${error?.url}, host=$host, isLocal=$isLocal, ignoreSslErrors=${appConfig.ignoreSslErrors}, error=${error?.primaryError}")
                        // if (appConfig.ignoreSslErrors || isLocal) {
                        if (appConfig.ignoreSslErrors) {
                            handler?.proceed()
                        } else {
                            handler?.cancel()
                        }
                    }
                }

                addJavascriptInterface(AndroidBridge(), "AndroidBridge")
            }
            AppLogger.info(TAG, "setupWebView: done")
        } catch (e: Exception) {
            AppLogger.error(TAG,"setupWebView failed", e)
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

    private fun requestCameraPermission() {
        if (checkSelfPermission(Manifest.permission.CAMERA) !=
            android.content.pm.PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.CAMERA), 1)
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1) {
            if (grantResults.isNotEmpty() && grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED) {
                AppLogger.info(TAG, "Camera permission granted")
                pendingPermissionRequest?.grant(pendingPermissionRequest?.resources ?: emptyArray())
                pendingPermissionRequest = null
            } else {
                AppLogger.warn(TAG, "Camera permission denied by user")
                pendingPermissionRequest?.deny()
                pendingPermissionRequest = null
                Toast.makeText(this, R.string.camera_permission_denied, Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setupBackPress() {
        AppLogger.info(TAG, "setupBackPress: registering callback")
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
            val insets = ViewCompat.getRootWindowInsets(window.decorView)
            val sat = insets?.getInsetsIgnoringVisibility(WindowInsetsCompat.Type.statusBars())?.top ?: 0
            val sab = insets?.getInsets(WindowInsetsCompat.Type.navigationBars())?.bottom ?: 0
            val sar = insets?.getInsets(WindowInsetsCompat.Type.systemBars())?.right ?: 0
            val sal = insets?.getInsets(WindowInsetsCompat.Type.systemBars())?.left ?: 0

            if (sat == 0 && sab == 0) {
                return
            }

            // 判断是否是手势导航：三键导航栏高度通常为 48dp，手势条通常为 8~20dp
            val gestureHeight = insets?.getInsets(WindowInsetsCompat.Type.mandatorySystemGestures())?.bottom ?: 0
            val isGestureNav = gestureHeight > 0 && sab < 30 * resources.displayMetrics.density

            // 前端需要的是 CSS 像素（逻辑像素）。需要物理像素 除以 DPR
            val density = resources.displayMetrics.density
            val satDp = sat / density
            val sabDp = if (isGestureNav) sab / density else 0f  // 三键导航栏不预留底部安全区域
            val sarDp = sar / density
            val salDp = sal / density
            AppLogger.debug(TAG, "injectSafeArea: sat=$sat, sab=$sab, isGestureNav=$isGestureNav, density=$density, satDp=${satDp}px, sabDp=${sabDp}px, sarDp=${sarDp}px, salDp=${salDp}px")

            val js = """
                (function() {
                    if (!document.documentElement) return;
                    document.documentElement.style.setProperty('--sat', '${satDp}px');
                    document.documentElement.style.setProperty('--sab', '${sabDp}px');
                    document.documentElement.style.setProperty('--sar', '${sarDp}px');
                    document.documentElement.style.setProperty('--sal', '${salDp}px');
                    console.log('[SafeArea] --sat=${satDp}px, --sab=${sabDp}px, --sar=${sarDp}px, --sal=${salDp}px');
                })();
            """.trimIndent()
            webView.evaluateJavascript(js, null)
        } catch (e: Exception) {
            AppLogger.error(TAG,"injectSafeArea failed", e)
        }
    }

    private fun openInSystemBrowser(url: String) {
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        } catch (e: Exception) {
            AppLogger.error(TAG,"openInSystemBrowser failed", e)
        }
    }

    private fun downloadUsingSystemManager(url: String, fileName: String?) {
        try {
            val downloadManager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            val request = DownloadManager.Request(Uri.parse(url))
            val destName = when {
                !fileName.isNullOrEmpty() -> fileName
                else -> extractFileNameFromUrl(url)
            }
            if (!destName.isNullOrEmpty()) {
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, destName)
                request.setTitle(destName)
            }
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            downloadManager.enqueue(request)
            AppLogger.info(TAG, "DownloadManager: enqueued $url, fileName=$destName")
        } catch (e: Exception) {
            AppLogger.error(TAG,"downloadUsingSystemManager failed", e)
            Toast.makeText(this, getString(com.github.u710850609.easytiereui.R.string.download_failed), Toast.LENGTH_SHORT).show()
        }
    }

    private fun extractFileNameFromUrl(url: String): String? {
        try {
            val path = Uri.parse(url).lastPathSegment ?: return null
            if (path.contains('.') && !path.endsWith('.') && path.length > 1) {
                return path.substringAfterLast('/')
            }
        } catch (e: Exception) {
            AppLogger.warn(TAG, "extractFileNameFromUrl failed: ${e.message}")
        }
        return null
    }

    private suspend fun startPythonBackend() {
        AppLogger.info(TAG, "Starting Python backend...")

        AppLogger.info(TAG, "Copying frontend assets...")
        copyAssetDir("frontend", File(filesDir, "frontend"))
        AppLogger.info(TAG, "Frontend assets copied")

        if (!Python.isStarted()) {
            AppLogger.info(TAG, "Python not started, calling Python.start()...")
            Python.start(AndroidPlatform(this))
            AppLogger.info(TAG, "Python.start() succeeded")
        } else {
            AppLogger.info(TAG, "Python already started")
        }

        AppLogger.info(TAG, "Getting Python instance...")
        val python = Python.getInstance()
        AppLogger.info(TAG, "Python instance obtained")

        AppLogger.info(TAG, "Importing main_noui module...")
        val module = python.getModule("main_noui")
        AppLogger.info(TAG, "main_noui module imported successfully")

        AppLogger.info(TAG, "Calling start_android_server with data_dir=${filesDir.absolutePath}...")
        val externalDir = getExternalFilesDir(null)?.absolutePath ?: ""
        AppLogger.info(TAG, "start_android_server: externalDir=$externalDir")
        val result = module.callAttr("start_android_server", filesDir.absolutePath, externalDir)
        AppLogger.info(TAG, "start_android_server returned: $result, type=${result::class.java.simpleName}")

        val portPyObj = result.callAttr("get", "port")
        httpServerPort = portPyObj.toJava(Int::class.java) as Int
        AppLogger.info(TAG, "HTTP server port: $httpServerPort")

        withContext(Dispatchers.Main) {
            AppLogger.info(TAG, "Loading WebView...")
            loadWebView()
            AppLogger.info(TAG, "Creating EasyTierManager...")
            easyTierManager = EasyTierManager(this@MainActivity)
            AppLogger.info(TAG, "EasyTierManager created (not auto-starting)")
        }
    }

    private fun loadWebView() {
        try {
            val url = "http://127.0.0.1:$httpServerPort/cgi/ThirdParty/EasyTier-EUI/index.cgi"
            AppLogger.info(TAG, "Loading WebView from $url")
            webView.loadUrl(url)
        } catch (e: Exception) {
            AppLogger.error(TAG,"loadWebView failed", e)
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
                    AppLogger.warn(TAG, "copyAssetDir: failed to copy $assetPath: ${e.message}")
                }
                return
            }
            targetDir.mkdirs()
            for (name in list) {
                copyAssetDir("$assetPath/$name", File(targetDir, name))
            }
        } catch (e: Exception) {
            AppLogger.warn(TAG, "copyAssetDir: failed for $assetPath: ${e.message}")
        }
    }

    override fun finish() {
        val sw = StringWriter()
        Thread.currentThread().stackTrace.forEach { sw.write("  $it\r\n") }
        AppLogger.warn(TAG, "finish() called! Stack trace:\r\n${sw}")
        super.finish()
    }

    override fun onDestroy() {
        AppLogger.info(TAG, "onDestroy: stopping HTTP server, VPN, and cancelling scope")
        pendingPermissionRequest?.deny()
        pendingPermissionRequest = null
        try {
            easyTierManager?.stopVpn()
        } catch (e: Exception) {
            AppLogger.error(TAG,"onDestroy: stop failed", e)
        }
        scope.cancel()
        try {
            if (Python.isStarted()) {
                Python.getInstance().getModule("actions.settings").callAttr("shutdown")
                AppLogger.info(TAG, "onDestroy: Python shutdown signal sent")
            }
        } catch (e: Exception) {
            AppLogger.error(TAG,"onDestroy: shutdown failed", e)
        }
        super.onDestroy()
        AppLogger.info(TAG, "onDestroy: done")
    }

    override fun onPause() {
        super.onPause()
        AppLogger.info(TAG, "onPause: isFinishing=$isFinishing")
    }

    override fun onResume() {
        super.onResume()
        if (h5ThemeOverride == null) {
            applySavedTheme()
        }
        AppLogger.info(TAG, "onResume")
    }

    override fun onStop() {
        super.onStop()
        AppLogger.info(TAG, "onStop: isFinishing=$isFinishing")
    }

    override fun onStart() {
        super.onStart()
        AppLogger.info(TAG, "onStart")
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        AppLogger.info(TAG, "onActivityResult: requestCode=$requestCode, resultCode=$resultCode")
        if (requestCode == EasyTierManager.VPN_REQUEST_CODE) {
            AppLogger.info(TAG, "VPN authorization result: $resultCode")
            easyTierManager?.onVpnAuthorizationResult(resultCode)
        }
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        if (!lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) return
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
            AppLogger.error(TAG,"onConfigurationChanged failed", e)
        }
    }

    private fun tryStartFade() {
        val iconView = splashIconView ?: return
        val provider = splashScreenView ?: return
        if (!splashContentLoaded || splashFadeStarted) return
        splashFadeStarted = true

        val fadeDuration = 300L
        val fadeOut = ObjectAnimator.ofFloat(iconView, View.ALPHA, 1f, 0f).apply {
            duration = fadeDuration
            interpolator = AccelerateDecelerateInterpolator()
        }
        fadeOut.start()

        Handler(Looper.getMainLooper()).postDelayed({
            splashScreenView?.remove()
            applySavedTheme()
        }, fadeDuration)
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
        AppLogger.debug(TAG, "applySavedTheme: mode=$savedMode, override=$h5ThemeOverride")
    }

    inner class AndroidBridge {
        @JavascriptInterface
        fun getApiBaseUrl(): String {
            val url = "http://127.0.0.1:$httpServerPort"
            AppLogger.debug(TAG, "AndroidBridge.getApiBaseUrl: $url")
            return url
        }

        @JavascriptInterface
        fun setThemeMode(mode: String) {
            AppLogger.debug(TAG, "AndroidBridge.setThemeMode: $mode")
            runOnUiThread {
                prefs.edit().putString("theme_mode", mode).apply()
                applySavedTheme()
            }
        }

        @JavascriptInterface
        fun downloadFile(url: String, fileName: String?) {
            AppLogger.debug(TAG, "AndroidBridge.downloadFile: url=$url, fileName=$fileName")
            runOnUiThread {
                downloadUsingSystemManager(url, fileName)
            }
        }

        @JavascriptInterface
        fun installApk(filePath: String) {
            AppLogger.debug(TAG, "AndroidBridge.installApk: $filePath")
            runOnUiThread {
                easyTierManager?.installApk(filePath)
            }
        }

        @JavascriptInterface
        fun readClipboard(): String {
            AppLogger.debug(TAG, "AndroidBridge.readClipboard")
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip
            if (clip != null && clip.itemCount > 0) {
                return clip.getItemAt(0).text?.toString() ?: ""
            }
            return ""
        }
    }
}