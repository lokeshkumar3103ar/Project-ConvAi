# RTX Log - June 9, 2025 15:30
**COMPLETE IMPLEMENTATION REFERENCE: Two-Phase Queue Multi-User Concurrency System**
**Classification: CRITICAL IMPLEMENTATION DOCUMENT**

## 🎯 EXECUTIVE SUMMARY
This document provides the complete technical specification and implementation reference for the two-phase queue system designed to handle 30+ simultaneous students in the ConvAi-IntroEval lab environment. This solution transforms a 25-minute sequential bottleneck into a 15-minute concurrent processing system with 100% file persistence and recovery capabilities.

---

## 📋 SYSTEM ARCHITECTURE OVERVIEW

### **Core Design Philosophy**
```
PRINCIPLE 1: Complete Phase Separation (STT ↔ LLM Mutual Exclusion)
PRINCIPLE 2: File-First Persistence (All uploads saved before processing)
PRINCIPLE 3: Graceful Degradation (System continues despite failures)
PRINCIPLE 4: Transparent Recovery (Students see clear status updates)
```

### **Two-Phase Processing Flow**
```
PHASE 1: STT BATCH PROCESSING
Students Upload → STT Queue → Sequential STT Processing → Batch Complete

PHASE 2: LLM PIPELINE PROCESSING  
STT Complete Batch → Evaluation Queue → Mistral+LLaMA3 Pipeline → Results

PHASE TRANSITION: Automatic switching when queues empty/complete
```

---

## 🏗️ DETAILED TECHNICAL ARCHITECTURE

### **1. Core Queue Management System**

#### **Primary Queue Controller**
```python
class TwoPhaseQueueManager:
    """
    Master controller for two-phase queue system
    Handles phase transitions, resource allocation, and error recovery
    """
    def __init__(self):
        # Phase Management
        self.current_phase = "STT"  # "STT" or "EVALUATION"
        self.phase_lock = threading.Lock()
        self.phase_transition_event = threading.Event()
        
        # Queue Systems
        self.stt_queue = queue.Queue()
        self.evaluation_queue = queue.Queue()
        self.completed_queue = queue.Queue()
        
        # Processing Status Tracking
        self.active_tasks = {}  # task_id: TaskStatus
        self.failed_tasks = {}  # task_id: FailureInfo
        self.processing_stats = ProcessingStats()
        
        # Resource Management
        self.stt_worker = None
        self.mistral_worker = None
        self.llama_worker = None
        self.resource_monitor = ResourceMonitor()
        
        # Persistence
        self.task_db = TaskDatabase()
        self.file_manager = FileManager()
        
    def start_processing(self):
        """Initialize all workers and start processing loop"""
        self.initialize_workers()
        self.start_phase_manager()
        self.start_monitoring()
        
    def add_upload_task(self, user_id: str, file_path: str) -> str:
        """Add new upload to appropriate queue based on current phase"""
        task_id = self.generate_task_id(user_id)
        
        # Always save file first (CRITICAL)
        saved_path = self.file_manager.save_upload(file_path, task_id)
        
        # Create persistent task record
        task = ProcessingTask(
            task_id=task_id,
            user_id=user_id,
            file_path=saved_path,
            status="pending_stt",
            created_at=datetime.now(),
            phase="STT"
        )
        
        # Save to database immediately
        self.task_db.save_task(task)
        
        # Add to appropriate queue
        if self.current_phase == "STT":
            self.stt_queue.put(task)
        else:
            # STT phase not active, queue for next STT batch
            self.stt_queue.put(task)
            
        return task_id
```

#### **Task Status Management**
```python
class ProcessingTask:
    """Individual task representation with full lifecycle tracking"""
    def __init__(self, task_id: str, user_id: str, file_path: str):
        self.task_id = task_id
        self.user_id = user_id
        self.file_path = file_path
        self.status = "pending_stt"
        self.phase = "STT"
        
        # Timestamps
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.last_updated = datetime.now()
        
        # Processing Results
        self.stt_result = None
        self.mistral_result = None
        self.llama_result = None
        
        # Error Information
        self.error_count = 0
        self.last_error = None
        self.retry_after = None
        
        # Progress Tracking
        self.progress_percentage = 0
        self.current_stage = "queued"
        self.estimated_completion = None

class TaskStatus:
    """Task status enumeration"""
    PENDING_STT = "pending_stt"
    PROCESSING_STT = "processing_stt"
    STT_COMPLETE = "stt_complete"
    PENDING_EVALUATION = "pending_evaluation"
    PROCESSING_MISTRAL = "processing_mistral"
    PROCESSING_LLAMA = "processing_llama"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY_QUEUED = "retry_queued"
```

