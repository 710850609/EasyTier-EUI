package com.github.u710850609.easytiereui

data class VpnParams(
    val instanceName: String,
    val ipv4: String,
    val ipv6: String,
    val proxyCidrs: List<String>,
    val dnsServers: List<String>,
    val notificationTitle: String,
    val notificationText: String,
    val mtu: Int = 1400
) : java.io.Serializable