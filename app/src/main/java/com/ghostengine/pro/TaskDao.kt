package com.ghostengine.pro

import androidx.room.*

@Dao
interface TaskDao {
    @Query("SELECT * FROM tasks")
    suspend fun getAllTasks(): List<Task>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTask(task: Task)

    @Update
    suspend fun updateTask(task: Task)

    @Delete
    suspend fun deleteTask(task: Task)

    @Query("DELETE FROM tasks WHERE infoHash = :infoHash")
    suspend fun deleteTaskByHash(infoHash: String)

    @Query("SELECT * FROM tasks WHERE infoHash = :infoHash")
    suspend fun getTaskByHash(infoHash: String): Task?
}
