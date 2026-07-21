buildscript {
    repositories {
        mavenCentral()
        maven { url = uri("https://chaquo.com/maven") }
    }
    dependencies {
        classpath("com.chaquo.python:gradle:17.0.0")
    }
}

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

apply(plugin = "com.chaquo.python")

android {
    namespace = "com.easytier.eui"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.easytier.eui"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.4.0"

        ndk {
            abiFilters += listOf("arm64-v8a")
        }

        python {
            buildPython("python3.12")
            pip {
                install("tomlkit")
                install("requests")
                install("dnspython")
                install("qrcode")
            }
            srcDir("src/main/python")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    buildFeatures {
        viewBinding = true
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.webkit:webkit:1.9.0")
}