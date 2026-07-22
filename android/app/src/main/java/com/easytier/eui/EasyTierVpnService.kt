package com.easytier.eui

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
import kotlin.concurrent.thread
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class EasyTierVpnService : VpnService() {

    private var vpnInterface: ParcelFileDescriptor? = null
    private var isRunning = false
    private var instanceName: String? = null
    private val handler = Handler(Looper.getMainLooper())

    companion object {
        private const val TAG = "EasyTierVpnService"
        const val CHANNEL_ID = "easytier_vpn_channel"
        const val NOTIFICATION_ID = 1

        var logFile: File? = null

        fun logToFile(level: String, msg: String) {
            val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()).format(Date())
            val line = "$ts [$level] [EasyTierVpnService] $msg"
            Log.println(
                when (level) { "ERROR" -> Log.ERROR; "WARN" -> Log.WARN; "FATAL" -> Log.ERROR; else -> Log.DEBUG },
                TAG, msg
            )
            try {
                logFile?.appendText(line + "\r\n")
            } catch (_: Exception) {}
        }
    }

    override fun onCreate() {
        super.onCreate()
        try {
            createNotificationChannel()
        } catch (e: Exception) {
            Log.e(TAG, "Failed to create notification channel", e)
        }
        logToFile("INFO", "VPN Service created")
        Log.d(TAG, "VPN Service created")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        logToFile("INFO", "onStartCommand: flags=$flags, startId=$startId")
        val ipv4Address = intent?.getStringExtra("ipv4_address")
        val proxyCidrs = intent?.getStringArrayListExtra("proxy_cidrs") ?: arrayListOf()
        instanceName = intent?.getStringExtra("instance_name")

        if (ipv4Address == null || instanceName == null) {
            logToFile("ERROR", "Missing parameters: ipv4Address=$ipv4Address, instanceName=$instanceName")
            Log.e(TAG, "Missing parameters: ipv4Address=$ipv4Address, instanceName=$instanceName")
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, buildNotification("EasyTier VPN Starting..."))

        logToFile("INFO", "Starting VPN - IPv4: $ipv4Address, Proxy CIDRs: $proxyCidrs, Instance: $instanceName")
        Log.i(TAG, "Starting VPN - IPv4: $ipv4Address, Proxy CIDRs: $proxyCidrs, Instance: $instanceName")

        try {
            val pfd = createVpnInterface(ipv4Address, proxyCidrs)
            if (pfd == null) {
                logToFile("ERROR", "Failed to create VPN interface (pfd is null)")
                Log.e(TAG, "Failed to create VPN interface")
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }

            vpnInterface = pfd
            startForeground(NOTIFICATION_ID, buildNotification("EasyTier VPN Connected"))
            logToFile("INFO", "VPN interface created, fd=${pfd.fd}")

            val name = instanceName!!
            val fd = pfd.fd
            thread {
                try {
                    logToFile("INFO", "Background thread: setting TUN fd=$fd for instance=$name")
                    setTunFd(name, fd)
                    logToFile("INFO", "Background thread: entering keepalive loop")
                    runKeepAliveLoop()
                } catch (t: Throwable) {
                    val sw = StringWriter()
                    t.printStackTrace(PrintWriter(sw))
                    logToFile("ERROR", "VPN background error: ${sw}")
                    Log.e(TAG, "VPN background error", t)
                } finally {
                    logToFile("INFO", "VPN background thread ending, cleaning up")
                    handler.post {
                        stopForeground(STOP_FOREGROUND_REMOVE)
                        stopSelf()
                    }
                }
            }
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "VPN setup failed: ${sw}")
            Log.e(TAG, "VPN setup failed", t)
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }

        return START_STICKY
    }

    private fun createVpnInterface(ipv4Address: String, proxyCidrs: List<String>): ParcelFileDescriptor? {
        logToFile("INFO", "createVpnInterface: ipv4=$ipv4Address, cidrs=${proxyCidrs.size}")
        val (ip, networkLength) = parseIpv4Address(ipv4Address)
        logToFile("DEBUG", "createVpnInterface: parsed ip=$ip, prefix=$networkLength")

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
                logToFile("DEBUG", "Added route: $routeIp/$routeLength")
                Log.d(TAG, "Added route: $routeIp/$routeLength")
            } catch (e: Exception) {
                logToFile("WARN", "Failed to parse CIDR: $cidr - ${e.message}")
                Log.w(TAG, "Failed to parse CIDR: $cidr", e)
            }
        }

        logToFile("INFO", "createVpnInterface: calling builder.establish()")
        val pfd = builder.establish()
        if (pfd == null) {
            logToFile("ERROR", "createVpnInterface: builder.establish() returned null")
        } else {
            logToFile("INFO", "createVpnInterface: builder.establish() succeeded, fd=${pfd.fd}")
        }
        return pfd
    }

    private fun setTunFd(instanceName: String, fd: Int) {
        try {
            val bridge = Python.getInstance().getModule("utils.et_bridge")!!.get("et_bridge")!!
            val result = bridge.callAttr("set_tun_fd", instanceName, fd).toInt()
            if (result == 0) {
                logToFile("INFO", "TUN fd set successfully: $fd")
                Log.i(TAG, "TUN fd set successfully: $fd")
            } else {
                logToFile("ERROR", "TUN fd set failed: $result")
                Log.e(TAG, "TUN fd set failed: $result")
            }
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            logToFile("ERROR", "TUN fd set error: ${sw}")
            Log.e(TAG, "TUN fd set error", t)
        }
    }

    private fun runKeepAliveLoop() {
        isRunning = true
        logToFile("INFO", "Keep-alive loop started")
        while (isRunning && vpnInterface != null) {
            try {
                Thread.sleep(1000)
            } catch (e: InterruptedException) {
                logToFile("INFO", "Keep-alive loop interrupted")
                break
            }
        }
        logToFile("INFO", "Keep-alive loop ended (isRunning=$isRunning, vpnInterface=${if (vpnInterface != null) "present" else "null"})")
        Log.i(TAG, "Keep-alive loop ended")
    }

    private fun parseIpv4Address(ipv4Address: String): Pair<String, Int> {
        return try {
            if (ipv4Address.contains("/")) {
                val parts = ipv4Address.split("/")
                Pair(parts[0], parts[1].toInt())
            } else {
                Pair(ipv4Address, 24)
            }
        } catch (e: Exception) {
            logToFile("ERROR", "parseIpv4Address failed for '$ipv4Address': ${e.message}")
            throw e
        }
    }

    private fun parseCidr(cidr: String): Pair<String, Int> {
        return try {
            val parts = cidr.split("/")
            if (parts.size != 2) {
                throw IllegalArgumentException("Invalid CIDR format: $cidr")
            }
            Pair(parts[0], parts[1].toInt())
        } catch (e: Exception) {
            logToFile("ERROR", "parseCidr failed for '$cidr': ${e.message}")
            throw e
        }
    }

    private fun cleanup() {
        isRunning = false
        vpnInterface?.close()
        vpnInterface = null
        logToFile("INFO", "VPN interface cleaned up")
        Log.i(TAG, "VPN interface cleaned up")
    }

    private fun buildNotification(text: String): Notification {
        return try {
            val pendingIntent = PendingIntent.getActivity(
                this, 0,
                Intent(this, MainActivity::class.java),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            )
            NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("EasyTier")
                .setContentText(text)
                .setSmallIcon(android.R.drawable.ic_menu_share)
                .setContentIntent(pendingIntent)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build()
        } catch (e: Exception) {
            logToFile("ERROR", "buildNotification failed: ${e.message}")
            Log.e(TAG, "buildNotification failed", e)
            NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("EasyTier")
                .setContentText(text)
                .setSmallIcon(android.R.drawable.ic_menu_share)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build()
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                val channel = NotificationChannel(
                    CHANNEL_ID, "EasyTier VPN", NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "EasyTier VPN Status"
                    setShowBadge(false)
                }
                getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
                logToFile("INFO", "Notification channel created")
            } catch (e: Exception) {
                logToFile("ERROR", "createNotificationChannel failed: ${e.message}")
                Log.e(TAG, "createNotificationChannel failed", e)
            }
        }
    }

    override fun onDestroy() {
        logToFile("INFO", "onDestroy: cleaning up")
        cleanup()
        stopForeground(STOP_FOREGROUND_REMOVE)
        super.onDestroy()
        logToFile("INFO", "VPN Service destroyed")
        Log.d(TAG, "VPN Service destroyed")
    }
}