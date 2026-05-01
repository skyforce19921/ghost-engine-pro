package com.ghostengine.pro

import java.io.ByteArrayInputStream
import java.io.InputStream
import java.nio.charset.StandardCharsets

/**
 * Lightweight Bencode Parser for Kotlin.
 */
object Bencode {
    fun decode(data: ByteArray): Any? {
        return decode(ByteArrayInputStream(data))
    }

    private fun decode(stream: InputStream): Any? {
        val c = stream.read().toChar()
        return when {
            c == 'i' -> decodeInt(stream)
            c == 'l' -> decodeList(stream)
            c == 'd' -> decodeDict(stream)
            c.isDigit() -> decodeString(stream, c)
            else -> null
        }
    }

    private fun decodeInt(stream: InputStream): Long {
        val sb = StringBuilder()
        var c = stream.read().toChar()
        while (c != 'e') {
            sb.append(c)
            c = stream.read().toChar()
        }
        return sb.toString().toLong()
    }

    private fun decodeString(stream: InputStream, firstChar: Char): Any {
        val sb = StringBuilder()
        sb.append(firstChar)
        var c = stream.read().toChar()
        while (c != ':') {
            sb.append(c)
            c = stream.read().toChar()
        }
        val length = sb.toString().toInt()
        val bytes = ByteArray(length)
        stream.read(bytes)
        
        // Return as string if it looks like UTF-8, else bytes
        return try {
            val s = String(bytes, StandardCharsets.UTF_8)
            if (s.all { it.code < 128 }) s else bytes
        } catch (e: Exception) {
            bytes
        }
    }

    private fun decodeList(stream: InputStream): List<Any?> {
        val list = mutableListOf<Any?>()
        while (true) {
            stream.mark(1)
            if (stream.read().toChar() == 'e') break
            stream.reset()
            list.add(decode(stream))
        }
        return list
    }

    private fun decodeDict(stream: InputStream): Map<String, Any?> {
        val dict = mutableMapOf<String, Any?>()
        while (true) {
            stream.mark(1)
            if (stream.read().toChar() == 'e') break
            stream.reset()
            val key = decode(stream) as String
            val value = decode(stream)
            dict[key] = value
        }
        return dict
    }
}
