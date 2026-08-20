package com.github.u710850609.easytiereui

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.ConnectivityManager
import android.net.VpnService
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
import kotlin.concurrent.thread
import java.io.PrintWriter
import java.io.StringWriter

class EasyTierVpnService : VpnService() {

    private var vpnInterface: ParcelFileDescriptor? = null
    private var isRunning = false
    private var instanceName: String? = null
    private val handler = Handler(Looper.getMainLooper())

    companion object {
        private const val TAG = "EasyTierVpnService"
        const val CHANNEL_ID = "easytier_eui_vpn_channel"
        const val NOTIFICATION_ID = 1

        private val DISALLOWED_APPS = listOf(
            "com.android.phone",                     // 电话/VoLTE/VoWiFi 服务
            "com.android.captiveportallogin",        // 网络认证门户检测
            "com.android.settings",                  // 系统设置
            "com.huawei.android.pushagent",          // 华为推送
            "com.xiaomi.xmsf",                       // 小米推送
            "com.heytap.mcs",                        // OPPO 推送
            "com.vivo.push",                         // vivo 推送
            "com.huawei.genexcloud.speedtest"        // 华为网络加速
        )

        var instance: EasyTierVpnService? = null
            private set

        var onRevokeCallback: (() -> Unit)? = null

        fun requestStop() {
            instance?.let { service ->
                AppLogger.info(TAG, "requestStop: cleaning up and stopping")
                service.isRunning = false
                try {
                    service.vpnInterface?.close()
                } catch (e: Exception) {
                    AppLogger.error(TAG, "requestStop: close vpnInterface failed: ${e.message}")
                }
                service.vpnInterface = null
                try {
                    service.stopForeground(STOP_FOREGROUND_REMOVE)
                    AppLogger.info(TAG, "requestStop: stopForeground succeeded")
                } catch (e: Exception) {
                    AppLogger.error(TAG, "requestStop: stopForeground failed: ${e.message}")
                }
                service.stopSelf()
            } ?: AppLogger.warn(TAG, "requestStop: no active instance")
        }
    }

    override fun onCreate() {
        super.onCreate()
        AppLogger.info(TAG, "VPN Service onCreate: start")
        try {
            createNotificationChannel()
            AppLogger.info(TAG, "VPN Service notification channel created")
        } catch (e: Exception) {
            AppLogger.error(TAG, "Failed to create notification channel: ${e.message}")
        }
        instance = this
        AppLogger.info(TAG, "VPN Service created")
    }

    @Suppress("UNCHECKED_CAST")
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        AppLogger.info(TAG, "onStartCommand: flags=$flags, startId=$startId")
        val params = intent?.getSerializableExtra("vpn_params") as? VpnParams
        instanceName = intent?.getStringExtra("instance_name")

        if (params == null || instanceName == null) {
            AppLogger.error(TAG, "Missing parameters: params=$params, instanceName=$instanceName")
            stopSelf()
            return START_NOT_STICKY
        }

        AppLogger.info(TAG, "Starting VPN - IPv4: ${params.ipv4}, IPv6: ${params.ipv6}, Proxy CIDRs: ${params.proxyCidrs}, DNS: ${params.dnsServers}, Instance: $instanceName")

