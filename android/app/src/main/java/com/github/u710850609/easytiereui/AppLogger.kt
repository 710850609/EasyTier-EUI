package com.github.u710850609.easytiereui

import android.content.Context
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
    var minLevel: Level = Level.WARN

    /** 功能边界内的统一默认级别（文件缺失/读取失败时）。与后端 Android 默认一致。 */
    private val DEFAULT_LEVEL: Level = Level.WARN

    @Volatile private var initialized = false

    private const val LOG_FILE_NAME = "app_kt.log"
    private const val LOG_FILE_PREFIX = "app_kt_"
    // 每个文件最大大小，5MB
    private const val MAX_FILE_SIZE = 5L * 1024 * 1024
    // 最大文件数量，5个
    private const val MAX_FILE_COUNT = 5
    // 最大保留天数，5天
    private const val MAX_DAYS = 5
    private val tsFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.getDefault())

    @Volatile private var currentLogFile: File? = null
    private val lock = Any()

    /** 将字符串日志级别映射为 Level；无法识别时返回 null。 */
    private fun parseLevel(level: String): Level? = when (level.trim().lowercase()) {
        "debug" -> Level.DEBUG
        "info" -> Level.INFO
        "warn" -> Level.WARN
        "error" -> Level.ERROR
        "fatal" -> Level.FATAL
        "off" -> Level.OFF
        else -> null
    }

    /** 运行中切换日志级别。级别非法时返回 false，minLevel 保持不变。 */
    fun setLogLevel(level: String): Boolean {
        val parsed = parseLevel(level) ?: return false
        minLevel = parsed
        return true
    }

    /**
     * 显式初始化入口，须在首次输出日志前调用一次（Application.onCreate）。
     * 线程安全、幂等：内部设置 logDir、读取 setting.json 并统一默认级别。
     */
    fun initialize(context: Context) {
        if (initialized) return
        synchronized(this) {
            if (initialized) return
            // 仅当外部存储可用时才启用日志落盘；否则 logDir 保持 null，文件日志不写入。
            val external = context.getExternalFilesDir(null)
            if (external != null) {
                val dir = File(external, "logs")
                dir.mkdirs()
                logDir = dir
            }
            minLevel = loadLevelFromSetting(context)
            initialized = true
        }
    }

    /** 从 setting.json 读取 log_level；缺失/无法解析/读取失败时回退统一默认级别 DEFAULT_LEVEL。 */
    private fun loadLevelFromSetting(context: Context): Level {
        val settingFile = File(context.filesDir, "data/setting.json")
        if (!settingFile.exists()) return DEFAULT_LEVEL
        return try {
            val level = org.json.JSONObject(settingFile.readText())
                .optString("log_level", "off")
                .lowercase()
            parseLevel(level) ?: DEFAULT_LEVEL
        } catch (_: Exception) {
            DEFAULT_LEVEL
        }
    }

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
                    rotateLogs()
                }
                val target = ensureLogFile()
                target.appendText(line + "\r\n")
            }
        } catch (_: Exception) {}
    }

    private fun ensureLogFile(): File {
        val dir = logDir ?: return File("/dev/null")

        currentLogFile?.let { f ->
            if (f.name == LOG_FILE_NAME) return f
        }

        dir.mkdirs()
        val file = File(dir, LOG_FILE_NAME)
        currentLogFile = file
        cleanOldLogs()
        return file
    }

    private fun rotateLogs() {
        val dir = logDir ?: return
        dir.mkdirs()

        // 找到当前最大的归档索引
        var maxIndex = 0
        dir.listFiles { f ->
            f.name.startsWith(LOG_FILE_PREFIX) && f.name.endsWith(".log") && f.name != LOG_FILE_NAME
        }?.forEach { f ->
            val name = f.nameWithoutExtension
            if (name.startsWith(LOG_FILE_PREFIX)) {
                val idxStr = name.removePrefix(LOG_FILE_PREFIX)
                val idx = idxStr.toIntOrNull()
                if (idx != null && idx > maxIndex) {
                    maxIndex = idx
                }
            }
        }

        // 从最大索引开始向后移动：3→4, 2→3, 1→2
        for (i in maxIndex downTo 1) {
            val src = File(dir, "${LOG_FILE_PREFIX}${i}.log")
            val dst = File(dir, "${LOG_FILE_PREFIX}${i + 1}.log")
            if (src.exists()) {
                src.renameTo(dst)
            }
        }

        // 当前文件移到 app_kt_1.log
        val current = File(dir, LOG_FILE_NAME)
        if (current.exists()) {
            current.renameTo(File(dir, "${LOG_FILE_PREFIX}1.log"))
        }

        currentLogFile = null
    }

    private fun cleanOldLogs() {
        val dir = logDir ?: return
        val logFiles = dir.listFiles { f ->
            f.name.startsWith(LOG_FILE_PREFIX) && f.name.endsWith(".log")
        } ?: return

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