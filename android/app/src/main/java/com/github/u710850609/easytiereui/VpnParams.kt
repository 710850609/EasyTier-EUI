package com.github.u710850609.easytiereui

data class VpnParams(
    val instanceNames: List<String>,
    val ipv4s: List<String>,
    val ipv6s: List<String>,
    val proxyCidrs: List<String>,
    val dnsServers: List<String>,
    val notificationTitle: String,
    val notificationText: String,
    val mtu: Int = 1400
) : java.io.Serializable