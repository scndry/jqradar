package com.acme.app.util

import javax.annotation.processing.Generated

class Formatter {
    fun format(value: Long): String = "#" + value
}

@Generated("codegen")
fun generatedLookup(key: String): Int = key.length