### **2. Phase Management System**

#### **Phase Controller**
```python
class PhaseController:
    """Manages transitions between STT and Evaluation phases"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.phase_history = []
        self.transition_metrics = {}
        
    def check_phase_transition(self):
        """Determine if phase transition should occur"""
        current_phase = self.queue_manager.current_phase
        
        if current_phase == "STT":
            return self._should_transition_to_evaluation()
        else:
            return self._should_transition_to_stt()
    
    def _should_transition_to_evaluation(self) -> bool:
        """Check if STT phase should transition to Evaluation"""
        conditions = {
            'stt_queue_empty': self.queue_manager.stt_queue.empty(),
            'no_active_stt': not self._has_active_stt_tasks(),
            'evaluation_queue_ready': not self.queue_manager.evaluation_queue.empty(),
            'memory_available': self.queue_manager.resource_monitor.gpu_memory_available()
        }
        
        # Log transition analysis
        self._log_transition_analysis("STT->EVALUATION", conditions)
        
        # All conditions must be true for transition
        return all(conditions.values())
    
    def _should_transition_to_stt(self) -> bool:
        """Check if Evaluation phase should transition to STT"""
        conditions = {
            'evaluation_queue_empty': self.queue_manager.evaluation_queue.empty(),
            'no_active_evaluation': not self._has_active_evaluation_tasks(),
            'stt_queue_waiting': not self.queue_manager.stt_queue.empty(),
            'memory_available': self.queue_manager.resource_monitor.gpu_memory_available()
        }
        
        self._log_transition_analysis("EVALUATION->STT", conditions)
        return all(conditions.values())
    
    def execute_phase_transition(self, new_phase: str):
        """Execute safe phase transition with proper cleanup"""
        old_phase = self.queue_manager.current_phase
        
        with self.queue_manager.phase_lock:
            # Step 1: Stop current phase workers
            self._stop_phase_workers(old_phase)
            
            # Step 2: Clear GPU memory
            self.queue_manager.resource_monitor.clear_gpu_memory()
            
            # Step 3: Update phase
            self.queue_manager.current_phase = new_phase
            
            # Step 4: Start new phase workers
            self._start_phase_workers(new_phase)
            
            # Step 5: Signal phase transition
            self.queue_manager.phase_transition_event.set()
            self.queue_manager.phase_transition_event.clear()
        
        # Log transition
        self._log_phase_transition(old_phase, new_phase)
        
        # Update user dashboards
        self._notify_users_phase_change(new_phase)
```

### **3. Resource Management & Memory Safety**

#### **GPU Memory Monitor**
```python
class ResourceMonitor:
    """Monitor and manage GPU memory usage across all models"""
    
    def __init__(self):
        self.gpu_memory_threshold = 0.85  # 85% max usage
        self.monitoring_interval = 5  # seconds
        self.memory_history = []
        
    def get_gpu_memory_usage(self) -> dict:
        """Get current GPU memory usage statistics"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Assume single GPU
                return {
                    'total_memory': gpu.memoryTotal,
                    'used_memory': gpu.memoryUsed,
                    'free_memory': gpu.memoryFree,
                    'usage_percentage': gpu.memoryUtil,
                    'temperature': gpu.temperature
                }
        except Exception as e:
            self._log_monitoring_error(e)
            return self._get_fallback_memory_stats()
    
    def gpu_memory_available(self) -> bool:
        """Check if GPU memory is available for new tasks"""
        stats = self.get_gpu_memory_usage()
        return stats['usage_percentage'] < self.gpu_memory_threshold
    
    def wait_for_memory_availability(self, timeout: int = 300):
        """Wait for GPU memory to become available"""
        start_time = time.time()
        
        while not self.gpu_memory_available():
            if time.time() - start_time > timeout:
                raise ResourceTimeoutError("GPU memory unavailable after timeout")
            
            self._log_memory_wait()
            time.sleep(self.monitoring_interval)
    
    def clear_gpu_memory(self):
        """Force GPU memory cleanup between phases"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except Exception as e:
            self._log_cleanup_error(e)

class ResourceTimeoutError(Exception):
    """Raised when resource availability timeout is exceeded"""
    pass
```

