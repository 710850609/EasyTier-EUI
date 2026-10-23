package com.github.u710850609.easytiereui

import android.app.Service
import android.content.Intent
import android.os.IBinder

class VpnCoordinatorService : Service() {

    companion object {
        private const val TAG = "VpnCoordinatorSvc"
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

        when (action) {
            ACTION_STOP -> {
                handleStop()
                stopSelf(startId)
            }
            else -> {
                AppLogger.warn(TAG, "onStartCommand: unknown action=$action")
                stopSelf(startId)
            }
        }

        return START_NOT_STICKY
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
}