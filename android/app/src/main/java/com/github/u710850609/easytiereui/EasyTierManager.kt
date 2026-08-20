package com.github.u710850609.easytiereui

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.net.VpnService
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import java.io.File
import com.chaquo.python.Python
import java.io.PrintWriter
import java.io.StringWriter

class EasyTierManager(
    private val activity: Activity,
) {
    companion object {
        private const val TAG = "EasyTierManager"
        const val VPN_REQUEST_CODE = 1001

        @Volatile
        private var cachedFacade: Any? = null

        fun getFacade(): Any? {
            cachedFacade?.let { return it }
            synchronized(this) {
                cachedFacade?.let { return it }
                val py = Python.getInstance()
                val mod = py.getModule("et_adapters.facade")
                cachedFacade = mod.callAttr("get_facade")
                return cachedFacade
            }
        }
    }

    private var currentInstanceName: String? = null
    private var pendingVpnParams: VpnParams? = null

    init {
        EasyTierVpnService.onRevokeCallback = {
            onVpnRevoked()
        }
    }

    // ── Python 回调 ──────────────────────────────────────────

    fun startVpn(ipv4: String, ipv6: String, proxyCidrs: List<String>, dnsServers: List<String>, notificationTitle: String, notificationText: String) {
        AppLogger.info(TAG, "startVpn: ipv4=$ipv4, ipv6=$ipv6, cidrs=${proxyCidrs.size}, dns=${dnsServers.size}")
        stopVpnService()
        val params = VpnParams(ipv4, ipv6, proxyCidrs, dnsServers, notificationTitle, notificationText)
        val prepareIntent = VpnService.prepare(activity)
        if (prepareIntent != null) {
            AppLogger.info(TAG, "startVpn: VPN not authorized, showing dialog")
            pendingVpnParams = params
            activity.startActivityForResult(prepareIntent, VPN_REQUEST_CODE)
            return
        }
        startVpnService(params)
    }

    fun stopVpn() {
        AppLogger.info(TAG, "stopVpn")
        stopVpnService()
        currentInstanceName = null
    }

    fun updateNotification(title: String, text: String) {
        EasyTierVpnService.instance?.updateNotification(title, text)
    }

    // ── 授权回调 ─────────────────────────────────────────────

    fun onVpnAuthorizationResult(resultCode: Int) {
        if (resultCode == Activity.RESULT_OK) {
            AppLogger.info(TAG, "VPN authorization granted")
            pendingVpnParams?.let {
                pendingVpnParams = null
                startVpnService(it)
            }
        } else {
            AppLogger.warn(TAG, "VPN authorization denied")
            pendingVpnParams = null
        }
    }

    // ── VPN 控制 ─────────────────────────────────────────────

    private fun startVpnService(params: VpnParams) {
        try {
            if (activity.isFinishing) {
                AppLogger.error(TAG, "Activity is finishing, cannot start VPN")
                return
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1 && activity.isDestroyed) {
                AppLogger.error(TAG, "Activity is destroyed, cannot start VPN")
                return
            }

            val intent = Intent(activity, EasyTierVpnService::class.java)
            intent.putExtra("vpn_params", params)
            intent.putExtra("instance_name", currentInstanceName ?: "unknown")

            AppLogger.info(TAG, "startVpnService: calling startService")
            activity.startService(intent)

            AppLogger.info(TAG, "VPN started: ${params.ipv4}, CIDRs=${params.proxyCidrs.size}, DNS=${params.dnsServers.size}")
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "Start VPN error: ${sw}")
        }
    }

    private fun stopVpnService() {
        try {
            EasyTierVpnService.requestStop()
            AppLogger.info(TAG, "Called EasyTierVpnService.requestStop()")
            val intent = Intent(activity, EasyTierVpnService::class.java)
            val stopped = activity.stopService(intent)
            AppLogger.info(TAG, "stopService result=$stopped")
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "Stop VPN error: ${sw}")
        }
    }

    // ── 工具方法 ─────────────────────────────────────────────

    fun setLogLevel(level: String) {
        AppLogger.minLevel = when (level.lowercase()) {
            "debug" -> AppLogger.Level.DEBUG
            "info" -> AppLogger.Level.INFO
            "warn" -> AppLogger.Level.WARN
            "error" -> AppLogger.Level.ERROR
            "fatal" -> AppLogger.Level.FATAL
            "off" -> AppLogger.Level.OFF
            else -> {
                AppLogger.warn(TAG, "setLogLevel: unknown level '$level'")
                return
            }
        }
        AppLogger.info(TAG, "setLogLevel: changed to ${AppLogger.minLevel}")
    }

    fun getDeviceName(): String {
        try {
            val name = Settings.Global.getString(activity.contentResolver, Settings.Global.DEVICE_NAME)
            if (!name.isNullOrEmpty()) {
                AppLogger.debug(TAG, "getDeviceName from Settings.Global: $name")
                return name
            }
        } catch (e: Exception) {
            AppLogger.debug(TAG, "getDeviceName from Settings.Global failed: ${e.message}")
        }
        try {
            val name = Settings.System.getString(activity.contentResolver, "device_name")
            if (!name.isNullOrEmpty()) {
                AppLogger.debug(TAG, "getDeviceName from Settings.System: $name")
                return name
            }
        } catch (e: Exception) {
            AppLogger.debug(TAG, "getDeviceName from Settings.System failed: ${e.message}")
        }
        val model = Build.MODEL ?: "Unknown"
        AppLogger.debug(TAG, "getDeviceName fallback to Build.MODEL: $model")
        return model
    }

    fun installApk(filePath: String) {
        AppLogger.info(TAG, "installApk: $filePath")
        try {
            val apkFile = File(filePath)
            if (!apkFile.exists()) {
                AppLogger.error(TAG, "installApk: file not found: $filePath")
                return
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && !activity.packageManager.canRequestPackageInstalls()) {
                AppLogger.warn(TAG, "installApk: no REQUEST_INSTALL_PACKAGES permission, opening settings")
                val intent = Intent(android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                    data = Uri.parse("package:${activity.packageName}")
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                activity.startActivity(intent)
                return
            }
            val intent = Intent(Intent.ACTION_VIEW).apply {
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                    val uri = FileProvider.getUriForFile(
                        activity,
                        "${activity.packageName}.fileprovider",
                        apkFile
                    )
                    setDataAndType(uri, "application/vnd.android.package-archive")
                } else {
                    val uri = Uri.fromFile(apkFile)
                    setDataAndType(uri, "application/vnd.android.package-archive")
                }
            }
            activity.startActivity(intent)
            AppLogger.info(TAG, "installApk: intent started")
        } catch (e: Exception) {
            AppLogger.error(TAG, "installApk: failed", e)
        }
    }

    private fun onVpnRevoked() {
        AppLogger.info(TAG, "onVpnRevoked: VPN was revoked by another app")
        val instanceName = currentInstanceName
        currentInstanceName = null
        if (instanceName != null) {
            Thread {
                try {
                    AppLogger.info(TAG, "onVpnRevoked: stopping Python network instance $instanceName")
                    val facade = getFacade()
                    if (facade != null) {
                        facade.callAttr("stop_network", instanceName)
                        AppLogger.info(TAG, "onVpnRevoked: Python network instance stopped")
                    }
                } catch (e: Exception) {
                    AppLogger.error(TAG, "onVpnRevoked: stop_network failed: ${e.message}")
                }
            }.start()
        }
    }
}