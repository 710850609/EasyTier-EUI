package com.easytier.eui

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*

class EasyTierVpnService : VpnService() {

    companion object {
        const val ACTION_START = "com.easytier.eui.START_VPN"
        const val ACTION_STOP = "com.easytier.eui.STOP_VPN"
        const val CHANNEL_ID = "easytier_vpn_channel"
        const val NOTIFICATION_ID = 1
        const val VPN_ADDRESS = "10.144.0.1"
        const val VPN_PREFIX_LENGTH = 24
        const val VPN_MTU = 1400
    }

    private var vpnInterface: ParcelFileDescriptor? = null
    @Volatile private var isRunning = false
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startVpn()
            ACTION_STOP -> stopVpn()
        }
        return START_STICKY
    }

    private fun startVpn() {
        val builder = Builder()
            .setSession("EasyTier VPN")
            .addAddress(VPN_ADDRESS, VPN_PREFIX_LENGTH)
            .setMtu(VPN_MTU)
            .setBlocking(false)

        try {
            builder.addDnsServer("114.114.114.114")
            builder.addDnsServer("233.5.5.5")
        } catch (_: Exception) {}

        try {
            builder.addRoute("0.0.0.0", 0)
        } catch (_: Exception) {}

        try {
            builder.addDisallowedApplication(packageName)
        } catch (_: Exception) {}

        vpnInterface = builder.establish() ?: run {
            stopSelf()
            return
        }

        isRunning = true
        startForeground(NOTIFICATION_ID, buildNotification("VPN Connected"))
        startVpnDataForwarding()
    }

    private fun stopVpn() {
        isRunning = false
        scope.cancel()
        try { vpnInterface?.close() } catch (_: Exception) {}
        vpnInterface = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun startVpnDataForwarding() {
        val fd = vpnInterface ?: return
        scope.launch {
            try {
                forwardPackets(fd.fileDescriptor)
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    private fun forwardPackets(fd: java.io.FileDescriptor) {
        val buffer = ByteArray(32767)
        while (isRunning) {
            try {
                val inputStream = java.io.FileInputStream(fd)
                val length = inputStream.read(buffer)
                if (length > 0) {
                    processOutgoingPacket(buffer, length)
                }
            } catch (e: Exception) {
                if (!isRunning) break
            }
        }
    }

    private fun processOutgoingPacket(packet: ByteArray, length: Int) {
        // TODO: 通过 JNI 将数据包发送到 EasyTier 网络层
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
        scope.cancel()
        try { vpnInterface?.close() } catch (_: Exception) {}
        vpnInterface = null
        super.onDestroy()
    }
}