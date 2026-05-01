package com.ghostengine.pro

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "tasks")
data class Task(
    @PrimaryKey
    val infoHash: String,
    val name: String,
    val peerId: String,
    val uploaded: Long = 0,
    val trackerUrl: String?,
    val leechers: Int = 0,
    val key: String,
    val targetSizeMb: Double = 0.0,
    val port: Int,
    val notified: Int = 0,
    val identityKey: String?,
    val extSeedHours: Int = 0,
    val finishedTs: Long = 0
)
