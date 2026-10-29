package com.github.u710850609.easytiereui

import android.app.PendingIntent
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

class EasyTierVpnTileService : TileService() {
    companion object {
        private const val TAG = "EasyTierVpnTile"

        @Volatile
        private var activeTile: Tile? = null

        /**
         * 磁贴状态以「是否有组网配置运行中」为准，而不是以 VPN 服务是否已启动为准。
         * 初始节点连不上时配置仍在运行（一直等待重试），磁贴也应显示为已开启。
         */
        private fun isNetworkRunning(): Boolean {
            if (!App.pythonReady) return false
            val manager = App.easyTierManager ?: return false
            return try {
                manager.isNetworkRunning()
            } catch (e: Exception) {
                AppLogger.error(TAG, "isNetworkRunning failed: ${e.message}")
                false
            }
        }

        fun notifyVpnServiceCreated() {
            val isRunning = isNetworkRunning()
            AppLogger.info(TAG, "notifyVpnServiceCreated: pushing tile state, networkRunning=$isRunning")
            updateTileDirect(isRunning)
        }

        private fun updateTileDirect(isRunning: Boolean) {
            activeTile?.apply {
                state = if (isRunning) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
                updateTile()
            }
        }

        fun requestStateUpdate(context: Context) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                AppLogger.info(TAG, "requestStateUpdate triggered")
                requestListeningState(context, ComponentName(context, EasyTierVpnTileService::class.java))
            }
        }
    }

    override fun onStartListening() {
        super.onStartListening()
        activeTile = qsTile
        AppLogger.info(TAG, "onStartListening: pythonReady=${App.pythonReady}")
        updateTileState()
    }

    override fun onStopListening() {
        super.onStopListening()
        activeTile = null
        AppLogger.info(TAG, "onStopListening")
    }

    override fun onClick() {
        super.onClick()
        AppLogger.info(TAG, "onClick: isLocked=$isLocked, pythonReady=${App.pythonReady}")

        if (isLocked) {
            unlockAndRun(::handleClick)
        } else {
            handleClick()
        }
    }

    private fun handleClick() {
        val manager = App.easyTierManager
        if (manager == null || !App.pythonReady) {
            AppLogger.warn(TAG, "handleClick: not ready (manager=${manager != null}, pythonReady=${App.pythonReady}), opening app")
            openApp()
            return
        }

        if (manager.isNetworkRunning()) {
            AppLogger.info(TAG, "handleClick: network running, stopping")
            stopNetwork()
            return
        }

        if (VpnService.prepare(this) != null) {
            AppLogger.info(TAG, "handleClick: VPN permission required, opening app")
            openApp()
            return
        }

        AppLogger.info(TAG, "handleClick: no network running, starting")
        startNetwork(manager)
    }

    private fun startNetwork(manager: EasyTierManager) {
        // 启动配置需要等待（可能包含连接初始节点），先按已开启显示，避免磁贴停在未开启状态
        applyTileState(true)
        Thread {
            val started = manager.triggerAutoStart()
            Handler(Looper.getMainLooper()).post {
                if (started) {
                    AppLogger.info(TAG, "startNetwork: started, posting connecting notification")
                    EasyTierVpnService.postConnectingNotification(
                        this,
                        EasyTierVpnService.defaultAppName(),
                        EasyTierVpnService.defaultStartText()
                    )
                } else {
                    AppLogger.warn(TAG, "startNetwork: no network to start, opening app")
                    openApp()
                }
                updateTileState()
            }
        }.start()
    }

    private fun stopNetwork() {
        AppLogger.info(TAG, "stopNetwork: stopping via coordinator")
        val intent = Intent(this, VpnCoordinatorService::class.java).apply {
            putExtra(VpnCoordinatorService.EXTRA_ACTION, VpnCoordinatorService.ACTION_STOP)
        }
        startService(intent)
        applyTileState(false)
    }

    private fun updateTileState() {
        val running = isNetworkRunning()
        AppLogger.info(TAG, "updateTileState: networkRunning=$running")
        applyTileState(running)
    }

    private fun applyTileState(running: Boolean) {
        qsTile?.apply {
            state = if (running) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
            updateTile()
        }
    }

    private fun openApp() {
        val intent = packageManager.getLaunchIntentForPackage(packageName)?.apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        } ?: run {
            AppLogger.error(TAG, "openApp: launch intent is null")
            return
        }

        AppLogger.info(TAG, "openApp: launching $packageName")
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                val pendingIntent = PendingIntent.getActivity(
                    this, 0, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
                )
                startActivityAndCollapse(pendingIntent)
            } else {
                @Suppress("DEPRECATION")
                startActivityAndCollapse(intent)
            }
        } catch (e: Exception) {
            AppLogger.error(TAG, "openApp: startActivityAndCollapse failed, fallback to startActivity", e)
            try {
                startActivity(intent)
            } catch (e2: Exception) {
                AppLogger.error(TAG, "openApp: startActivity also failed", e2)
            }
        }
    }
}