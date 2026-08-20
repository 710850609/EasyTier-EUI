package com.github.u710850609.easytiereui

data class VpnParams(
    val ipv4: String,
    val ipv6: String,
    val proxyCidrs: List<String>,
    val dnsServers: List<String>,
    val notificationTitle: String,
    val notificationText: String
) : java.io.Serializable