# Ensure all classes and methods used by Cython code are left alone by minifyEnabled.
-keep class com.chaquo.python.** { * ; }

# Chaquopy core classes (used by Kotlin code)
-keep class com.chaquo.python.PyObject { *; }
-keep class com.chaquo.python.Python { *; }
-keep class com.chaquo.python.android.AndroidPlatform { *; }

# See get_sam in class.pxi.
-keep class kotlin.jvm.functions.** { * ; }
-keep class kotlin.jvm.internal.FunctionBase { * ; }
-keep class kotlin.reflect.KAnnotatedElement { *; }

# Kotlin reflection (if Python code calls Kotlin)
-keep class kotlin.reflect.** { *; }

# TODO: https://github.com/chaquo/chaquopy/issues/842
-dontwarn org.jetbrains.annotations.NotNull