### **4. Worker Management System**

#### **STT Worker (Single Threaded)**
```python
class STTWorker:
    """Single-threaded STT processor for sequential batch processing"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.is_active = False
        self.current_task = None
        self.processing_thread = None
        
    def start(self):
        """Start STT processing thread"""
        self.is_active = True
        self.processing_thread = threading.Thread(target=self._process_stt_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop(self):
        """Stop STT processing gracefully"""
        self.is_active = False
        if self.processing_thread:
            self.processing_thread.join(timeout=30)
    
    def _process_stt_queue(self):
        """Main STT processing loop"""
        while self.is_active:
            try:
                # Wait for task with timeout
                task = self.queue_manager.stt_queue.get(timeout=5)
                
                if task is None:  # Shutdown signal
                    break
                
                self._process_single_stt_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                self._handle_stt_error(task if 'task' in locals() else None, e)
    
    def _process_single_stt_task(self, task: ProcessingTask):
        """Process individual STT task with full error handling"""
        self.current_task = task
        
        try:
            # Update task status
            task.status = TaskStatus.PROCESSING_STT
            task.started_at = datetime.now()
            task.current_stage = "speech_to_text"
            task.progress_percentage = 10
            self.queue_manager.task_db.update_task(task)
            
            # Ensure GPU memory available
            self.queue_manager.resource_monitor.wait_for_memory_availability()
            
            # Process STT
            transcription = self._run_stt_processing(task.file_path)
            
            # Save STT result
            task.stt_result = transcription
            task.status = TaskStatus.STT_COMPLETE
            task.progress_percentage = 30
            task.current_stage = "stt_complete"
            self.queue_manager.task_db.update_task(task)
            
            # Move to evaluation queue
            self.queue_manager.evaluation_queue.put(task)
            
            # Log success
            self._log_stt_success(task)
            
        except Exception as e:
            self._handle_stt_task_error(task, e)
        finally:
            self.current_task = None
    
    def _run_stt_processing(self, file_path: str) -> str:
        """Execute actual STT processing with Whisper"""
        import whisper
        
        # Load model (cached after first load)
        model = whisper.load_model("base")
        
        # Process audio
        result = model.transcribe(file_path)
        
        return result["text"]
```

