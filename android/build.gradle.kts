// Top-level build file for EasyTier-EUI Android
plugins {
    id("com.android.application") version "8.4.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
    id("com.chaquo.python") version "16.0.0" apply false
}

tasks.register("clean", Delete::class) {
    delete(rootProject.layout.buildDirectory)
}