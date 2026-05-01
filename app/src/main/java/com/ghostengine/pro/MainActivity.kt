package com.ghostengine.pro

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.room.Room
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.flow.collectAsState
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

class MainActivity : ComponentActivity() {
    private lateinit var db: AppDatabase
    private val tasksState = MutableStateFlow<List<Task>>(emptyList())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        db = Room.databaseBuilder(
            applicationContext,
            AppDatabase::class.java, "seeder.db"
        ).build()

        lifecycleScope.launch {
            while(true) {
                tasksState.value = db.taskDao().getAllTasks()
                delay(2000)
            }
        }

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    Dashboard(tasksState.collectAsState().value)
                }
            }
        }
    }
}

@Composable
fun Dashboard(tasks: List<Task>) {
    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Ghost Engine PRO", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn {
            items(tasks) { task ->
                TaskItem(task)
            }
        }
    }
}

@Composable
fun TaskItem(task: Task) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = task.name, style = MaterialTheme.typography.titleMedium)
            Text(text = "Identity: ${task.identityKey}")
            Text(text = "Uploaded: ${task.uploaded / (1024 * 1024)} MB")
            Text(text = "Leechers: ${task.leechers}")
            LinearProgressIndicator(
                progress = if (task.targetSizeMb > 0) (task.uploaded / (task.targetSizeMb * 1024 * 1024)).toFloat() else 0f,
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
            )
        }
    }
}
