package com.ghostengine.pro

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.room.Room
import kotlinx.coroutines.delay
import java.util.concurrent.TimeUnit
import kotlin.random.Random

class SeedingWorker(appContext: Context, workerParams: WorkerParameters) :
    CoroutineWorker(appContext, workerParams) {

    private val db = Room.databaseBuilder(
        appContext,
        AppDatabase::class.java, "seeder.db"
    ).build()

    override suspend fun doWork(): Result {
        while (true) {
            val tasks = db.taskDao().getAllTasks()
            if (tasks.isEmpty()) break

            for (task in tasks) {
                // Simplified seeding logic
                if (task.leechers > 0) {
                    val baseSpeed = Random.nextDouble(200.0, 600.0) // KB/s
                    val incrementMb = (baseSpeed * 5) / 1024.0
                    val newUploaded = task.uploaded + (incrementMb * 1024 * 1024).toLong()
                    
                    val updatedTask = task.copy(uploaded = newUploaded)
                    db.taskDao().updateTask(updatedTask)
                    
                    // Periodic Announce (every 30 mins, but for simulation let's say every 100 ticks)
                    // In real app, we would track LAST_ANNOUNCE_TIME
                }
            }
            
            delay(5000) // 5 second ticks
        }
        return Result.success()
    }
}
