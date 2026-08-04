package com.github.u710850609.easytiereui

import android.util.Log
import java.io.File
import java.io.PrintWriter
import java.io.StringWriter
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object AppLogger {

    enum class Level(val priority: Int) {
        DEBUG(3),
        INFO(4),
        WARN(5),
        ERROR(6),
        FATAL(7),
        OFF(Int.MAX_VALUE)
    }

    var logFile: File? = null
    var minLevel: Level = Level.DEBUG

    fun debug(tag: String, msg: String) = log(Level.DEBUG, tag, msg)
    fun info(tag: String, msg: String) = log(Level.INFO, tag, msg)
    fun warn(tag: String, msg: String) = log(Level.WARN, tag, msg)
    fun error(tag: String, msg: String) = log(Level.ERROR, tag, msg)
    fun fatal(tag: String, msg: String) = log(Level.FATAL, tag, msg)

    fun error(tag: String, msg: String, t: Throwable) {
        val sw = StringWriter()
        t.printStackTrace(PrintWriter(sw))
        log(Level.ERROR, tag, "$msg\n${sw}")
    }

    private fun log(level: Level, tag: String, msg: String) {
        if (level.priority < minLevel.priority) return
        val ts = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault()).format(Date())
        val line = "$ts [$level] [$tag] $msg"
        Log.println(
            when (level) {
                Level.ERROR, Level.FATAL -> Log.ERROR
                Level.WARN -> Log.WARN
                Level.INFO -> Log.INFO
                else -> Log.DEBUG
            },
            tag, msg
        )
        try {
            logFile?.appendText(line + "\r\n")
        } catch (_: Exception) {}
    }
}