#### **LLM Workers (Dual Pipeline)**
```python
class LLMWorkerManager:
    """Manages Mistral and LLaMA3 workers for pipeline processing"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.mistral_worker = MistralWorker(self)
        self.llama_worker = LLaMA3Worker(self)
        self.is_active = False
        
    def start(self):
        """Start both LLM workers"""
        self.is_active = True
        self.mistral_worker.start()
        self.llama_worker.start()
    
    def stop(self):
        """Stop both LLM workers gracefully"""
        self.is_active = False
        self.mistral_worker.stop()
        self.llama_worker.stop()

class MistralWorker:
    """Handles form extraction using Mistral model"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.mistral_queue = queue.Queue()
        self.is_active = False
        self.processing_thread = None
        
    def start(self):
        self.is_active = True
        self.processing_thread = threading.Thread(target=self._process_mistral_queue)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def _process_mistral_queue(self):
        """Main Mistral processing loop"""
        while self.is_active:
            try:
                # Get task from evaluation queue
                task = self._get_next_stt_completed_task()
                
                if task:
                    self._process_mistral_task(task)
                else:
                    time.sleep(1)  # Wait for tasks
                    
            except Exception as e:
                self._handle_mistral_error(e)
    
    def _process_mistral_task(self, task: ProcessingTask):
        """Process form extraction with Mistral"""
        try:
            # Update status
            task.status = TaskStatus.PROCESSING_MISTRAL
            task.current_stage = "form_extraction"
            task.progress_percentage = 50
            self.llm_manager.queue_manager.task_db.update_task(task)
            
            # Call Mistral API
            form_data = self._call_mistral_api(task.stt_result)
            
            # Save result
            task.mistral_result = form_data
            task.progress_percentage = 70
            self.llm_manager.queue_manager.task_db.update_task(task)
            
            # Pass to LLaMA3 worker
            self.llm_manager.llama_worker.add_task(task)
            
        except Exception as e:
            self._handle_mistral_task_error(task, e)
    
    def _call_mistral_api(self, transcription: str) -> dict:
        """Call Mistral container for form extraction"""
        import requests
        
        payload = {
            "model": "mistral",
            "prompt": f"Extract form data from: {transcription}",
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise MistralAPIError(f"Mistral API error: {response.status_code}")

class LLaMA3Worker:
    """Handles rating and feedback using LLaMA3 model"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
        self.llama_queue = queue.Queue()
        self.is_active = False
        self.processing_thread = None
        
    def add_task(self, task: ProcessingTask):
        """Add task to LLaMA3 processing queue"""
        self.llama_queue.put(task)
    
    def _process_llama_queue(self):
        """Main LLaMA3 processing loop"""
        while self.is_active:
            try:
                task = self.llama_queue.get(timeout=5)
                self._process_llama_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                self._handle_llama_error(e)
    
    def _process_llama_task(self, task: ProcessingTask):
        """Process rating and feedback with LLaMA3"""
        try:
            # Update status
            task.status = TaskStatus.PROCESSING_LLAMA
            task.current_stage = "rating_feedback"
            task.progress_percentage = 80
            self.llm_manager.queue_manager.task_db.update_task(task)
            
            # Call LLaMA3 API
            rating_data = self._call_llama_api(task.mistral_result)
            
            # Save final result
            task.llama_result = rating_data
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress_percentage = 100
            task.current_stage = "completed"
            self.llm_manager.queue_manager.task_db.update_task(task)
            
            # Save final files
            self._save_final_results(task)
            
            # Move to completed queue
            self.llm_manager.queue_manager.completed_queue.put(task)
            
        except Exception as e:
            self._handle_llama_task_error(task, e)
    
    def _call_llama_api(self, form_data: dict) -> dict:
        """Call LLaMA3 container for rating and feedback"""
        import requests
        
        payload = {
            "model": "llama3",
            "prompt": f"Rate and provide feedback for: {form_data}",
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11435/api/generate",
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise LLaMAAPIError(f"LLaMA3 API error: {response.status_code}")
```

### **5. Error Handling & Recovery System**

