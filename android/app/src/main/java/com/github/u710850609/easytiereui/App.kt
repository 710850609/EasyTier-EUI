package com.github.u710850609.easytiereui

import android.app.Application
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import kotlin.concurrent.thread

class App : Application() {

    companion object {
        private const val TAG = "App"

        @JvmStatic
        var easyTierManager: EasyTierManager? = null
            private set

        @JvmStatic
        var instance: App? = null
            private set

        @Volatile
        @JvmStatic
        var pythonReady: Boolean = false
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this

        AppLogger.logDir = File(getExternalFilesDir(null), "logs")
        AppLogger.logDir?.mkdirs()
        AppLogger.minLevel = AppLogger.Level.INFO
        AppLogger.info(TAG, "App.onCreate: initializing")

        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            val sw = StringWriter()
            throwable.printStackTrace(PrintWriter(sw))
            AppLogger.fatal(TAG, "Uncaught exception in thread ${thread.name}: ${sw}")
            throwable.printStackTrace()
        }

        easyTierManager = EasyTierManager(applicationContext, null)
        MainActivity.easyTierManager = easyTierManager
        AppLogger.info(TAG, "App.onCreate: EasyTierManager created (no Activity yet)")

        thread(name = "python-init") {
            try {
                initPython()
            } catch (e: Exception) {
                AppLogger.error(TAG, "Python init failed: ${e.message}")
            }
        }
    }

    private fun initPython() {
        try {
            AppLogger.info(TAG, "initPython: copying frontend assets...")
            copyAssetDir("frontend", File(filesDir, "frontend"))
            AppLogger.info(TAG, "initPython: frontend assets copied")

            if (!Python.isStarted()) {
                AppLogger.info(TAG, "initPython: starting Python runtime...")
                Python.start(AndroidPlatform(this))
                AppLogger.info(TAG, "initPython: Python.start() succeeded")
            } else {
                AppLogger.info(TAG, "initPython: Python already started")
            }

            val py = Python.getInstance()
            AppLogger.info(TAG, "initPython: calling main_noui.init_android_env...")
            val dataDir = filesDir.absolutePath
            val externalDir = getExternalFilesDir(null)?.absolutePath ?: dataDir
            py.getModule("main_noui").callAttr("init_android_env", dataDir, externalDir)
            AppLogger.info(TAG, "initPython: init_android_env done, dataDir=$dataDir, externalDir=$externalDir")

            AppLogger.info(TAG, "initPython: setup complete, pythonReady=true")

            pythonReady = true
            AppLogger.info(TAG, "initPython: ready")
        } catch (e: Exception) {
            AppLogger.error(TAG, "initPython failed: ${e.message}")
            throw e
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
}