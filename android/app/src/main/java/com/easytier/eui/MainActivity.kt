package com.easytier.eui

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import kotlinx.coroutines.*

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    private var httpServerPort = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        setupWebView()

        scope.launch(Dispatchers.IO) {
            startPythonBackend()
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
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        val python = Python.getInstance()
        val module = python.getModule("main_noui")
        val result = module.callAttr("start_android_server", filesDir.absolutePath)

        val resultMap = result.toJava(Map::class.java) as Map<*, *>
        httpServerPort = (resultMap["port"] as Number).toInt()

        withContext(Dispatchers.Main) {
            loadWebView()
        }
    }

    private fun loadWebView() {
        webView.loadUrl("file:///android_asset/frontend/index.html")
    }

    override fun onDestroy() {
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