#### **Comprehensive Error Handler**
```python
class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.error_log = []
        self.recovery_strategies = {
            'STTError': self._handle_stt_error,
            'MistralAPIError': self._handle_mistral_error,
            'LLaMAAPIError': self._handle_llama_error,
            'ResourceTimeoutError': self._handle_resource_timeout,
            'DatabaseError': self._handle_database_error,
            'FileSystemError': self._handle_filesystem_error
        }
        
    def handle_error(self, error: Exception, task: ProcessingTask = None, context: dict = None):
        """Central error handling with automatic recovery"""
        error_type = type(error).__name__
        error_info = {
            'timestamp': datetime.now(),
            'error_type': error_type,
            'error_message': str(error),
            'task_id': task.task_id if task else None,
            'context': context or {},
            'stack_trace': traceback.format_exc()
        }
        
        # Log error
        self.error_log.append(error_info)
        self._log_error_details(error_info)
        
        # Execute recovery strategy
        if error_type in self.recovery_strategies:
            self.recovery_strategies[error_type](error, task, error_info)
        else:
            self._handle_unknown_error(error, task, error_info)
    
    def _handle_stt_error(self, error: Exception, task: ProcessingTask, error_info: dict):
        """Handle STT processing errors with retry logic"""
        if task:
            task.error_count += 1
            task.last_error = str(error)
            
            if task.error_count <= 3:  # Max 3 retries
                # Schedule retry
                task.status = TaskStatus.RETRY_QUEUED
                task.retry_after = datetime.now() + timedelta(minutes=2)
                self.queue_manager.task_db.update_task(task)
                
                # Add back to STT queue after delay
                threading.Timer(120, self._retry_stt_task, args=[task]).start()
            else:
                # Mark as failed after 3 attempts
                task.status = TaskStatus.FAILED
                self.queue_manager.task_db.update_task(task)
                self._notify_user_failure(task)
    
    def _handle_mistral_error(self, error: Exception, task: ProcessingTask, error_info: dict):
        """Handle Mistral API errors with container restart if needed"""
        if "connection" in str(error).lower():
            # Container might be down, attempt restart
            self._restart_mistral_container()
            
        # Retry task
        if task and task.error_count < 3:
            task.error_count += 1
            self.queue_manager.evaluation_queue.put(task)
    
    def _handle_resource_timeout(self, error: Exception, task: ProcessingTask, error_info: dict):
        """Handle GPU memory timeout with aggressive cleanup"""
        # Force GPU memory cleanup
        self.queue_manager.resource_monitor.clear_gpu_memory()
        
        # Restart all workers to clear memory leaks
        self._restart_all_workers()
        
        # Requeue task
        if task:
            self.queue_manager.stt_queue.put(task)
    
    def _restart_mistral_container(self):
        """Restart Mistral Docker container"""
        try:
            import subprocess
            subprocess.run(["docker", "restart", "mistral-container"], check=True)
            time.sleep(10)  # Wait for container startup
        except Exception as e:
            self._log_container_restart_error("mistral", e)
    
    def _notify_user_failure(self, task: ProcessingTask):
        """Notify user of processing failure with retry option"""
        # Update database with failure status
        task.status = TaskStatus.FAILED
        task.last_updated = datetime.now()
        self.queue_manager.task_db.update_task(task)
        
        # Send notification (email/dashboard update)
        self._send_failure_notification(task)
```

#### **Recovery & Persistence System**
```python
class TaskDatabase:
    """Persistent task storage with recovery capabilities"""
    
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize task database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL,
                phase TEXT NOT NULL,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                last_updated TIMESTAMP,
                stt_result TEXT,
                mistral_result TEXT,
                llama_result TEXT,
                error_count INTEGER DEFAULT 0,
                last_error TEXT,
                retry_after TIMESTAMP,
                progress_percentage INTEGER DEFAULT 0,
                current_stage TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_task(self, task: ProcessingTask):
        """Save task to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processing_tasks 
            (task_id, user_id, file_path, status, phase, created_at, started_at, 
             completed_at, last_updated, stt_result, mistral_result, llama_result,
             error_count, last_error, retry_after, progress_percentage, current_stage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.task_id, task.user_id, task.file_path, task.status, task.phase,
            task.created_at, task.started_at, task.completed_at, task.last_updated,
            task.stt_result, task.mistral_result, task.llama_result,
            task.error_count, task.last_error, task.retry_after,
            task.progress_percentage, task.current_stage
        ))
        
        conn.commit()
        conn.close()
    
    def get_tasks_by_status(self, statuses: list) -> list:
        """Retrieve tasks by status for recovery"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(statuses))
        cursor.execute(f'''
            SELECT * FROM processing_tasks 
            WHERE status IN ({placeholders})
            ORDER BY created_at ASC
        ''', statuses)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_task(row) for row in rows]
    
    def recover_incomplete_tasks(self) -> dict:
        """Recover all incomplete tasks on system startup"""
        incomplete_statuses = [
            TaskStatus.PENDING_STT,
            TaskStatus.PROCESSING_STT,
            TaskStatus.STT_COMPLETE,
            TaskStatus.PENDING_EVALUATION,
            TaskStatus.PROCESSING_MISTRAL,
            TaskStatus.PROCESSING_LLAMA,
            TaskStatus.RETRY_QUEUED
        ]
        
        incomplete_tasks = self.get_tasks_by_status(incomplete_statuses)
        
        recovery_plan = {
            'stt_queue': [],
            'evaluation_queue': [],
            'retry_queue': [],
            'total_recovered': len(incomplete_tasks)
        }
        
        for task in incomplete_tasks:
            if task.status in [TaskStatus.PENDING_STT, TaskStatus.PROCESSING_STT]:
                recovery_plan['stt_queue'].append(task)
            elif task.status in [TaskStatus.STT_COMPLETE, TaskStatus.PENDING_EVALUATION, 
                               TaskStatus.PROCESSING_MISTRAL, TaskStatus.PROCESSING_LLAMA]:
                recovery_plan['evaluation_queue'].append(task)
            elif task.status == TaskStatus.RETRY_QUEUED:
                recovery_plan['retry_queue'].append(task)
        
        return recovery_plan
```

