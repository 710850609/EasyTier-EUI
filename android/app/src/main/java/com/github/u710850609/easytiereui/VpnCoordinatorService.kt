package com.github.u710850609.easytiereui

import android.app.Service
import android.content.Intent
import android.os.IBinder
import kotlin.concurrent.thread

class VpnCoordinatorService : Service() {

    companion object {
        private const val TAG = "VpnCoordinatorSvc"
        const val ACTION_START = "action_start"
        const val ACTION_STOP = "action_stop"
        const val EXTRA_ACTION = "extra_action"
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.getStringExtra(EXTRA_ACTION) ?: run {
            AppLogger.warn(TAG, "onStartCommand: no action, stopping")
            stopSelf(startId)
            return START_NOT_STICKY
        }

        AppLogger.info(TAG, "onStartCommand: action=$action, startId=$startId")

        val commandId = startId
        thread(name = "vpn-coordinator") {
            try {
                when (action) {
                    ACTION_START -> handleStart()
                    ACTION_STOP -> handleStop()
                    else -> AppLogger.warn(TAG, "onStartCommand: unknown action=$action")
                }
            } catch (e: Exception) {
                AppLogger.error(TAG, "onStartCommand: error: ${e.message}")
            } finally {
                stopSelf(commandId)
                AppLogger.info(TAG, "onStartCommand: done, self-stopping")
            }
        }

        return START_NOT_STICKY
    }

    private fun handleStart() {
        if (!App.pythonReady) {
            AppLogger.warn(TAG, "handleStart: Python not ready yet, delaying...")
            val waited = waitForPythonReady(15000)
            if (!waited) {
                AppLogger.error(TAG, "handleStart: Python not ready after timeout, opening app")
                openMainActivity()
                return
            }
        }

        val manager = App.easyTierManager
        if (manager == null) {
            AppLogger.error(TAG, "handleStart: EasyTierManager is null")
            return
        }

        AppLogger.info(TAG, "handleStart: triggering auto-start in background")
        manager.triggerAutoStart()
    }

    private fun handleStop() {
        val manager = App.easyTierManager
        if (manager != null) {
            AppLogger.info(TAG, "handleStop: stopping VPN via EasyTierManager")
            manager.stopVpn(stopPythonNetwork = true)
        } else {
            AppLogger.warn(TAG, "handleStop: EasyTierManager is null, fallback to direct stop")
            EasyTierVpnService.requestStop()
        }
        EasyTierVpnTileService.requestStateUpdate(this)
    }

    private fun waitForPythonReady(timeoutMs: Int): Boolean {
        val startTime = System.currentTimeMillis()
        while (System.currentTimeMillis() - startTime < timeoutMs) {
            if (App.pythonReady && App.easyTierManager != null) {
                return true
            }
            Thread.sleep(200)
        }
        return App.pythonReady && App.easyTierManager != null
    }

    private fun openMainActivity() {
        try {
            val intent = packageManager.getLaunchIntentForPackage(packageName)?.apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            }
            if (intent != null) {
                startActivity(intent)
            }
        } catch (e: Exception) {
            AppLogger.error(TAG, "openMainActivity failed: ${e.message}")
        }
    }
}