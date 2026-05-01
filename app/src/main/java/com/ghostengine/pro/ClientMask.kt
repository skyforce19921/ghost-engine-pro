package com.ghostengine.pro

data class ClientMask(
    val name: String,
    val agent: String,
    val prefix: String
)

object ClientMasks {
    val MASKS = mapOf(
        "qbit_514" to ClientMask("qBit 5.1.4", "qBittorrent/5.1.4", "-qB5140-"),
        "qbit_501" to ClientMask("qBit 5.0.1", "qBittorrent/5.0.1", "-qB5010-"),
        "qbit_464" to ClientMask("qBit 4.6.4", "qBittorrent/4.6.4", "-qB4640-"),
        "qbit_442" to ClientMask("qBit 4.4.2", "qBittorrent/4.4.2", "-qB4420-"),
        "trans_405" to ClientMask("Transmission 4.0.5", "Transmission/4.0.5", "-TR4050-"),
        "trans_300" to ClientMask("Transmission 3.00", "Transmission/3.00", "-TR3000-"),
        "deluge_211" to ClientMask("Deluge 2.1.1", "Deluge/2.1.1", "-DE2110-"),
        "deluge_203" to ClientMask("Deluge 2.0.3", "Deluge/2.0.3", "-DE2030-")
    )
    
    val DEFAULT_MASK = MASKS["qbit_514"]!!
}