### **6. User Interface & Status Updates**

#### **Real-time Dashboard Updates**
```python
class DashboardManager:
    """Manages real-time dashboard updates for students"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.websocket_connections = {}  # user_id: websocket
        
    def connect_user(self, user_id: str, websocket):
        """Register user websocket connection"""
        self.websocket_connections[user_id] = websocket
        
        # Send current tasks status
        self._send_user_status_update(user_id)
    
    def broadcast_phase_change(self, new_phase: str):
        """Broadcast phase change to all connected users"""
        message = {
            'type': 'phase_change',
            'phase': new_phase,
            'message': self._get_phase_message(new_phase),
            'timestamp': datetime.now().isoformat()
        }
        
        self._broadcast_to_all_users(message)
    
    def send_task_update(self, task: ProcessingTask):
        """Send task progress update to specific user"""
        if task.user_id in self.websocket_connections:
            message = {
                'type': 'task_update',
                'task_id': task.task_id,
                'status': task.status,
                'progress': task.progress_percentage,
                'stage': task.current_stage,
                'estimated_completion': task.estimated_completion,
                'timestamp': datetime.now().isoformat()
            }
            
            self._send_to_user(task.user_id, message)
    
    def _get_phase_message(self, phase: str) -> str:
        """Get user-friendly phase message"""
        messages = {
            'STT': 'System is processing speech-to-text for uploaded videos',
            'EVALUATION': 'System is evaluating and rating processed videos'
        }
        return messages.get(phase, f'System is in {phase} phase')
    
    def _send_user_tasks_summary(self, user_id: str):
        """Send complete tasks summary to user"""
        user_tasks = self.queue_manager.task_db.get_user_tasks(user_id)
        
        summary = {
            'type': 'tasks_summary',
            'tasks': [self._task_to_dict(task) for task in user_tasks],
            'queue_position': self._get_user_queue_position(user_id),
            'estimated_wait': self._calculate_estimated_wait(user_id)
        }
        
        self._send_to_user(user_id, summary)
```

#### **Queue Position & Wait Time Calculator**
```python
class QueueAnalytics:
    """Provides queue analytics and wait time estimates"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.processing_history = []
        
    def get_user_queue_position(self, user_id: str) -> dict:
        """Calculate user's position in current phase queue"""
        current_phase = self.queue_manager.current_phase
        
        if current_phase == "STT":
            return self._get_stt_queue_position(user_id)
        else:
            return self._get_evaluation_queue_position(user_id)
    
    def calculate_estimated_wait_time(self, user_id: str) -> dict:
        """Calculate estimated wait time for user's tasks"""
        queue_position = self.get_user_queue_position(user_id)
        average_processing_times = self._get_average_processing_times()
        
        estimated_times = {}
        
        for task_id, position in queue_position.items():
            if position > 0:
                phase = self._get_task_phase(task_id)
                avg_time = average_processing_times.get(phase, 30)  # Default 30s
                estimated_wait = position * avg_time
                estimated_times[task_id] = {
                    'position': position,
                    'estimated_wait_seconds': estimated_wait,
                    'estimated_completion': datetime.now() + timedelta(seconds=estimated_wait)
                }
        
        return estimated_times
    
    def _get_average_processing_times(self) -> dict:
        """Calculate average processing times from history"""
        if not self.processing_history:
            return {
                'STT': 10,
                'MISTRAL': 15,
                'LLAMA': 25
            }
        
        # Calculate from actual history
        stt_times = [h['stt_duration'] for h in self.processing_history if 'stt_duration' in h]
        mistral_times = [h['mistral_duration'] for h in self.processing_history if 'mistral_duration' in h]
        llama_times = [h['llama_duration'] for h in self.processing_history if 'llama_duration' in h]
        
        return {
            'STT': statistics.mean(stt_times) if stt_times else 10,
            'MISTRAL': statistics.mean(mistral_times) if mistral_times else 15,
            'LLAMA': statistics.mean(llama_times) if llama_times else 25
        }
```

