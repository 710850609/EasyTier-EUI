package com.github.u710850609.easytiereui

import android.app.PendingIntent
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

class EasyTierVpnTileService : TileService() {
    companion object {
        private const val TAG = "EasyTierVpnTile"
        private const val PREFS_NAME = "easytier_vpn_tile"
        private const val PENDING_ACTION_KEY = "pending_action"
        const val ACTION_START = "start"
        const val ACTION_STOP = "stop"

        @Volatile
        private var isConnecting = false

        fun notifyVpnServiceCreated() {
            AppLogger.info(TAG, "notifyVpnServiceCreated: clearing connecting state")
            isConnecting = false
        }

        @Synchronized
        fun consumePendingAction(context: Context): String? {
            val preferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val action = preferences.getString(PENDING_ACTION_KEY, null)
            if (action != null) {
                preferences.edit().remove(PENDING_ACTION_KEY).commit()
                AppLogger.info(TAG, "consumePendingAction: consumed action=$action")
            }
            return action
        }

        fun requestStateUpdate(context: Context) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                AppLogger.info(TAG, "requestStateUpdate triggered")
                requestListeningState(context, ComponentName(context, EasyTierVpnTileService::class.java))
            }
        }

        private fun pendingAction(context: Context): String? =
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .getString(PENDING_ACTION_KEY, null)

        private fun savePendingAction(context: Context, action: String) {
            context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                .edit()
                .putString(PENDING_ACTION_KEY, action)
                .commit()
        }
    }

    override fun onStartListening() {
        super.onStartListening()
        AppLogger.info(TAG, "onStartListening: instance=${EasyTierVpnService.instance != null}")
        updateTileState()
    }

    override fun onClick() {
        super.onClick()
        AppLogger.info(TAG, "onClick: isLocked=$isLocked, instance=${EasyTierVpnService.instance != null}")

        if (isLocked) {
            unlockAndRun(::handleClick)
        } else {
            handleClick()
        }
    }

    private fun handleClick() {
        if (isConnecting) {
            AppLogger.info(TAG, "handleClick: already connecting, cancelling and reverting")
            clearConnectingState()
            return
        }

        val action = consumePendingAction(this)
            ?: if (EasyTierVpnService.instance == null) ACTION_START else ACTION_STOP
        AppLogger.info(TAG, "handleClick: action=$action, instance=${EasyTierVpnService.instance != null}")
        updateTileState()

        val permissionRequired = action == ACTION_START && VpnService.prepare(this) != null
        if (permissionRequired) {
            AppLogger.info(TAG, "handleClick: permission required, opening app")
            openApp()
            return
        }

        if (EasyTierVpnService.instance == null && action == ACTION_START) {
            handleStartViaCoordinator()
        } else if (action == ACTION_STOP) {
            handleStopViaCoordinator()
        }
    }

    private fun handleStartViaCoordinator() {
        val manager = App.easyTierManager
        if (manager != null && App.pythonReady) {
            AppLogger.info(TAG, "handleStart: triggering auto-start")
            setConnectingState()
            val started = manager.triggerAutoStart()
            if (!started) {
                AppLogger.warn(TAG, "handleStart: no network to start, opening app")
                clearConnectingState()
                openApp()
            }
        } else {
            AppLogger.warn(TAG, "handleStart: not ready (manager=${manager != null}, pythonReady=${App.pythonReady}), opening app")
            openApp()
        }
    }

    private fun handleStopViaCoordinator() {
        val manager = App.easyTierManager
        if (manager != null) {
            AppLogger.info(TAG, "handleClick: stopping via coordinator")
            val intent = Intent(this, VpnCoordinatorService::class.java).apply {
                putExtra(VpnCoordinatorService.EXTRA_ACTION, VpnCoordinatorService.ACTION_STOP)
            }
            startService(intent)
        } else {
            AppLogger.warn(TAG, "handleClick: EasyTierManager is null, fallback to direct stop")
            EasyTierVpnService.requestStop()
        }
        updateTileState()
    }

    private fun updateTileState() {
        qsTile?.apply {
            state = when {
                EasyTierVpnService.instance != null -> Tile.STATE_ACTIVE
                isConnecting -> Tile.STATE_UNAVAILABLE
                else -> Tile.STATE_INACTIVE
            }
            AppLogger.info(TAG, "updateTileState: state=${when (state) {
                Tile.STATE_ACTIVE -> "ACTIVE"
                Tile.STATE_UNAVAILABLE -> "UNAVAILABLE"
                else -> "INACTIVE"
            }}")
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

    private fun setConnectingState() {
        isConnecting = true
        qsTile?.apply {
            state = Tile.STATE_UNAVAILABLE
            updateTile()
        }
        AppLogger.info(TAG, "setConnectingState: tile=UNAVAILABLE")
    }

    private fun clearConnectingState() {
        isConnecting = false
        qsTile?.apply {
            state = Tile.STATE_INACTIVE
            updateTile()
        }
        AppLogger.info(TAG, "clearConnectingState: tile=INACTIVE")
    }
}