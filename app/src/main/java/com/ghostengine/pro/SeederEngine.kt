package com.ghostengine.pro

import android.content.Context
import androidx.room.Room
import kotlinx.coroutines.*
import java.util.*
import kotlin.random.Random

/**
 * Ported from bot.py announce_loop.
 * Manages periodic seeding simulation and tracker updates.
 */
class SeederEngine(private val context: Context) {
    private val db = Room.databaseBuilder(context, AppDatabase::class.java, "seeder.db").build()
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var job: Job? = null

    private val lastAnnounceTime = mutableMapOf<String, Long>()
    private val ANNOUNCE_INTERVAL_MS = 1800 * 1000L

    fun start() {
        if (job?.isActive == true) return
        job = scope.launch {
            while (isActive) {
                try {
                    val tasks = db.taskDao().getAllTasks()
                    for (task in tasks) {
                        processTask(task)
                    }
                } catch (e: Exception) {
                    // Log error
                }
                delay(5000) // Seeding tick every 5 seconds
            }
        }
    }

    private suspend fun processTask(task: Task) {
        val now = System.currentTimeMillis()
        
        // 1. Simulation Logic (Humanized Seeding)
        val calendar = Calendar.getInstance(TimeZone.getTimeZone("Asia/Kolkata"))
        val hour = calendar.get(Calendar.HOUR_OF_DAY)
        val isSleeping = hour in 2..7 // 2 AM to 8 AM

        if (task.leechers > 0 && !isSleeping) {
            // Simulate upload: random speed 200-600 KB/s
            val speedKb = Random.nextDouble(200.0, 600.0)
            val incrementBytes = (speedKb * 5 * 1024).toLong() // 5 seconds of upload
            
            val newUploaded = task.uploaded + incrementBytes
            val updatedTask = task.copy(uploaded = newUploaded)
            db.taskDao().updateTask(updatedTask)
        }

        // 2. Announce Logic (Every 30 mins)
        val lastAnnounce = lastAnnounceTime[task.infoHash] ?: 0L
        if (now - lastAnnounce >= ANNOUNCE_INTERVAL_MS) {
            val client = TrackerClient(task)
            val result = withContext(Dispatchers.IO) { client.announce() }
            
            if (result.first) {
                lastAnnounceTime[task.infoHash] = now
                // Extract leecher count if possible and update DB
                val leecherMatch = Regex("Leechers: (\\d+)").find(result.second)
                val leechers = leecherMatch?.groupValues?.get(1)?.toIntOrNull() ?: 0
                db.taskDao().updateTask(task.copy(leechers = leechers))
            }
        }
    }

    fun stop() {
        job?.cancel()
    }
}
