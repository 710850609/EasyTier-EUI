package com.github.u710850609.easytiereui

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import androidx.core.content.FileProvider
import java.io.File
import com.chaquo.python.Python
import org.json.JSONObject
import java.io.PrintWriter
import java.io.StringWriter
import java.util.concurrent.Executors

class EasyTierManager(
    private val activity: Activity,
) {
    companion object {
        private const val TAG = "EasyTierManager"
        private const val MONITOR_INTERVAL = 5000L
        const val VPN_REQUEST_CODE = 1001
    }

    private val handler = Handler(Looper.getMainLooper())
    private val monitorExecutor = Executors.newSingleThreadExecutor { r ->
        Thread(r, "EasyTierMonitor").apply {
            isDaemon = true
            setUncaughtExceptionHandler { t, e ->
                val sw = StringWriter()
                e.printStackTrace(PrintWriter(sw))
                AppLogger.fatal(TAG, "Uncaught in monitor thread ${t.name}: ${sw}")
            }
        }
    }
    private var isMonitoring = false
    private var currentIpv4: String? = null
    private var currentProxyCidrs: List<String> = emptyList()
    private var currentDnsServers: List<String> = emptyList()
    private var currentInstanceName: String? = null
    private var lastNotificationUpdateTime: Long = 0L
    private var vpnServiceIntent: Intent? = null

    init {
        EasyTierVpnService.onRevokeCallback = {
            onVpnRevoked()
        }
    }

    private val monitorRunnable = object : Runnable {
        override fun run() {
            if (!isMonitoring) {
                AppLogger.debug(TAG, "monitorRunnable: isMonitoring=false, aborting")
                return
            }
            AppLogger.debug(TAG, "monitorRunnable: posting to monitorExecutor")
            try {
                val self = this
                monitorExecutor.execute {
                    AppLogger.debug(TAG, "monitorExecutor: task started, calling collectNetworkStatus")
                    try {
                        val json = collectNetworkStatus()
                        AppLogger.debug(TAG, "monitorExecutor: collectNetworkStatus returned, jsonLen=${json?.length ?: 0}")
                        handler.post {
                            if (isMonitoring) {
                                processNetworkStatus(json)
                                AppLogger.debug(TAG, "handler.post: processNetworkStatus returned")
                            }
                        }
                    } catch (e: Exception) {
                        val sw = StringWriter()
                        e.printStackTrace(PrintWriter(sw))
                        AppLogger.error(TAG, "monitorExecutor: collectNetworkStatus exception: ${sw}")
                    }
                    AppLogger.debug(TAG, "monitorExecutor: scheduling next run in ${MONITOR_INTERVAL}ms")
                    handler.postDelayed(self, MONITOR_INTERVAL)
                }
            } catch (e: Exception) {
                val sw = StringWriter()
                e.printStackTrace(PrintWriter(sw))
                AppLogger.error(TAG, "monitorRunnable: execute() failed: ${sw}")
            }
        }
    }

    private fun startMonitoring() {
        if (isMonitoring) {
            AppLogger.warn(TAG, "startMonitoring: already monitoring")
            return
        }
        isMonitoring = true
        AppLogger.info(TAG, "startMonitoring: posting monitorRunnable to handler")
        handler.post(monitorRunnable)
    }

    fun stop() {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            doStop()
        } else {
            handler.post { doStop() }
        }
    }

    private fun doStop() {
        if (!isMonitoring) {
            AppLogger.info(TAG, "stop: not monitoring, still stopping VPN service")
            stopVpnService()
            return
        }
        isMonitoring = false
        AppLogger.info(TAG, "stop: removing callbacks and stopping VPN")
        handler.removeCallbacks(monitorRunnable)
        stopVpnService()
        currentIpv4 = null
        currentProxyCidrs = emptyList()
        currentDnsServers = emptyList()
        currentInstanceName = null
    }

    private fun collectNetworkStatus(): String? {
        val instanceName = currentInstanceName ?: return null
        AppLogger.debug(TAG, "collectNetworkStatus: start, instance=$instanceName")
        try {
            val python = Python.getInstance()
            val module = python.getModule("et_adapters.facade")
            val facade = module.callAttr("get_facade")
            if (facade == null) {
                AppLogger.error(TAG, "collectNetworkStatus: facade is null")
                return null
            }
            val result = facade.callAttr("get_route_info", instanceName)
            if (result == null) {
                AppLogger.debug(TAG, "collectNetworkStatus: get_route_info returned null")
                return null
            }
            val json = result.toString()
            AppLogger.debug(TAG, "collectNetworkStatus: done, jsonLen=${json.length}")
            return json
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "collectNetworkStatus: exception: ${sw}")
            return null
        }
    }

    private fun processNetworkStatus(infosJson: String?) {
        AppLogger.debug(TAG, "processNetworkStatus: start")
        try {
            if (infosJson.isNullOrEmpty() || infosJson == "{}") {
                AppLogger.debug(TAG, "processNetworkStatus: empty result, skipping")
                return
            }

            val root = JSONObject(infosJson)
            val newIpv4 = root.optString("virtual_ipv4", "")
            if (newIpv4.isEmpty()) {
                AppLogger.debug(TAG, "processNetworkStatus: no IPv4 address yet")
                return
            }

            val now = System.currentTimeMillis()
            if (now - lastNotificationUpdateTime >= 60_000) {
                lastNotificationUpdateTime = now
                val upload = root.optString("total_upload", "")
                val download = root.optString("total_download", "")
                val text = buildString {
                    val name = (currentInstanceName ?: "").removeSuffix(".toml")
                    append(name)
                    append("运行中 ")
                    if (upload.isNotEmpty()) {
                        append("↑${upload}")
                    }
                    if (download.isNotEmpty()) {
                        if (upload.isNotEmpty()) append(" ")
                        append("↓${download}")
                    }
                }
                EasyTierVpnService.instance?.updateNotification(text)
                AppLogger.debug(TAG, "processNetworkStatus: updateNotification $text")
            }

            val newProxyCidrs = mutableListOf<String>()
            val routesArr = root.optJSONArray("routes")
            if (routesArr != null) {
                for (i in 0 until routesArr.length()) {
                    val cidr = routesArr.optString(i, null)
                    if (!cidr.isNullOrEmpty()) {
                        newProxyCidrs.add(cidr)
                    }
                }
            }

            val newDnsServers = mutableListOf<String>()
            val dnsArr = root.optJSONArray("dns_servers")
            if (dnsArr != null) {
                for (i in 0 until dnsArr.length()) {
                    val dns = dnsArr.optString(i, null)
                    if (!dns.isNullOrEmpty()) {
                        newDnsServers.add(dns)
                    }
                }
            }

            val ipv4Changed = newIpv4 != currentIpv4
            val cidrsChanged = newProxyCidrs != currentProxyCidrs
            val dnsChanged = newDnsServers != currentDnsServers

            if (ipv4Changed || cidrsChanged || dnsChanged) {
                AppLogger.info(TAG, "Network changed: IPv4=$currentIpv4->$newIpv4, CIDRs=${currentProxyCidrs}->${newProxyCidrs}, DNS=${currentDnsServers}->${newDnsServers}")
                currentIpv4 = newIpv4
                currentProxyCidrs = newProxyCidrs.toList()
                currentDnsServers = newDnsServers.toList()
                restartVpnService(newIpv4, newProxyCidrs, newDnsServers)
                // 重启vpn后，立即重置刷新时间，尽量及时更新流量
                lastNotificationUpdateTime = 0L
            }

            AppLogger.debug(TAG, "processNetworkStatus: done")
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "processNetworkStatus: throwable: ${t.javaClass.name}: ${sw}")
        }
    }

    private fun restartVpnService(ipv4: String, proxyCidrs: List<String>, dnsServers: List<String>) {
        try {
            AppLogger.info(TAG, "Restarting VPN: $ipv4")
            stopVpnService()
            startVpnService(ipv4, proxyCidrs, dnsServers)
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "Restart VPN error: ${sw}")
        }
    }

    private fun startVpnService(ipv4: String, proxyCidrs: List<String>, dnsServers: List<String>) {
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
            intent.putExtra("ipv4_address", ipv4)
            intent.putStringArrayListExtra("proxy_cidrs", ArrayList(proxyCidrs))
            intent.putStringArrayListExtra("dns_servers", ArrayList(dnsServers))
            intent.putExtra("instance_name", currentInstanceName ?: "unknown")

            AppLogger.info(TAG, "startVpnService: calling startService")
            activity.startService(intent)
            vpnServiceIntent = intent

            AppLogger.info(TAG, "VPN started: $ipv4, CIDRs=${proxyCidrs.size}, DNS=${dnsServers.size}")
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "Start VPN error: ${sw}")
        }
    }

    fun onVpnAuthorizationResult(resultCode: Int) {
        if (resultCode == Activity.RESULT_OK) {
            AppLogger.info(TAG, "VPN authorization granted, starting monitoring")
            startMonitoring()
        } else {
            AppLogger.warn(TAG, "VPN authorization denied by user")
        }
    }

    fun start(instanceName: String) {
        if (Looper.myLooper() == Looper.getMainLooper()) {
            doStart(instanceName)
        } else {
            handler.post { doStart(instanceName) }
        }
    }

    private fun doStart(instanceName: String) {
        try {
            AppLogger.info(TAG, "start: instance=$instanceName")
            currentInstanceName = instanceName
            val prepareIntent = VpnService.prepare(activity)
            if (prepareIntent != null) {
                AppLogger.info(TAG, "start: VPN not authorized, showing dialog")
                activity.startActivityForResult(prepareIntent, VPN_REQUEST_CODE)
            } else {
                AppLogger.info(TAG, "start: VPN already authorized, starting monitoring")
                startMonitoring()
            }
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "start error: ${sw}")
        }
    }

    private fun stopVpnService() {
        try {
            EasyTierVpnService.requestStop()
            AppLogger.info(TAG, "Called EasyTierVpnService.requestStop()")

            if (vpnServiceIntent != null) {
                val stopped = activity.stopService(vpnServiceIntent)
                AppLogger.info(TAG, "stopService result=$stopped, intent=$vpnServiceIntent")
            } else {
                val intent = Intent(activity, EasyTierVpnService::class.java)
                val stopped = activity.stopService(intent)
                AppLogger.info(TAG, "stopService(fallback) result=$stopped")
            }
            vpnServiceIntent = null
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "Stop VPN error: ${sw}")
        }
    }

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

    fun installApk(filePath: String) {
        AppLogger.info(TAG, "installApk: $filePath")
        handler.post {
            try {
                val apkFile = File(filePath)
                if (!apkFile.exists()) {
                    AppLogger.error(TAG, "installApk: file not found: $filePath")
                    return@post
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
    }

    private fun onVpnRevoked() {
        AppLogger.info(TAG, "onVpnRevoked: VPN was revoked by another app")
        if (isMonitoring) {
            isMonitoring = false
            handler.removeCallbacks(monitorRunnable)
            AppLogger.info(TAG, "onVpnRevoked: monitoring stopped")
        }
        val instanceName = currentInstanceName
        currentIpv4 = null
        currentProxyCidrs = emptyList()
        currentDnsServers = emptyList()
        currentInstanceName = null
        vpnServiceIntent = null

        if (instanceName != null) {
            monitorExecutor.execute {
                try {
                    AppLogger.info(TAG, "onVpnRevoked: stopping Python network instance $instanceName")
                    val python = Python.getInstance()
                    val module = python.getModule("et_adapters.facade")
                    val facade = module.callAttr("get_facade")
                    if (facade != null) {
                        facade.callAttr("stop_network", instanceName)
                        AppLogger.info(TAG, "onVpnRevoked: Python network instance stopped")
                    }
                } catch (e: Exception) {
                    AppLogger.error(TAG, "onVpnRevoked: stop_network failed: ${e.message}")
                }
            }
        }
    }
}