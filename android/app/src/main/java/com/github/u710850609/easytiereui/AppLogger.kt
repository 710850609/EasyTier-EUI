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

    var logDir: File? = null
    var minLevel: Level = Level.DEBUG

    // 每个文件最大大小，5MB
    private const val MAX_FILE_SIZE = 5L * 1024 * 1024
    // 最大文件数量，50个
    private const val MAX_FILE_COUNT = 50
    // 最大保留天数，7天
    private const val MAX_DAYS = 7
    private val dateFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
    private val tsFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())

    @Volatile private var currentLogFile: File? = null
    private val lock = Any()

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
        val ts = tsFormat.format(Date())
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
            synchronized(lock) {
                val file = ensureLogFile()
                if (file.length() >= MAX_FILE_SIZE) {
                    currentLogFile = null
                }
                val target = ensureLogFile()
                target.appendText(line + "\r\n")
            }
        } catch (_: Exception) {}
    }

    private fun ensureLogFile(): File {
        val dir = logDir ?: return File("/dev/null")
        val today = dateFormat.format(Date())

        currentLogFile?.let { f ->
            val name = f.nameWithoutExtension
            if (name.startsWith("app_$today")) return f
        }

        dir.mkdirs()

        var index = 0
        var file: File
        do {
            val suffix = if (index == 0) "" else "_$index"
            file = File(dir, "app_$today$suffix.log")
            index++
        } while (file.exists() && file.length() >= MAX_FILE_SIZE)

        currentLogFile = file
        cleanOldLogs()
        return file
    }

    private fun cleanOldLogs() {
        val dir = logDir ?: return
        val logFiles = dir.listFiles { f -> f.name.startsWith("app_") && f.name.endsWith(".log") }
            ?: return

        val cutoff = System.currentTimeMillis() - MAX_DAYS * 24L * 3600 * 1000

        logFiles.forEach { file ->
            if (file.lastModified() < cutoff) {
                file.delete()
            }
        }

        val remaining = logFiles.filter { it.exists() }.sortedByDescending { it.lastModified() }
        remaining.drop(MAX_FILE_COUNT).forEach { it.delete() }
    }
}