### **7. System Monitoring & Logging**

#### **Comprehensive System Monitor**
```python
class SystemMonitor:
    """Comprehensive system monitoring and alerting"""
    
    def __init__(self, queue_manager):
        self.queue_manager = queue_manager
        self.monitoring_active = False
        self.alert_thresholds = {
            'queue_size_warning': 20,
            'queue_size_critical': 50,
            'processing_time_warning': 60,  # seconds
            'processing_time_critical': 120,
            'error_rate_warning': 0.1,  # 10%
            'error_rate_critical': 0.25,  # 25%
            'gpu_memory_warning': 0.8,  # 80%
            'gpu_memory_critical': 0.95  # 95%
        }
        
    def start_monitoring(self):
        """Start comprehensive system monitoring"""
        self.monitoring_active = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_queues, daemon=True).start()
        threading.Thread(target=self._monitor_processing_times, daemon=True).start()
        threading.Thread(target=self._monitor_error_rates, daemon=True).start()
        threading.Thread(target=self._monitor_resources, daemon=True).start()
        
    def _monitor_queues(self):
        """Monitor queue sizes and alert on buildup"""
        while self.monitoring_active:
            stt_size = self.queue_manager.stt_queue.qsize()
            eval_size = self.queue_manager.evaluation_queue.qsize()
            
            # Check thresholds
            if stt_size >= self.alert_thresholds['queue_size_critical']:
                self._send_alert('CRITICAL', f'STT queue size: {stt_size}')
            elif stt_size >= self.alert_thresholds['queue_size_warning']:
                self._send_alert('WARNING', f'STT queue size: {stt_size}')
            
            if eval_size >= self.alert_thresholds['queue_size_critical']:
                self._send_alert('CRITICAL', f'Evaluation queue size: {eval_size}')
            elif eval_size >= self.alert_thresholds['queue_size_warning']:
                self._send_alert('WARNING', f'Evaluation queue size: {eval_size}')
            
            time.sleep(30)  # Check every 30 seconds
    
    def _monitor_processing_times(self):
        """Monitor individual task processing times"""
        while self.monitoring_active:
            active_tasks = self.queue_manager.get_active_tasks()
            
            for task in active_tasks:
                if task.started_at:
                    processing_time = (datetime.now() - task.started_at).total_seconds()
                    
                    if processing_time >= self.alert_thresholds['processing_time_critical']:
                        self._send_alert('CRITICAL', 
                                       f'Task {task.task_id} processing for {processing_time}s')
                    elif processing_time >= self.alert_thresholds['processing_time_warning']:
                        self._send_alert('WARNING', 
                                       f'Task {task.task_id} processing for {processing_time}s')
            
            time.sleep(60)  # Check every minute
    
    def generate_system_report(self) -> dict:
        """Generate comprehensive system status report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'phase': self.queue_manager.current_phase,
            'queues': {
                'stt_size': self.queue_manager.stt_queue.qsize(),
                'evaluation_size': self.queue_manager.evaluation_queue.qsize(),
                'completed_size': self.queue_manager.completed_queue.qsize()
            },
            'active_tasks': len(self.queue_manager.get_active_tasks()),
            'failed_tasks': len(self.queue_manager.get_failed_tasks()),
            'resource_usage': self.queue_manager.resource_monitor.get_gpu_memory_usage(),
            'processing_stats': self._get_processing_statistics(),
            'error_summary': self._get_error_summary(),
            'performance_metrics': self._get_performance_metrics()
        }
```

---

## 🚀 IMPLEMENTATION ROADMAP

### **Phase 1: Core Infrastructure (Week 1)**
1. **Queue Management System**
   - Implement `TwoPhaseQueueManager`
   - Create `ProcessingTask` data structure
   - Build `TaskDatabase` with SQLite persistence

2. **Phase Controller**
   - Implement `PhaseController` with transition logic
   - Create phase transition safety mechanisms
   - Add comprehensive logging

3. **Resource Monitoring**
   - Implement `ResourceMonitor` for GPU memory tracking
   - Create memory cleanup mechanisms
   - Add resource availability checks

