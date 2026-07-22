package com.easytier.jni

import android.app.Activity
import android.content.Intent
import android.net.VpnService
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.chaquo.python.Python
import com.easytier.eui.EasyTierVpnService
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors

class EasyTierManager(
    private val activity: Activity,
    private val logFile: File? = null,
) {
    companion object {
        private const val TAG = "EasyTierManager"
        private const val MONITOR_INTERVAL = 3000L
        const val VPN_REQUEST_CODE = 1001
    }

    private val handler = Handler(Looper.getMainLooper())
    private val monitorExecutor = Executors.newSingleThreadExecutor { r ->
        Thread(r, "EasyTierMonitor").apply {
            isDaemon = true
            setUncaughtExceptionHandler { t, e ->
                val sw = StringWriter()
                e.printStackTrace(PrintWriter(sw))
                val line = "FATAL: Uncaught in monitor thread ${t.name}: ${sw}"
                Log.e(TAG, line, e)
                logToFile("FATAL", line)
            }
        }
    }
    private var isMonitoring = false
    private var currentIpv4: String? = null
    private var currentProxyCidrs: List<String> = emptyList()
    private var currentInstanceName: String? = null
    private var vpnServiceIntent: Intent? = null
    private var pendingVpnIpv4: String? = null
    private var pendingVpnProxyCidrs: List<String> = emptyList()
    private var isVpnAuthorizationPending = false

    private fun logToFile(level: String, msg: String) {
        val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()).format(Date())
        val line = "$ts [$level] [EasyTierManager] $msg"
        Log.println(
            when (level) { "ERROR" -> Log.ERROR; "WARN" -> Log.WARN; "FATAL" -> Log.ERROR; else -> Log.DEBUG },
            TAG, msg
        )
        try {
            logFile?.appendText(line + "\r\n")
        } catch (_: Exception) {}
    }

    private val monitorRunnable = object : Runnable {
        override fun run() {
            if (!isMonitoring) {
                logToFile("DEBUG", "monitorRunnable: isMonitoring=false, aborting")
                return
            }
            logToFile("DEBUG", "monitorRunnable: posting to monitorExecutor")
            try {
                val self = this
                monitorExecutor.execute {
                    logToFile("DEBUG", "monitorExecutor: task started, calling collectNetworkStatus")
                    try {
                        val result = collectNetworkStatus()
                        logToFile("DEBUG", "monitorExecutor: collectNetworkStatus returned, jsonLen=${result.infosJson?.length ?: 0}")
                        handler.post {
                            if (isMonitoring) {
                                processNetworkStatus(result)
                                logToFile("DEBUG", "handler.post: processNetworkStatus returned")
                            }
                        }
                    } catch (e: Exception) {
                        val sw = StringWriter()
                        e.printStackTrace(PrintWriter(sw))
                        logToFile("ERROR", "monitorExecutor: collectNetworkStatus exception: ${sw}")
                        Log.e(TAG, "Monitor background error", e)
                    }
                    logToFile("DEBUG", "monitorExecutor: scheduling next run in ${MONITOR_INTERVAL}ms")
                    handler.postDelayed(self, MONITOR_INTERVAL)
                }
            } catch (e: Exception) {
                val sw = StringWriter()
                e.printStackTrace(PrintWriter(sw))
                logToFile("ERROR", "monitorRunnable: execute() failed: ${sw}")
                Log.e(TAG, "monitorRunnable execute failed", e)
            }
        }
    }

    fun startMonitoring() {
        if (isMonitoring) {
            logToFile("WARN", "startMonitoring: already monitoring")
            Log.w(TAG, "Already monitoring")
            return
        }
        isMonitoring = true
        logToFile("INFO", "startMonitoring: posting monitorRunnable to handler")
        Log.i(TAG, "Monitoring started")
        handler.post(monitorRunnable)
    }

    fun stopMonitoring() {
        if (!isMonitoring) {
            return
        }
        isMonitoring = false
        logToFile("INFO", "stopMonitoring: removing callbacks and stopping VPN")
        handler.removeCallbacks(monitorRunnable)
        stopVpnService()
        currentIpv4 = null
        currentProxyCidrs = emptyList()
        currentInstanceName = null
        Log.i(TAG, "Monitoring stopped")
    }

    private data class NetworkStatus(
        val infosJson: String?,
        val error: String?
    )

    private fun collectNetworkStatus(): NetworkStatus {
        logToFile("DEBUG", "collectNetworkStatus: start")
        try {
            logToFile("DEBUG", "collectNetworkStatus: Python.getInstance()")
            val python = Python.getInstance()
            logToFile("DEBUG", "collectNetworkStatus: getModule(utils.et_bridge)")
            val module = python.getModule("utils.et_bridge")
            if (module == null) {
                logToFile("ERROR", "collectNetworkStatus: module utils.et_bridge is null")
                return NetworkStatus(null, null)
            }
            logToFile("DEBUG", "collectNetworkStatus: get(et_bridge)")
            val bridge = module.get("et_bridge")
            if (bridge == null) {
                logToFile("ERROR", "collectNetworkStatus: et_bridge is null")
                return NetworkStatus(null, null)
            }
            logToFile("DEBUG", "collectNetworkStatus: callAttr(collect_network_infos_json, 10)")
            val json = bridge.callAttr("collect_network_infos_json", 10).toString()
            logToFile("DEBUG", "collectNetworkStatus: done, jsonLen=${json.length}")
            return NetworkStatus(json, null)
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "collectNetworkStatus: exception: ${sw}")
            Log.w(TAG, "Python FFI call failed", e)
            return NetworkStatus(null, null)
        }
    }

    private fun processNetworkStatus(status: NetworkStatus) {
        logToFile("DEBUG", "processNetworkStatus: start")
        try {
            val infosJson = status.infosJson
            logToFile("DEBUG", "processNetworkStatus: infosJson=${infosJson?.take(200)}")
            if (infosJson.isNullOrEmpty() || infosJson == "{}") {
                if (currentInstanceName != null) {
                    logToFile("INFO", "processNetworkStatus: no instances, stopping VPN")
                    stopVpnService()
                    currentInstanceName = null
                }
                logToFile("DEBUG", "processNetworkStatus: empty result, returning")
                return
            }

            logToFile("DEBUG", "processNetworkStatus: parsing JSONObject")
            val root = JSONObject(infosJson)
            logToFile("DEBUG", "processNetworkStatus: getting map")
            val map = root.optJSONObject("map")
            if (map == null) {
                logToFile("DEBUG", "processNetworkStatus: map is null, returning")
                return
            }
            logToFile("DEBUG", "processNetworkStatus: map keys=${map.keys().asSequence().toList()}")

            if (currentInstanceName != null) {
                logToFile("DEBUG", "processNetworkStatus: checking current instance $currentInstanceName")
                val info = map.optJSONObject(currentInstanceName)
                if (info == null || !info.optBoolean("running", false)) {
                    logToFile("WARN", "Instance $currentInstanceName stopped, stopping VPN")
                    Log.w(TAG, "Instance $currentInstanceName stopped, stopping VPN")
                    stopVpnService()
                    currentInstanceName = null
                    currentIpv4 = null
                    currentProxyCidrs = emptyList()
                }
            }

            if (currentInstanceName == null) {
                logToFile("DEBUG", "processNetworkStatus: looking for running instance")
                for (key in map.keys()) {
                    val info = map.optJSONObject(key) ?: continue
                    if (info.optBoolean("running", false)) {
                        currentInstanceName = key
                        logToFile("INFO", "Discovered running instance: $key")
                        Log.i(TAG, "Discovered running instance: $key")
                        break
                    }
                }
            }

            if (currentInstanceName == null) {
                logToFile("DEBUG", "processNetworkStatus: no running instance, returning")
                return
            }

            logToFile("DEBUG", "processNetworkStatus: getting networkInfo for $currentInstanceName")
            val networkInfo = map.optJSONObject(currentInstanceName) ?: return
            if (!networkInfo.optBoolean("running", false)) return

            val myNodeInfo = networkInfo.optJSONObject("my_node_info")
            val virtualIpv4 = myNodeInfo?.optJSONObject("virtual_ipv4")
            val newIpv4 = parseIpv4Inet(virtualIpv4)

            if (newIpv4 == null) {
                logToFile("DEBUG", "No IPv4 yet")
                Log.d(TAG, "No IPv4 yet")
                return
            }

            val newProxyCidrs = mutableListOf<String>()
            val routes = networkInfo.optJSONArray("routes")
            if (routes != null) {
                for (i in 0 until routes.length()) {
                    val route = routes.getJSONObject(i)
                    val cidrs = route.optJSONArray("proxy_cidrs")
                    if (cidrs != null) {
                        for (j in 0 until cidrs.length()) {
                            newProxyCidrs.add(cidrs.getString(j))
                        }
                    }
                }
            }

            val ipv4Changed = newIpv4 != currentIpv4
            val cidrsChanged = newProxyCidrs != currentProxyCidrs

            if (ipv4Changed || cidrsChanged) {
                logToFile("INFO", "Network changed: IPv4=$currentIpv4->$newIpv4, CIDRs=${currentProxyCidrs.size}->${newProxyCidrs.size}")
                Log.i(TAG, "Network changed: IPv4=$currentIpv4->$newIpv4, CIDRs=${currentProxyCidrs.size}->${newProxyCidrs.size}")
                currentIpv4 = newIpv4
                currentProxyCidrs = newProxyCidrs.toList()
                restartVpnService(newIpv4, newProxyCidrs)
            }
            logToFile("DEBUG", "processNetworkStatus: done")
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "processNetworkStatus: throwable: ${t.javaClass.name}: ${sw}")
            Log.e(TAG, "Monitor error", t)
        }
    }

    private fun parseIpv4Inet(inet: JSONObject?): String? {
        if (inet == null) return null
        val address = inet.optJSONObject("address") ?: return null
        val addr = address.optInt("addr", -1)
        if (addr < 0) return null
        val networkLength = inet.optInt("network_length", 24)

        val ip = "${(addr shr 24) and 0xFF}.${(addr shr 16) and 0xFF}.${(addr shr 8) and 0xFF}.${addr and 0xFF}"
        return "$ip/$networkLength"
    }

    private fun restartVpnService(ipv4: String, proxyCidrs: List<String>) {
        try {
            logToFile("INFO", "Restarting VPN: $ipv4")
            stopVpnService()
            startVpnService(ipv4, proxyCidrs)
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "Restart VPN error: ${sw}")
            Log.e(TAG, "Restart VPN error", e)
        }
    }

    private fun startVpnService(ipv4: String, proxyCidrs: List<String>) {
        if (isVpnAuthorizationPending) {
            logToFile("WARN", "VPN authorization already pending, queuing")
            Log.w(TAG, "VPN authorization already pending, queuing request")
            pendingVpnIpv4 = ipv4
            pendingVpnProxyCidrs = proxyCidrs
            return
        }

        try {
            val prepareIntent = VpnService.prepare(activity)
            if (prepareIntent != null) {
                logToFile("INFO", "VPN not authorized, requesting user permission")
                Log.i(TAG, "VPN not authorized, requesting user permission")
                isVpnAuthorizationPending = true
                pendingVpnIpv4 = ipv4
                pendingVpnProxyCidrs = proxyCidrs
                activity.startActivityForResult(prepareIntent, VPN_REQUEST_CODE)
                return
            }

            doStartVpnService(ipv4, proxyCidrs)
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "Start VPN error: ${sw}")
            Log.e(TAG, "Start VPN error", e)
        }
    }

    private fun doStartVpnService(ipv4: String, proxyCidrs: List<String>) {
        try {
            EasyTierVpnService.logFile = logFile
            val intent = Intent(activity, EasyTierVpnService::class.java)
            intent.putExtra("ipv4_address", ipv4)
            intent.putStringArrayListExtra("proxy_cidrs", ArrayList(proxyCidrs))
            intent.putExtra("instance_name", currentInstanceName ?: "unknown")

            activity.startService(intent)
            vpnServiceIntent = intent

            logToFile("INFO", "VPN started: $ipv4, CIDRs=${proxyCidrs.size}")
            Log.i(TAG, "VPN started: $ipv4, CIDRs=${proxyCidrs.size}")
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "Start VPN error: ${sw}")
            Log.e(TAG, "Start VPN error", e)
        }
    }

    fun onVpnAuthorizationResult(resultCode: Int) {
        isVpnAuthorizationPending = false
        if (resultCode == Activity.RESULT_OK) {
            logToFile("INFO", "VPN authorization granted")
            Log.i(TAG, "VPN authorization granted")
            val ipv4 = pendingVpnIpv4
            val proxyCidrs = pendingVpnProxyCidrs
            pendingVpnIpv4 = null
            pendingVpnProxyCidrs = emptyList()
            if (ipv4 != null) {
                doStartVpnService(ipv4, proxyCidrs)
            }
        } else {
            logToFile("WARN", "VPN authorization denied by user")
            Log.w(TAG, "VPN authorization denied by user")
            pendingVpnIpv4 = null
            pendingVpnProxyCidrs = emptyList()
        }
    }

    private fun stopVpnService() {
        try {
            if (vpnServiceIntent != null) {
                activity.stopService(vpnServiceIntent)
                logToFile("INFO", "VPN stopped")
                Log.i(TAG, "VPN stopped")
            } else {
                val intent = Intent(activity, EasyTierVpnService::class.java)
                activity.stopService(intent)
                logToFile("INFO", "VPN stopped (fallback)")
                Log.i(TAG, "VPN stopped (fallback intent)")
            }
            vpnServiceIntent = null
        } catch (e: Exception) {
            val sw = StringWriter()
            e.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "Stop VPN error: ${sw}")
            Log.e(TAG, "Stop VPN error", e)
        }
    }

    fun isMonitoring(): Boolean = isMonitoring
}