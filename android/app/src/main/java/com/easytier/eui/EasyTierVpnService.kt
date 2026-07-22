package com.easytier.eui

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
import kotlin.concurrent.thread

class EasyTierVpnService : VpnService() {

    private var vpnInterface: ParcelFileDescriptor? = null
    private var isRunning = false
    private var instanceName: String? = null

    companion object {
        private const val TAG = "EasyTierVpnService"
        const val CHANNEL_ID = "easytier_vpn_channel"
        const val NOTIFICATION_ID = 1
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        Log.d(TAG, "VPN Service created")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val ipv4Address = intent?.getStringExtra("ipv4_address")
        val proxyCidrs = intent?.getStringArrayListExtra("proxy_cidrs") ?: arrayListOf()
        instanceName = intent?.getStringExtra("instance_name")

        if (ipv4Address == null || instanceName == null) {
            Log.e(TAG, "Missing parameters: ipv4Address=$ipv4Address, instanceName=$instanceName")
            stopSelf()
            return START_NOT_STICKY
        }

        Log.i(TAG, "Starting VPN - IPv4: $ipv4Address, Proxy CIDRs: $proxyCidrs, Instance: $instanceName")

        thread {
            try {
                setupVpnInterface(ipv4Address, proxyCidrs)
            } catch (t: Throwable) {
                Log.e(TAG, "VPN setup failed", t)
                stopSelf()
            }
        }

        return START_STICKY
    }

    private fun setupVpnInterface(ipv4Address: String, proxyCidrs: List<String>) {
        try {
            val (ip, networkLength) = parseIpv4Address(ipv4Address)

            val builder = Builder()
            builder.setSession("EasyTier VPN")
                .addAddress(ip, networkLength)
                .addDnsServer("223.5.5.5")
                .addDnsServer("114.114.114.114")
                .addDisallowedApplication(packageName)

            proxyCidrs.forEach { cidr ->
                try {
                    val (routeIp, routeLength) = parseCidr(cidr)
                    builder.addRoute(routeIp, routeLength)
                    Log.d(TAG, "Added route: $routeIp/$routeLength")
                } catch (e: Exception) {
                    Log.w(TAG, "Failed to parse CIDR: $cidr", e)
                }
            }

            vpnInterface = builder.establish()

            if (vpnInterface == null) {
                Log.e(TAG, "Failed to create VPN interface")
                return
            }

            Log.i(TAG, "VPN interface created successfully")

            startForeground(NOTIFICATION_ID, buildNotification("EasyTier VPN Connected"))

            instanceName?.let { name ->
                val fd = vpnInterface!!.fd
                // !! 只是对 Kotlin 编译器声明"这个返回值不会是 null"
                val bridge = Python.getInstance().getModule("utils.et_bridge")!!.get("et_bridge")!!
                val result = bridge.callAttr("set_tun_fd", name, fd).toInt()
                if (result == 0) {
                    Log.i(TAG, "TUN fd set successfully: $fd")
                } else {
                    Log.e(TAG, "TUN fd set failed: $result")
                }
            }

            isRunning = true

            while (isRunning && vpnInterface != null) {
                Thread.sleep(1000)
            }
        } catch (t: Throwable) {
            Log.e(TAG, "Error during VPN interface setup", t)
        } finally {
            cleanup()
        }
    }

    private fun parseIpv4Address(ipv4Address: String): Pair<String, Int> {
        return if (ipv4Address.contains("/")) {
            val parts = ipv4Address.split("/")
            Pair(parts[0], parts[1].toInt())
        } else {
            Pair(ipv4Address, 24)
        }
    }

    private fun parseCidr(cidr: String): Pair<String, Int> {
        val parts = cidr.split("/")
        if (parts.size != 2) {
            throw IllegalArgumentException("Invalid CIDR format: $cidr")
        }
        return Pair(parts[0], parts[1].toInt())
    }

    private fun cleanup() {
        isRunning = false
        vpnInterface?.close()
        vpnInterface = null
        Log.i(TAG, "VPN interface cleaned up")
    }

    private fun buildNotification(text: String): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("EasyTier")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_share)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID, "EasyTier VPN", NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "EasyTier VPN Status"
                setShowBadge(false)
            }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        cleanup()
        super.onDestroy()
        Log.d(TAG, "VPN Service destroyed")
    }
}