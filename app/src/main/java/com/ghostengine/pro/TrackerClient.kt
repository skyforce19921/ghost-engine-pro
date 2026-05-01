package com.ghostengine.pro

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.net.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest
import java.util.*
import kotlin.random.Random

/**
 * Ported from bot.py Core Seeder Engine.
 * Handles HTTP and UDP tracker announcements with stealth masking.
 */
class TrackerClient(private val task: Task) {
    private val client = OkHttpClient()

    fun announce(event: String? = null): Pair<Boolean, String> {
        return if (task.trackerUrl?.startsWith("udp://") == true) {
            announceUdp(event)
        } else {
            announceHttp(event)
        }
    }

    private fun announceHttp(event: String?): Pair<Boolean, String> {
        val trackerUrl = task.trackerUrl ?: return false to "No tracker URL"
        val mask = ClientMasks.MASKS[task.identityKey] ?: ClientMasks.DEFAULT_MASK
        
        val infoHashBytes = hexToBytes(task.infoHash)
        val encodedHash = urlEncodeBytes(infoHashBytes)
        
        val baseUrl = if (trackerUrl.contains("?")) "$trackerUrl&" else "$trackerUrl?"
        val params = mutableMapOf(
            "peer_id" to task.peerId,
            "port" to task.port.toString(),
            "uploaded" to task.uploaded.toString(),
            "downloaded" to "0",
            "left" to "0",
            "corrupt" to "0",
            "key" to task.key,
            "numwant" to "200",
            "compact" to "1",
            "no_peer_id" to "1",
            "supportcrypto" to "1",
            "redundant" to "0"
        )
        if (event != null) params["event"] = event
        
        val queryString = params.entries.joinToString("&") { "${it.key}=${URLEncoder.encode(it.value, "UTF-8")}" }
        val fullUrl = "${baseUrl}${queryString}&info_hash=${encodedHash}"
        
        val request = Request.Builder()
            .url(fullUrl)
            .header("User-Agent", mask.agent)
            .header("Accept-Encoding", "gzip")
            .header("Connection", "close")
            .build()
            
        return try {
            val response: Response = client.newCall(request).execute()
            if (response.isSuccessful) {
                val body = response.body?.bytes()
                val bodyStr = body?.let { String(it, Charsets.ISO_8859_1) } ?: ""
                
                if (bodyStr.contains("failure reason")) {
                    val reason = Regex("failure reason(\\d+):(.*)").find(bodyStr)?.groupValues?.get(2) ?: "Unknown Failure"
                    return false to "Tracker: $reason"
                }

                // Extract leechers (incomplete) from bencode
                val leechersMatch = Regex("incompletei(\\d+)e").find(bodyStr)
                val leechers = leechersMatch?.groupValues?.get(1)?.toIntOrNull() ?: 0
                true to (if (leechers == 0) "👻 Lurking" else "Leechers: $leechers")
            } else {
                false to "HTTP ${response.code}"
            }
        } catch (e: Exception) {
            false to (e.message ?: "Network Error")
        }
    }

    private fun announceUdp(event_name: String?): Pair<Boolean, String> {
        return try {
            val url = URL(task.trackerUrl?.replace("udp://", "http://"))
            val address = InetAddress.getByName(url.host)
            val port = if (url.port == -1) 80 else url.port
            val socket = DatagramSocket()
            socket.soTimeout = 10000
            
            // 1. Connect
            val transactionId = Random.nextInt()
            val connectPacket = ByteBuffer.allocate(16).apply {
                order(ByteOrder.BIG_ENDIAN)
                putLong(0x41727101980L) // Connection ID (Protocol ID)
                putInt(0)               // Action: Connect
                putInt(transactionId)
            }
            
            socket.send(DatagramPacket(connectPacket.array(), 16, address, port))
            
            val receiveBuffer = ByteArray(16)
            val receivePacket = DatagramPacket(receiveBuffer, 16)
            socket.receive(receivePacket)
            
            val receiveBb = ByteBuffer.wrap(receiveBuffer).apply { order(ByteOrder.BIG_ENDIAN) }
            val action = receiveBb.getInt()
            val resTransactionId = receiveBb.getInt()
            val connectionId = receiveBb.getLong()
            
            if (action != 0 || resTransactionId != transactionId) return false to "UDP Connect failed"
            
            // 2. Announce
            val announceTransactionId = Random.nextInt()
            val eventType = when(event_name) {
                "started" -> 2
                "stopped" -> 3
                "completed" -> 1
                else -> 0
            }
            
            val announcePacket = ByteBuffer.allocate(98).apply {
                order(ByteOrder.BIG_ENDIAN)
                putLong(connectionId)
                putInt(1) // Action: Announce
                putInt(announceTransactionId)
                put(hexToBytes(task.infoHash))
                put(task.peerId.toByteArray(Charsets.US_ASCII))
                putLong(0) // Downloaded
                putLong(0) // Left
                putLong(task.uploaded)
                putInt(eventType)
                putInt(0) // IP (0 = default)
                putInt(task.key.toLong(16).toInt())
                putInt(-1) // Num Want (-1 = default)
                putShort(task.port.toShort())
            }
            
            socket.send(DatagramPacket(announcePacket.array(), 98, address, port))
            
            val announceResponse = ByteArray(20)
            val receiveAnnounce = DatagramPacket(announceResponse, 20)
            socket.receive(receiveAnnounce)
            
            val announceBb = ByteBuffer.wrap(announceResponse).apply { order(ByteOrder.BIG_ENDIAN) }
            val resAction = announceBb.getInt()
            val resAnnounceTransactionId = announceBb.getInt()
            val interval = announceBb.getInt()
            val leechers = announceBb.getInt()
            val seeders = announceBb.getInt()
            
            if (resAction != 1 || resAnnounceTransactionId != announceTransactionId) return false to "UDP Announce failed"
            
            true to (if (leechers == 0) "👻 Lurking" else "Leechers: $leechers")
        } catch (e: Exception) {
            false to "UDP Error: ${e.message}"
        }
    }

    private fun hexToBytes(hex: String): ByteArray {
        val result = ByteArray(hex.length / 2)
        for (i in result.indices) {
            val v = hex.substring(i * 2, i * 2 + 2).toInt(16)
            result[i] = v.toByte()
        }
        return result
    }

    private fun urlEncodeBytes(bytes: ByteArray): String {
        val sb = StringBuilder()
        for (b in bytes) {
            val i = b.toInt() and 0xFF
            if (i in 0x30..0x39 || i in 0x41..0x5A || i in 0x61..0x7A || i == 0x2D || i == 0x2E || i == 0x5F || i == 0x7E) {
                sb.append(i.toChar())
            } else {
                sb.append("%" + String.format("%02X", i))
            }
        }
        return sb.toString()
    }
}