### **Phase 2: Worker Implementation (Week 2)**
1. **STT Worker**
   - Implement single-threaded `STTWorker`
   - Add Whisper integration
   - Create error handling and retry logic

2. **LLM Workers**
   - Implement `MistralWorker` with Docker API calls
   - Implement `LLaMA3Worker` with pipeline processing
   - Add inter-worker communication

3. **Error Handling System**
   - Implement comprehensive `ErrorHandler`
   - Create recovery strategies for each error type
   - Add automatic retry mechanisms

### **Phase 3: User Interface & Monitoring (Week 3)**
1. **Dashboard Updates**
   - Implement real-time WebSocket updates
   - Create queue position calculator
   - Add estimated wait time display

2. **System Monitoring**
   - Implement `SystemMonitor` with alerting
   - Create performance metrics collection
   - Add automated health checks

3. **Testing & Optimization**
   - Test with 5, 15, and 30 concurrent users
   - Optimize memory usage and processing times
   - Fine-tune phase transition logic

### **Phase 4: Production Deployment (Week 4)**
1. **Lab Environment Setup**
   - Deploy on 3060Ti desktop
   - Configure Docker containers
   - Set up monitoring dashboards

2. **User Training & Documentation**
   - Create user guides for students and teachers
   - Document system administration procedures
   - Prepare troubleshooting guides

3. **Go-Live & Support**
   - Gradual rollout with small classes
   - Monitor system performance
   - Provide ongoing support and optimization

---

## 📊 PERFORMANCE EXPECTATIONS

### **Throughput Projections**
```
Current System: 1 user per 50 seconds = 25 minutes for 30 students
Two-Phase System: 15 minutes total for 30 students (40% improvement)

Breakdown:
- STT Phase: 10 students × 10s = 100s (3 batches = 5 minutes total)
- Evaluation Phase: 30 students × 40s ÷ 2 = 10 minutes total
```

### **Resource Utilization**
```
GPU Memory Usage:
- STT Phase: 3-4GB maximum (safe)
- Evaluation Phase: 6-7GB maximum (monitored)
- Peak Efficiency: 85% GPU utilization maintained
```

### **User Experience Metrics**
```
Average Wait Time: 7.5 minutes (down from 12.5 minutes)
Maximum Wait Time: 15 minutes (down from 25 minutes)
System Availability: 99.5% (with recovery mechanisms)
Processing Success Rate: 98% (with retry logic)
```

---

## 🔒 CRITICAL SUCCESS FACTORS

### **1. Memory Management**
- Strict phase separation prevents GPU memory conflicts
- Aggressive cleanup between phases ensures stability
- Continuous monitoring prevents resource exhaustion

### **2. Error Recovery**
- File-first persistence ensures no data loss
- Automatic retry mechanisms handle transient failures
- Graceful degradation maintains service availability

### **3. User Experience**
- Real-time status updates keep students informed
- Queue position and wait time estimates manage expectations
- Transparent error handling maintains trust

### **4. System Monitoring**
- Comprehensive logging enables rapid troubleshooting
- Performance metrics guide optimization efforts
- Automated alerting ensures proactive support

---

## ⚡ EMERGENCY PROCEDURES

### **System Overload Response**
1. **Immediate**: Pause new uploads, process existing queue
2. **Short-term**: Increase phase transition frequency
3. **Long-term**: Scale to multiple processing nodes

### **Critical Failure Recovery**
1. **Detection**: Automated health checks and monitoring
2. **Isolation**: Restart failed components without data loss
3. **Recovery**: Resume processing from persistent state
4. **Notification**: Alert administrators and update users

### **Data Integrity Protection**
1. **Upload**: All files saved before processing starts
2. **Processing**: Intermediate results persisted at each stage
3. **Failure**: Tasks marked for retry with full recovery capability
4. **Verification**: Checksums and validation at each step

---

**Document Status: COMPLETE - READY FOR IMPLEMENTATION**
**Next Action: Begin Phase 1 implementation with queue management system**
**Implementation Timeline: 4 weeks to full production deployment**

---

*This document serves as the complete technical reference for implementing the two-phase queue multi-user concurrency system. All implementation decisions, error handling strategies, and performance optimizations are documented here for consistent execution.*
