package com.easytier.eui

import android.annotation.SuppressLint
import android.os.Bundle
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
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
        log("INFO", "=== App started ===")
        log("INFO", "Log file: ${crashLogFile.absolutePath}")
        log("INFO", "FilesDir: ${filesDir.absolutePath}")
        log("INFO", "ExternalFilesDir: ${getExternalFilesDir(null)?.absolutePath}")

        try {
            setContentView(R.layout.activity_main)
            webView = findViewById(R.id.webview)
            setupWebView()

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

            webChromeClient = WebChromeClient()
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean = false
                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    injectApiConfig()
                }
            }

            addJavascriptInterface(AndroidBridge(), "AndroidBridge")
        }
    }

    private fun injectApiConfig() {
        webView.evaluateJavascript("window.__API_BASE__ = 'http://127.0.0.1:$httpServerPort';", null)
    }

    private suspend fun startPythonBackend() {
        log("INFO", "Starting Python backend...")

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
        val result = module.callAttr("start_android_server", filesDir.absolutePath)
        log("INFO", "start_android_server returned: $result, type=${result::class.java.simpleName}")

        val portPyObj = result.callAttr("get", "port")
        httpServerPort = portPyObj.toJava(Int::class.java) as Int
        log("INFO", "HTTP server port: $httpServerPort")

        withContext(Dispatchers.Main) {
            log("INFO", "Loading WebView...")
            loadWebView()
        }
    }

    private fun loadWebView() {
        webView.loadUrl("file:///android_asset/frontend/index.html")
        log("INFO", "WebView loadUrl called")
    }

    override fun onDestroy() {
        log("INFO", "onDestroy")
        scope.cancel()
        super.onDestroy()
    }

    inner class AndroidBridge {
        @JavascriptInterface
        fun getApiBaseUrl(): String = "http://127.0.0.1:$httpServerPort"

        @JavascriptInterface
        fun startVpn(): String = "{\"code\": 0}"

        @JavascriptInterface
        fun stopVpn(): String = "{\"code\": 0}"
    }
}