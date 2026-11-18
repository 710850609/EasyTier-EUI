package com.github.u710850609.easytiereui

import android.app.Service
import android.content.Intent
import android.os.Handler
import android.os.IBinder
import android.os.Looper

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
            ACTION_STOP -> handleStop(startId)
            else -> {
                AppLogger.warn(TAG, "onStartCommand: unknown action=$action")
                stopSelf(startId)
            }
        }

        return START_NOT_STICKY
    }

    private fun handleStop(startId: Int) {
        val manager = App.easyTierManager
        if (manager == null) {
            AppLogger.warn(TAG, "handleStop: EasyTierManager is null, fallback to direct stop")
            EasyTierVpnService.requestStop()
            EasyTierVpnTileService.requestStateUpdate(this)
            stopSelf(startId)
            return
        }
        AppLogger.info(TAG, "handleStop: stopping VPN via EasyTierManager on background thread")
        // stop_network 会逐实例 join 监控线程并等待实例退出，可能耗时数秒，
        // 若在 onStartCommand（主线程）中同步执行会阻塞 UI 导致 ANR/崩溃。
        Thread {
            try {
                manager.stopVpn(stopPythonNetwork = true)
            } catch (e: Exception) {
                AppLogger.error(TAG, "handleStop: stopVpn failed: ${e.message}")
            }
            Handler(Looper.getMainLooper()).post {
                EasyTierVpnTileService.requestStateUpdate(this)
                stopSelf(startId)
            }
        }.start()
    }
}