package com.ghostengine.pro

import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.net.*
import java.nio.ByteBuffer
import java.security.MessageDigest
import java.util.*
import kotlin.random.Random

class TrackerClient(private val task: Task) {
    private val client = OkHttpClient()

    fun announceHttp(event: String? = null): Pair<Boolean, String> {
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
                // Simple Bencode parsing for 'incomplete' (leechers)
                val bodyStr = body?.let { String(it, Charsets.ISO_8859_1) } ?: ""
                if (bodyStr.contains("failure reason")) {
                    return false to "Tracker Failure"
                }
                val leechersMatch = Regex("incompletei(\\d+)e").find(bodyStr)
                val leechers = leechersMatch?.groupValues?.get(1)?.toIntOrNull() ?: 0
                true to "Leechers: $leechers"
            } else {
                false to "HTTP ${response.code}"
            }
        } catch (e: Exception) {
            false to (e.message ?: "Unknown Error")
        }
    }

    fun announceUdp(event: String? = null): Pair<Boolean, String> {
        return try {
            val url = URL(task.trackerUrl?.replace("udp://", "http://"))
            val address = InetAddress.getByName(url.host)
            val port = url.port
            val socket = DatagramSocket()
            socket.soTimeout = 10000
            
            val transactionId = Random.nextInt()
            val connectPacket = ByteBuffer.allocate(16)
            connectPacket.putLong(0x41727101980L)
            connectPacket.putInt(0)
            connectPacket.putInt(transactionId)
            
            val sendPacket = DatagramPacket(connectPacket.array(), 16, address, port)
            socket.send(sendPacket)
            
            val receiveBuffer = ByteArray(16)
            val receivePacket = DatagramPacket(receiveBuffer, 16)
            socket.receive(receivePacket)
            
            val receiveBb = ByteBuffer.wrap(receiveBuffer)
            val action = receiveBb.getInt()
            val resTransactionId = receiveBb.getInt()
            val connectionId = receiveBb.getLong()
            
            if (action != 0 || resTransactionId != transactionId) return false to "UDP Connect failed"
            
            val announceTransactionId = Random.nextInt()
            val eventType = when(event) {
                "started" -> 2
                "stopped" -> 3
                "completed" -> 1
                else -> 0
            }
            
            val announcePacket = ByteBuffer.allocate(98)
            announcePacket.putLong(connectionId)
            announcePacket.putInt(1) // action announce
            announcePacket.putInt(announceTransactionId)
            announcePacket.put(hexToBytes(task.infoHash))
            announcePacket.put(task.peerId.toByteArray(Charsets.US_ASCII))
            announcePacket.putLong(0) // downloaded
            announcePacket.putLong(0) // left
            announcePacket.putLong(task.uploaded)
            announcePacket.putInt(eventType)
            announcePacket.putInt(0) // ip
            announcePacket.putInt(task.key.toLong(16).toInt())
            announcePacket.putInt(-1) // num_want
            announcePacket.putShort(task.port.toShort())
            
            val sendAnnounce = DatagramPacket(announcePacket.array(), 98, address, port)
            socket.send(sendAnnounce)
            
            val announceResponse = ByteArray(20)
            val receiveAnnounce = DatagramPacket(announceResponse, 20)
            socket.receive(receiveAnnounce)
            
            val announceBb = ByteBuffer.wrap(announceResponse)
            val resAction = announceBb.getInt()
            val resAnnounceTransactionId = announceBb.getInt()
            val interval = announceBb.getInt()
            val leechers = announceBb.getInt()
            val seeders = announceBb.getInt()
            
            if (resAction != 1 || resAnnounceTransactionId != announceTransactionId) return false to "UDP Announce failed"
            
            true to "Leechers: $leechers"
        } catch (e: Exception) {
            false to "UDP Error: ${e.message}"
        }
    }

    private fun hexToBytes(hex: String): ByteArray {
        val result = ByteArray(hex.length / 2)
        for (i in result.indices) {
            val index = i * 2
            val v = hex.substring(index, index + 2).toInt(16)
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
