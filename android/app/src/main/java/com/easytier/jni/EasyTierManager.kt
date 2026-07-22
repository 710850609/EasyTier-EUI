package com.easytier.jni

import android.app.Activity
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.chaquo.python.Python
import com.easytier.eui.EasyTierVpnService
import org.json.JSONArray
import org.json.JSONObject

class EasyTierManager(
    private val activity: Activity,
) {
    companion object {
        private const val TAG = "EasyTierManager"
        private const val MONITOR_INTERVAL = 3000L
    }

    private val handler = Handler(Looper.getMainLooper())
    private var isMonitoring = false
    private var currentIpv4: String? = null
    private var currentProxyCidrs: List<String> = emptyList()
    private var currentInstanceName: String? = null
    private var vpnServiceIntent: Intent? = null

    private val monitorRunnable = object : Runnable {
        override fun run() {
            if (isMonitoring) {
                monitorNetworkStatus()
                handler.postDelayed(this, MONITOR_INTERVAL)
            }
        }
    }

    fun startMonitoring() {
        if (isMonitoring) {
            Log.w(TAG, "Already monitoring")
            return
        }
        isMonitoring = true
        Log.i(TAG, "Monitoring started")
        handler.post(monitorRunnable)
    }

    fun stopMonitoring() {
        if (!isMonitoring) {
            return
        }
        isMonitoring = false
        handler.removeCallbacks(monitorRunnable)
        stopVpnService()
        currentIpv4 = null
        currentProxyCidrs = emptyList()
        currentInstanceName = null
        Log.i(TAG, "Monitoring stopped")
    }

    private fun monitorNetworkStatus() {
        try {
            val infosJson = try {
                val bridge = Python.getInstance().getModule("et_bridge").get("et_bridge")
                bridge.callAttr("collect_network_infos_json", 10).toString()
            } catch (e: Exception) {
                Log.w(TAG, "Python FFI call failed", e)
                null
            }
            if (infosJson.isNullOrEmpty() || infosJson == "{}") {
                if (currentInstanceName != null) {
                    stopVpnService()
                    currentInstanceName = null
                }
                return
            }

            val root = JSONObject(infosJson)
            val map = root.optJSONObject("map") ?: return

            if (currentInstanceName != null) {
                val info = map.optJSONObject(currentInstanceName)
                if (info == null || !info.optBoolean("running", false)) {
                    Log.w(TAG, "Instance $currentInstanceName stopped, stopping VPN")
                    stopVpnService()
                    currentInstanceName = null
                    currentIpv4 = null
                    currentProxyCidrs = emptyList()
                }
            }

            if (currentInstanceName == null) {
                for (key in map.keys()) {
                    val info = map.optJSONObject(key) ?: continue
                    if (info.optBoolean("running", false)) {
                        currentInstanceName = key
                        Log.i(TAG, "Discovered running instance: $key")
                        break
                    }
                }
            }

            if (currentInstanceName == null) return

            val networkInfo = map.optJSONObject(currentInstanceName) ?: return
            if (!networkInfo.optBoolean("running", false)) return

            val myNodeInfo = networkInfo.optJSONObject("my_node_info")
            val virtualIpv4 = myNodeInfo?.optJSONObject("virtual_ipv4")
            val newIpv4 = parseIpv4Inet(virtualIpv4)

            if (newIpv4 == null) {
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
                Log.i(TAG, "Network changed: IPv4=$currentIpv4->$newIpv4, CIDRs=${currentProxyCidrs.size}->${newProxyCidrs.size}")
                currentIpv4 = newIpv4
                currentProxyCidrs = newProxyCidrs.toList()
                restartVpnService(newIpv4, newProxyCidrs)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Monitor error", e)
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
            stopVpnService()
            startVpnService(ipv4, proxyCidrs)
        } catch (e: Exception) {
            Log.e(TAG, "Restart VPN error", e)
        }
    }

    private fun startVpnService(ipv4: String, proxyCidrs: List<String>) {
        try {
            val intent = Intent(activity, EasyTierVpnService::class.java)
            intent.putExtra("ipv4_address", ipv4)
            intent.putStringArrayListExtra("proxy_cidrs", ArrayList(proxyCidrs))
            intent.putExtra("instance_name", currentInstanceName ?: "unknown")

            activity.startService(intent)
            vpnServiceIntent = intent

            Log.i(TAG, "VPN started: $ipv4, CIDRs=${proxyCidrs.size}")
        } catch (e: Exception) {
            Log.e(TAG, "Start VPN error", e)
        }
    }

    private fun stopVpnService() {
        try {
            vpnServiceIntent?.let { intent ->
                activity.stopService(intent)
                Log.i(TAG, "VPN stopped")
            }
            vpnServiceIntent = null
        } catch (e: Exception) {
            Log.e(TAG, "Stop VPN error", e)
        }
    }

    fun isMonitoring(): Boolean = isMonitoring
}