        try {
            val pfd = createVpnInterface(params.ipv4, params.ipv6, params.proxyCidrs, params.dnsServers, params.mtu)
            if (pfd == null) {
                AppLogger.error(TAG, "Failed to create VPN interface (pfd is null)")
                stopSelf()
                return START_NOT_STICKY
            }

            vpnInterface = pfd
            startForeground(NOTIFICATION_ID, buildNotification(params.notificationTitle, params.notificationText))
            AppLogger.info(TAG, "VPN interface created, fd=${pfd.fd}")

            val name = instanceName!!
            val fd = pfd.fd
            thread {
                try {
                    AppLogger.info(TAG, "Background thread: setting TUN fd=$fd for instance=$name")
                    setTunFd(name, fd)
                    AppLogger.info(TAG, "Background thread: entering keepalive loop")
                    runKeepAliveLoop()
                } catch (t: Throwable) {
                    val sw = StringWriter()
                    t.printStackTrace(PrintWriter(sw))
                    AppLogger.error(TAG, "VPN background error: ${sw}")
                } finally {
                    AppLogger.info(TAG, "VPN background thread ending, cleaning up")
                    handler.post {
                        try {
                            stopForeground(STOP_FOREGROUND_REMOVE)
                        } catch (e: Exception) {
                            AppLogger.error(TAG, "stopForeground in finally failed: ${e.message}")
                        }
                        stopSelf()
                    }
                }
            }
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "VPN setup failed: ${sw}")
            try {
                stopForeground(STOP_FOREGROUND_REMOVE)
            } catch (e: Exception) {
                AppLogger.error(TAG, "stopForeground in catch failed: ${e.message}")
            }
            stopSelf()
            return START_NOT_STICKY
        }

        return START_STICKY
    }

    private fun createVpnInterface(ipv4Address: String, ipv6Address: String, proxyCidrs: List<String>, dnsServers: List<String>, mtu: Int): ParcelFileDescriptor? {
        AppLogger.info(TAG, "createVpnInterface: ipv4=$ipv4Address, ipv6=$ipv6Address, cidrs=${proxyCidrs.size}, dns=${dnsServers.size}, mtu=$mtu")
        val (ip, networkLength) = parseIpv4Address(ipv4Address)
        AppLogger.debug(TAG, "createVpnInterface: parsed ip=$ip, prefix=$networkLength")

        val builder = Builder()
        builder.setSession("EasyTier-EUI VPN")
            .addAddress(ip, networkLength)
            .also {
                if (ipv6Address.isNotEmpty()) {
                    try {
                        val (ipv6, ipv6Prefix) = parseCidr(ipv6Address)
                        it.addAddress(ipv6, ipv6Prefix)
                        AppLogger.info(TAG, "createVpnInterface: added IPv6 address $ipv6/$ipv6Prefix")
                    } catch (e: Exception) {
                        AppLogger.warn(TAG, "createVpnInterface: failed to parse IPv6 '$ipv6Address': ${e.message}")
                    }
                }
            }
            .addDisallowedApplication(packageName)
            .also {
                DISALLOWED_APPS.forEach { app -> it.addDisallowedApplication(app) }
            }
            .also {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    val cm = getSystemService(ConnectivityManager::class.java)
                    val isMetered = cm.isActiveNetworkMetered
                    AppLogger.debug(TAG, "createVpnInterface: active network isMetered=$isMetered")
                    it.setMetered(isMetered)
                }
            }
            .setMtu(mtu)

        AppLogger.debug(TAG, "createVpnInterface: DNS servers=${dnsServers.joinToString()}")
        dnsServers.forEach { dns -> builder.addDnsServer(dns) }

        proxyCidrs.forEach { cidr ->
            try {
                val (routeIp, routeLength) = parseCidr(cidr)
                builder.addRoute(routeIp, routeLength)
                AppLogger.debug(TAG, "Added route: $routeIp/$routeLength")
            } catch (e: Exception) {
                AppLogger.warn(TAG, "Failed to parse CIDR: $cidr - ${e.message}")
            }
        }

        AppLogger.info(TAG, "createVpnInterface: calling builder.establish()")
        try {
            val pfd = builder.establish()
            if (pfd == null) {
                AppLogger.error(TAG, "createVpnInterface: builder.establish() returned null")
            } else {
                AppLogger.info(TAG, "createVpnInterface: builder.establish() succeeded, fd=${pfd.fd}")
            }
            return pfd
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "createVpnInterface: builder.establish() threw: ${sw}")
            return null
        }
    }

    private fun setTunFd(instanceName: String, fd: Int) {
        try {
            val facade = EasyTierManager.getFacade()
            if (facade == null) {
                AppLogger.error(TAG, "TUN fd set: facade is null")
                return
            }
            val result = facade.callAttr("set_tun_fd", instanceName, fd).toInt()
            if (result == 0) {
                AppLogger.info(TAG, "TUN fd set successfully: $fd")
            } else {
                AppLogger.error(TAG, "TUN fd set failed: $result")
            }
        } catch (t: Throwable) {
            val sw = StringWriter()
            t.printStackTrace(PrintWriter(sw))
            AppLogger.error(TAG, "TUN fd set error: ${sw}")
        }
    }

    private fun runKeepAliveLoop() {
        isRunning = true
        AppLogger.info(TAG, "Keep-alive loop started")
        while (isRunning && vpnInterface != null) {
            try {
                Thread.sleep(1000)
            } catch (e: InterruptedException) {
                AppLogger.info(TAG, "Keep-alive loop interrupted")
                break
            }
        }
        AppLogger.info(TAG, "Keep-alive loop ended (isRunning=$isRunning, vpnInterface=${if (vpnInterface != null) "present" else "null"})")
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
            AppLogger.error(TAG, "parseIpv4Address failed for '$ipv4Address': ${e.message}")
            throw e
        }
    }

    private fun parseCidr(cidr: String): Pair<String, Int> {
        return try {
            val parts = cidr.split("/")
            when (parts.size) {
                2 -> Pair(parts[0], parts[1].toInt())
                1 -> {
                    val defaultPrefix = if (parts[0].contains(":")) 128 else 32
                    Pair(parts[0], defaultPrefix)
                }
                else -> throw IllegalArgumentException("Invalid CIDR format: $cidr")
            }
        } catch (e: Exception) {
            AppLogger.error(TAG, "parseCidr failed for '$cidr': ${e.message}")
            throw e
        }
    }

    private fun cleanup() {
        isRunning = false
        try {
            vpnInterface?.close()
        } catch (e: Exception) {
            AppLogger.error(TAG, "VPN interface close failed: ${e.message}")
        }
        vpnInterface = null
        AppLogger.info(TAG, "VPN interface cleaned up")
    }

    fun updateNotification(title: String, text: String) {
        try {
            val notification = buildNotification(title, text)
            val nm = getSystemService(NotificationManager::class.java)
            nm.notify(NOTIFICATION_ID, notification)
        } catch (e: Exception) {
            AppLogger.error(TAG, "updateNotification failed: ${e.message}")
        }
    }

    private fun buildNotification(title: String, text: String): Notification {
        return try {
            val pendingIntent = PendingIntent.getActivity(
                this, 0,
                Intent(this, MainActivity::class.java),
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
            )
            NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle(title)
                .setContentText(text)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentIntent(pendingIntent)
                .setOngoing(true)
                .setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build()
        } catch (e: Exception) {
            AppLogger.error(TAG, "buildNotification failed: ${e.message}")
            NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("EasyTier-EUI")
                .setContentText("Service Is Running")
                .setSmallIcon(R.drawable.ic_notification)
                .setOngoing(true)
                .setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build()
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            try {
                val channel = NotificationChannel(
                    CHANNEL_ID, "组网服务", NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "组网运行通知"
                    setShowBadge(true)
                }
                getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
                AppLogger.info(TAG, "Notification channel created")
            } catch (e: Exception) {
                AppLogger.error(TAG, "createNotificationChannel failed: ${e.message}")
            }
        }
    }

    override fun onRevoke() {
        AppLogger.info(TAG, "onRevoke: VPN revoked by system (another VPN took over)")
        isRunning = false
        try {
            vpnInterface?.close()
        } catch (e: Exception) {
            AppLogger.error(TAG, "onRevoke: close vpnInterface failed: ${e.message}")
        }
        vpnInterface = null
        try {
            stopForeground(STOP_FOREGROUND_REMOVE)
            AppLogger.info(TAG, "onRevoke: stopForeground succeeded")
        } catch (e: Exception) {
            AppLogger.error(TAG, "onRevoke: stopForeground failed: ${e.message}")
        }
        try {
            onRevokeCallback?.invoke()
        } catch (e: Exception) {
            AppLogger.error(TAG, "onRevoke: callback failed: ${e.message}")
        }
        instance = null
        try {
            super.onRevoke()
        } catch (e: Exception) {
            AppLogger.error(TAG, "onRevoke: super.onRevoke failed: ${e.message}")
        }
        AppLogger.info(TAG, "onRevoke: done")
        stopSelf()
    }

    override fun onDestroy() {
        AppLogger.info(TAG, "onDestroy: start")
        try {
            cleanup()
        } catch (e: Exception) {
            AppLogger.error(TAG, "onDestroy: cleanup failed: ${e.message}")
        }
        try {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } catch (e: Exception) {
            AppLogger.error(TAG, "onDestroy: stopForegroundCompat failed: ${e.message}")
        }
        instance = null
        try {
            super.onDestroy()
        } catch (e: Exception) {
            AppLogger.error(TAG, "onDestroy: super.onDestroy failed: ${e.message}")
        }
        AppLogger.info(TAG, "onDestroy: done")
    }
}