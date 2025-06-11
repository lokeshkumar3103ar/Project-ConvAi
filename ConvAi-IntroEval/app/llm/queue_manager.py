"""
Two-Phase Queue Manager for ConvAi-IntroEval
Implements STT Queue → Evaluation Queue strategy with Mistral LLM

Phase 1: STT processing (sequential)
Phase 2: Form extraction and Rating (Mistral only)

Author: RTX Analysis Implementation - Cleaned Version
Date: June 10, 2025
"""

import json
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, List, Optional
from dataclasses import dataclass
import requests

# Import existing modules
from .utils import DISABLE_LLM
from .form_extractor import extract_fields_from_transcript
from .profile_rater_updated import evaluate_profile_rating
from .intro_rater_updated import evaluate_intro_rating_sync

# Import STT function and file organizer
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from stt import transcribe_file
from file_organizer import organize_path, log_file_operation

class PhaseType(Enum):
    STT_PHASE = "stt_phase"
    EVALUATION_PHASE = "evaluation_phase"
    IDLE = "idle"

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    STT_COMPLETE = "stt_complete"
    FORM_COMPLETE = "form_complete"
    RATING_COMPLETE = "rating_complete"
    FAILED = "failed"
    COMPLETE = "complete"

@dataclass
class ProcessingTask:
    """Represents a single student's processing task"""
    user_id: str
    roll_number: str
    file_path: str
    transcript_path: Optional[str] = None
    form_path: Optional[str] = None
    profile_rating_path: Optional[str] = None
    intro_rating_path: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    phase_timestamps: Dict[str, datetime] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.phase_timestamps is None:
            self.phase_timestamps = {}

class TwoPhaseQueueManager:
    """
    Manages two-phase processing with mutual exclusion:
    Phase 1: STT Queue (sequential processing)
    Phase 2: Evaluation Queue (Mistral pipeline for both form extraction and rating)
    """
    def __init__(self, test_mode: bool = False):
        # Queue management
        self.stt_queue = Queue()
        self.evaluation_queue = Queue()
        self.task_registry: Dict[str, ProcessingTask] = {}
        
        # Phase management
        self.current_phase = PhaseType.IDLE
        self.phase_lock = threading.Lock()
        self.processing_active = False
        
        # Worker threads
        self.stt_worker_thread = None
        self.evaluation_worker_thread = None
        self.monitor_thread = None
        
        # Test mode configuration
        self.test_mode = test_mode
        
        # Configuration
        self.stt_timeout = 30  # 30 seconds timeout per STT task
        self.evaluation_timeout = 60  # 60 seconds timeout per evaluation
        
        # Mistral endpoint (single LLM for all tasks)
        self.mistral_endpoint = "http://localhost:11434/api/generate"
        
        # Initialize processing times tracking
        self._processing_times = []
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "current_phase_start": None,
            "phase_switch_count": 0
        }
        
        mode_str = "TEST MODE" if test_mode else "PRODUCTION MODE"
        print(f"🚀 TwoPhaseQueueManager initialized ({mode_str})")
        if not test_mode:
            print(f"📊 Mistral endpoint: {self.mistral_endpoint}")
        else:
            print("🧪 Test mode: File processing will be mocked")
            
    def submit_task(self, user_id: str, roll_number: str, file_path: str) -> str:
        """Submit a task for processing"""
        print(f"📋 Submitting task: user_id={user_id}, roll_number={roll_number}")
        # Ensure roll_number is meaningful, use user_id if no roll_number
        if not roll_number:
            roll_number = user_id
            print(f"⚠️ Using user_id as roll_number: {roll_number}")
        elif roll_number == user_id:
            # If roll_number is same as user_id, just use it as-is
            print(f"✅ Using consistent roll_number: {roll_number}")
        
        return self._add_task(user_id, roll_number, file_path)

    def _add_task(self, user_id: str, roll_number: str, file_path: str) -> str:
        """Add a new processing task to STT queue"""
        # Validate inputs
        if not user_id or not isinstance(user_id, str):
            raise ValueError("Invalid user_id: must be a non-empty string")
            
        if not roll_number or not isinstance(roll_number, str):
            raise ValueError("Invalid roll_number: must be a non-empty string")
            
        if not file_path or not isinstance(file_path, str):
            raise ValueError("Invalid file_path: must be a non-empty string")
            
        # Check if file exists or has a valid path
        if not Path(file_path).exists() and not self.test_mode:
            print(f"⚠️ Warning: File path does not exist: {file_path}")
            # Continue anyway but log the warning
        
        task = ProcessingTask(
            user_id=user_id,
            roll_number=roll_number,
            file_path=file_path
        )
        
        # Generate unique task ID with microsecond precision + user info
        timestamp = time.time()
        task_id = f"{user_id}_{roll_number}_{timestamp:.6f}".replace(".", "_")
        
        # Ensure task ID is truly unique
        counter = 1
        original_task_id = task_id
        while task_id in self.task_registry:
            task_id = f"{original_task_id}_{counter}"
            counter += 1
        
        self.task_registry[task_id] = task
        
        # Add to STT queue
        self.stt_queue.put(task_id)
        self.stats["total_tasks"] += 1
        
        print(f"📥 Added task {task_id} to STT queue (User: {user_id}, Roll: {roll_number}, Queue size: {self.stt_queue.qsize()})")
        
        # Start processing if not active
        if not self.processing_active:
            self.start_processing()
        
        return task_id
        
    def get_task_status(self, task_id: str) -> Dict:
        """Get current status of a task"""
        # Input validation
        if not task_id or not isinstance(task_id, str):
            return {
                "status": "error", 
                "message": "Invalid task_id: must be a non-empty string",
                "error_code": "INVALID_TASK_ID"
            }
            
        if task_id not in self.task_registry:
            return {
                "status": "not_found", 
                "message": f"Task not found: {task_id}",
                "error_code": "TASK_NOT_FOUND"
            }
        
        try:
            task = self.task_registry[task_id]
            status_response = {
                "task_id": task_id,
                "status": task.status.value,
                "current_phase": self.current_phase.value,
                "created_at": task.created_at.isoformat(),
                "phase_timestamps": {k: v.isoformat() for k, v in task.phase_timestamps.items()},
                "error_message": task.error_message,
                "queue_position": self._get_queue_position(task_id),
                "system_stats": self.get_system_stats(),
                # Include file paths for reference
                "transcript_path": task.transcript_path,
                "form_path": task.form_path,
                "profile_rating_path": task.profile_rating_path,
                "intro_rating_path": task.intro_rating_path
            }
            
            # If task is complete, include file contents for immediate display
            if task.status == TaskStatus.COMPLETE:
                try:
                    file_contents = self._load_task_results(task)
                    status_response["data"] = file_contents
                except Exception as e:
                    print(f"⚠️ Error loading file contents for completed task {task_id}: {e}")
                    status_response["data_load_error"] = str(e)
                    status_response["error_code"] = "FILE_LOAD_ERROR"
            
            return status_response
            
        except Exception as e:
            print(f"❌ Unexpected error in get_task_status for {task_id}: {e}")
            return {
                "status": "error",
                "message": f"System error retrieving task status: {str(e)}",
                "error_code": "SYSTEM_ERROR"
            }
            
    def _get_queue_position(self, task_id: str) -> Optional[int]:
        """Get position of task in current queue"""
        try:
            # Validate input
            if not task_id or task_id not in self.task_registry:
                return None
                
            task = self.task_registry[task_id]
            
            # Only return position for pending tasks
            if task.status != TaskStatus.PENDING:
                return 0
                
            # FIXED: Queue contains task IDs (strings), not ProcessingTask objects
            # Check STT queue - iterate through task ID strings
            stt_items = list(self.stt_queue.queue)
            for i, queued_task_id in enumerate(stt_items):
                if queued_task_id == task_id:
                    return i + 1
            
            # Check evaluation queue - iterate through task ID strings  
            eval_items = list(self.evaluation_queue.queue)
            for i, queued_task_id in enumerate(eval_items):
                if queued_task_id == task_id:
                    return i + 1
            
            # If the task is pending but not in either queue, something is wrong
            # so return a fallback position
            if task.status == TaskStatus.PENDING:
                print(f"⚠️ Warning: Task {task_id} is pending but not found in any queue")
                print(f"  - STT queue size: {self.stt_queue.qsize()}")
                print(f"  - Eval queue size: {self.evaluation_queue.qsize()}")
                print(f"  - Current phase: {self.current_phase.value}")
                print(f"  - Processing active: {self.processing_active}")
                return 1
                
            return 0
        except Exception as e:
            # Log error for debugging but return None for safe fallback
            print(f"Error calculating queue position for {task_id}: {e}")
            return 0
    
    def get_queue_position(self, task_id: str) -> Optional[int]:
        """Get position of task in current queue (public method)"""
        return self._get_queue_position(task_id)
    
    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        return {
            "current_phase": self.current_phase.value,
            "stt_queue_size": self.stt_queue.qsize(),
            "evaluation_queue_size": self.evaluation_queue.qsize(),
            "total_tasks": self.stats["total_tasks"],
            "completed_tasks": self.stats["completed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "processing_active": self.processing_active,
            "phase_switch_count": self.stats["phase_switch_count"]
        }

    def get_stats(self) -> Dict:
        """Get comprehensive queue statistics for API endpoints"""
        # Calculate average processing time
        completed_count = self.stats["completed_tasks"]
        if completed_count > 0 and hasattr(self, '_processing_times'):
            avg_time = sum(self._processing_times) / len(self._processing_times)
        else:
            avg_time = 45  # Default estimate in seconds
        
        return {
            "current_phase": self.current_phase.value,
            "stt_queue_size": self.stt_queue.qsize(),
            "evaluation_queue_size": self.evaluation_queue.qsize(),
            "queue_length": self.stt_queue.qsize() + self.evaluation_queue.qsize(),
            "active_users": len([t for t in self.task_registry.values() if t.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]]),
            "total_tasks": self.stats["total_tasks"],
            "completed_tasks": self.stats["completed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "processing_active": self.processing_active,
            "phase_switch_count": self.stats["phase_switch_count"],
            "average_processing_time": avg_time
        }

    def start_processing(self):
        """Start the two-phase processing system"""
        if self.processing_active:
            print("⚠️ Processing already active, skipping start")
            return
        
        self.processing_active = True
        print("🎬 Starting two-phase processing system")
        
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._phase_monitor, daemon=True)
        self.monitor_thread.start()
        
        # Switch to STT phase if we have tasks
        if not self.stt_queue.empty():
            self._switch_to_stt_phase()

    def stop_processing(self):
        """Stop the processing system gracefully"""
        print("🛑 Stopping two-phase processing system")
        self.processing_active = False
        
        # Wait for workers to finish current tasks
        if self.stt_worker_thread and self.stt_worker_thread.is_alive():
            self.stt_worker_thread.join(timeout=10)
        
        if self.evaluation_worker_thread and self.evaluation_worker_thread.is_alive():
            self.evaluation_worker_thread.join(timeout=10)    
    def _phase_monitor(self):
        """Monitor phases and switch when appropriate"""
        while self.processing_active:
            try:
                with self.phase_lock:
                    # Check worker thread status
                    stt_worker_active = self.stt_worker_thread and self.stt_worker_thread.is_alive()
                    eval_worker_active = self.evaluation_worker_thread and self.evaluation_worker_thread.is_alive()
                    
                    # Check queue status
                    stt_queue_has_tasks = not self.stt_queue.empty()
                    eval_queue_has_tasks = not self.evaluation_queue.empty()
                    both_queues_empty = not stt_queue_has_tasks and not eval_queue_has_tasks
                    no_active_workers = not stt_worker_active and not eval_worker_active
                    
                    # Print diagnostic info every few cycles for better debugging
                    if int(time.time()) % 10 == 0:  # Print every ~10 seconds
                        print(f"📊 Phase Monitor Status: Phase={self.current_phase.value}, STT Queue={self.stt_queue.qsize()}, " +
                              f"Eval Queue={self.evaluation_queue.qsize()}, STT Worker={stt_worker_active}, " +
                              f"Eval Worker={eval_worker_active}")
                    
                    # IDLE state handling - start appropriate phase if there are tasks
                    if self.current_phase == PhaseType.IDLE:
                        if stt_queue_has_tasks:
                            print(f"🔄 Phase Monitor: Found {self.stt_queue.qsize()} STT tasks in IDLE state, switching to STT phase")
                            self._switch_to_stt_phase()
                            continue
                        elif eval_queue_has_tasks:
                            print(f"🔄 Phase Monitor: Found {self.evaluation_queue.qsize()} evaluation tasks in IDLE state, switching to evaluation phase")
                            self._switch_to_evaluation_phase()
                            continue
                    
                    # STT phase handling
                    elif self.current_phase == PhaseType.STT_PHASE:
                        # If STT worker died but tasks remain, restart it
                        if stt_queue_has_tasks and not stt_worker_active:
                            print(f"🔄 Phase Monitor: STT worker not running but {self.stt_queue.qsize()} tasks queued, restarting worker")
                            self._switch_to_stt_phase()  # This will restart the worker
                            continue
                            
                        # If STT queue empty, switch to evaluation if tasks exist there
                        if not stt_queue_has_tasks and not stt_worker_active:
                            if eval_queue_has_tasks:
                                print(f"🔄 Phase Monitor: STT queue empty, switching to evaluation ({self.evaluation_queue.qsize()} tasks waiting)")
                                self._switch_to_evaluation_phase()
                            else:
                                print(f"🔄 Phase Monitor: All queues empty, switching to IDLE")
                                self._switch_to_idle()
                            continue
                    
                    # Evaluation phase handling
                    elif self.current_phase == PhaseType.EVALUATION_PHASE:
                        # If evaluation worker died but tasks remain, restart it
                        if eval_queue_has_tasks and not eval_worker_active:
                            print(f"🔄 Phase Monitor: Evaluation worker not running but {self.evaluation_queue.qsize()} tasks queued, restarting worker")
                            self._switch_to_evaluation_phase()  # This will restart the worker
                            continue
                            
                        # If evaluation queue empty, check for STT tasks or go idle
                        if not eval_queue_has_tasks and not eval_worker_active:
                            if stt_queue_has_tasks:
                                print(f"🔄 Phase Monitor: Evaluation queue empty, switching to STT phase ({self.stt_queue.qsize()} tasks waiting)")
                                self._switch_to_stt_phase()
                            else:
                                print(f"🔄 Phase Monitor: All queues empty, switching to IDLE")
                                self._switch_to_idle()
                            continue
                    
                    # Transition to IDLE when both queues are empty and no workers active
                    if both_queues_empty and no_active_workers and self.current_phase != PhaseType.IDLE:
                        print(f"🔄 Phase Monitor: All queues empty and no active workers, switching to idle state")
                        self._switch_to_idle()
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"❌ Error in phase monitor: {e}")
                time.sleep(5)    
    def _switch_to_stt_phase(self):
        """Switch to STT processing phase and ensure worker thread is running"""
        if self.current_phase == PhaseType.STT_PHASE:
            # If already in STT phase, just ensure worker is running
            if not (self.stt_worker_thread and self.stt_worker_thread.is_alive()) and not self.stt_queue.empty():
                print("🔄 Restarting STT worker thread in existing STT phase")
                self.stt_worker_thread = threading.Thread(target=self._stt_worker, daemon=True)
                self.stt_worker_thread.start()
            return
        
        print(f"🔄 Switching to STT Phase (Queue: {self.stt_queue.qsize()} tasks)")
        self.current_phase = PhaseType.STT_PHASE
        self.stats["current_phase_start"] = datetime.now()
        self.stats["phase_switch_count"] += 1
        
        # Wait for any existing evaluation worker to finish
        if self.evaluation_worker_thread and self.evaluation_worker_thread.is_alive():
            print("⏳ Waiting for evaluation worker to finish...")
            self.evaluation_worker_thread.join(timeout=5)
        
        # Start STT worker (only if not already running)
        if not (self.stt_worker_thread and self.stt_worker_thread.is_alive()):
            self.stt_worker_thread = threading.Thread(target=self._stt_worker, daemon=True)
            self.stt_worker_thread.start()
            print("🎤 Started new STT worker thread")    
    def _switch_to_evaluation_phase(self):
        """Switch to evaluation processing phase and ensure worker thread is running"""
        if self.current_phase == PhaseType.EVALUATION_PHASE:
            # If already in evaluation phase, just ensure worker is running
            if not (self.evaluation_worker_thread and self.evaluation_worker_thread.is_alive()) and not self.evaluation_queue.empty():
                print("🔄 Restarting evaluation worker thread in existing evaluation phase")
                self.evaluation_worker_thread = threading.Thread(target=self._evaluation_worker, daemon=True)
                self.evaluation_worker_thread.start()
            return
        
        print(f"🔄 Switching to Evaluation Phase (Queue: {self.evaluation_queue.qsize()} tasks)")
        self.current_phase = PhaseType.EVALUATION_PHASE
        self.stats["current_phase_start"] = datetime.now()
        self.stats["phase_switch_count"] += 1
        
        # Wait for any existing STT worker to finish current task
        if self.stt_worker_thread and self.stt_worker_thread.is_alive():
            print("⏳ Waiting for STT worker to finish current task...")
            self.stt_worker_thread.join(timeout=5)
            
        # Start evaluation worker (only if not already running)
        if not (self.evaluation_worker_thread and self.evaluation_worker_thread.is_alive()):
            self.evaluation_worker_thread = threading.Thread(target=self._evaluation_worker, daemon=True)
            self.evaluation_worker_thread.start()
            print("🧠 Started new evaluation worker thread")
    def _switch_to_idle(self):
        """Switch to idle state, ready to process new tasks when they arrive"""
        if self.current_phase == PhaseType.IDLE:
            return
        
        print("😴 Switching to Idle state - waiting for new tasks")
        self.current_phase = PhaseType.IDLE
        self.stats["current_phase_start"] = datetime.now()
        
        # Ensure we have no lingering references to stopped worker threads
        # This is important for proper detection of thread state in the monitor
        if self.stt_worker_thread and not self.stt_worker_thread.is_alive():
            self.stt_worker_thread = None
            
        if self.evaluation_worker_thread and not self.evaluation_worker_thread.is_alive():
            self.evaluation_worker_thread = None
        
        # Double-check queues one last time to prevent race conditions
        if not self.stt_queue.empty():
            print("⚠️ Found STT tasks during idle switch, reverting to STT phase")
            self._switch_to_stt_phase()
        elif not self.evaluation_queue.empty():
            print("⚠️ Found evaluation tasks during idle switch, reverting to evaluation phase")
            self._switch_to_evaluation_phase()    
    def _stt_worker(self):
        """Worker for STT phase - processes STT queue sequentially"""
        print("🎤 STT worker started")
        
        # Continue processing while active AND either still in STT phase OR has queued tasks
        while self.processing_active:
            try:
                # Check if phase has changed before getting a new task
                if self.current_phase != PhaseType.STT_PHASE:
                    print("🎤 STT worker: Phase changed to " + self.current_phase.value + ", stopping worker")
                    break
                
                # Get task from STT queue (with timeout)
                try:
                    task_id = self.stt_queue.get(timeout=5)
                except Empty:
                    print("🎤 STT worker: Queue is empty, checking for phase change")
                    if self.stt_queue.empty() and not self.evaluation_queue.empty():
                        # Suggest phase transition if evaluation queue has tasks
                        print("🎤 STT worker: Suggesting phase transition to evaluation")
                        with self.phase_lock:
                            if self.current_phase == PhaseType.STT_PHASE:
                                self._switch_to_evaluation_phase()
                        break
                    continue
                
                if task_id not in self.task_registry:
                    print(f"⚠️ Task {task_id} not found in registry")
                    continue
                
                task = self.task_registry[task_id]
                print(f"🎤 Processing STT for task {task_id} (user: {task.user_id}, roll: {task.roll_number})")
                
                # Update task status
                task.status = TaskStatus.PROCESSING
                task.phase_timestamps["stt_start"] = datetime.now()
                
                # Process STT - Complete this task regardless of phase changes
                try:
                    # Wait for file to be available
                    file_path = Path(task.file_path)
                    max_wait_time = 10  # seconds
                    wait_interval = 0.5
                    total_wait = 0
                    
                    while not file_path.exists() and total_wait < max_wait_time:
                        print(f"⏳ Waiting for file: {file_path} (waited {total_wait:.1f}s)")
                        time.sleep(wait_interval)
                        total_wait += wait_interval
                    if not file_path.exists():
                        raise FileNotFoundError(f"File not found after waiting {max_wait_time}s: {file_path}")
                    
                    if self.test_mode:
                        # TEST MODE: Mock STT processing
                        print(f"🧪 TEST MODE: Mocking STT for {task.file_path}")
                        time.sleep(1)  # Simulate processing time
                        
                        # Create mock transcript
                        transcript_content = f"Mock transcript for {task.user_id} (Roll: {task.roll_number}). This is a test introduction."
                        
                        # Create mock transcript file
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        transcript_filename = f"transcript_{timestamp}.txt"
                        transcript_path = organize_path("transcription", transcript_filename, task.roll_number)
                        transcript_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(transcript_path, 'w', encoding='utf-8') as f:
                            f.write(transcript_content)
                        
                        task.transcript_path = str(transcript_path)
                        log_file_operation("CREATE mock transcript", transcript_path, task.roll_number)
                    else:
                        # PRODUCTION MODE: Real STT processing
                        print(f"🎤 Starting transcription for {task.file_path}")
                        transcript_content, transcript_path = transcribe_file(
                            file_path, 
                            Path("transcription"),
                            task.roll_number
                        )
                        
                        task.transcript_path = str(transcript_path)
                        log_file_operation("CREATE transcript", transcript_path, task.roll_number)
                    
                    task.status = TaskStatus.STT_COMPLETE
                    task.phase_timestamps["stt_complete"] = datetime.now()
                    
                    # Add to evaluation queue
                    self.evaluation_queue.put(task_id)
                    print(f"✅ STT complete for {task_id}: {transcript_path}")
                    print(f"📋 Added {task_id} to evaluation queue (size: {self.evaluation_queue.qsize()})")
                    
                    # Mark task as completed in the queue
                    self.stt_queue.task_done()
                    
                except Exception as e:
                    print(f"❌ STT failed for {task_id}: {e}")
                    task.status = TaskStatus.FAILED
                    task.error_message = f"STT processing failed: {e}"
                    self.stats["failed_tasks"] += 1
                    
                    # Mark task as completed in the queue even on failure
                    try:
                        self.stt_queue.task_done()
                    except Exception:
                        pass
                
            except Exception as e:
                print(f"❌ Error in STT worker: {e}")
                time.sleep(1)
        
        print("🎤 STT worker stopped")
        
        # After worker stops, check if the phase needs transition
        # This ensures proper phase transitions when the worker exits
        if self.current_phase == PhaseType.STT_PHASE:
            with self.phase_lock:
                if self.stt_queue.empty() and not self.evaluation_queue.empty():
                    print("🔄 STT worker exited: Recommending switch to evaluation phase")
                    self._switch_to_evaluation_phase()
                elif self.stt_queue.empty() and self.evaluation_queue.empty():
                    print("🔄 STT worker exited: Recommending switch to idle state")
                    self._switch_to_idle()
    def _evaluation_worker(self):
        """Worker for evaluation phase - processes with Mistral pipeline"""
        print("🧠 Evaluation worker started")
        
        # Continue processing while active AND either still in EVALUATION phase OR has queued tasks
        while self.processing_active:
            try:
                # Check if phase has changed before getting a new task
                if self.current_phase != PhaseType.EVALUATION_PHASE:
                    print("🧠 Evaluation worker: Phase changed to " + self.current_phase.value + ", stopping worker")
                    break
                
                # Get task from evaluation queue
                try:
                    task_id = self.evaluation_queue.get(timeout=5)
                except Empty:
                    print("🧠 Evaluation worker: Queue is empty, checking for phase change")
                    if self.evaluation_queue.empty() and not self.stt_queue.empty():
                        # Suggest phase transition if STT queue has tasks
                        print("🧠 Evaluation worker: Suggesting phase transition to STT")
                        with self.phase_lock:
                            if self.current_phase == PhaseType.EVALUATION_PHASE:
                                self._switch_to_stt_phase()
                        break
                    continue
                
                if task_id not in self.task_registry:
                    print(f"⚠️ Task {task_id} not found in registry")
                    continue
                
                task = self.task_registry[task_id]
                print(f"🧠 Processing evaluation for task {task_id} (user: {task.user_id}, roll: {task.roll_number})")
                
                task.phase_timestamps["evaluation_start"] = datetime.now()
                
                # Step 1: Form extraction with Mistral
                self._process_form_extraction(task)
                
                if task.status == TaskStatus.FAILED:
                    # Mark task as completed in the queue even on failure
                    try:
                        self.evaluation_queue.task_done()
                    except Exception:
                        pass
                    continue
                
                # Step 2: Rating generation with Mistral
                self._process_rating_generation(task)
                
                # Mark task as completed in the queue
                try:
                    self.evaluation_queue.task_done()
                except Exception:
                    pass
                
                # Check if this was the last task and trigger an idle state check
                if self.evaluation_queue.empty() and self.stt_queue.empty():
                    print("🏁 All tasks complete, checking for idle state transition")
                
            except Exception as e:
                print(f"❌ Error in evaluation worker: {e}")
                time.sleep(1)
        
        print("🧠 Evaluation worker stopped")
        
        # After worker stops, check if we need to transition to idle or STT phase
        if self.current_phase == PhaseType.EVALUATION_PHASE:
            with self.phase_lock:
                if self.evaluation_queue.empty() and not self.stt_queue.empty():
                    print("🔄 Evaluation worker exited: Recommending switch to STT phase")
                    self._switch_to_stt_phase()
                elif self.evaluation_queue.empty() and self.stt_queue.empty():
                    print("🔄 Evaluation worker exited: Recommending switch to idle state")
                    self._switch_to_idle()

    def _process_form_extraction(self, task: ProcessingTask):
        """Process form extraction for a task"""
        try:
            print(f"📝 Extracting form with Mistral for {task.user_id}")
            
            if self.test_mode:
                # TEST MODE: Mock form extraction
                print(f"🧪 TEST MODE: Mocking form extraction for {task.user_id}")
                time.sleep(0.5)  # Simulate processing time
                
                # Create mock form data
                mock_form_data = {
                    "name": f"Test Student {task.roll_number}",
                    "roll_number": task.roll_number,
                    "branch": "Computer Science",
                    "year": "3rd Year",
                    "skills": ["Programming", "Communication"],
                    "interests": ["Technology", "Innovation"],
                    "test_mode": True
                }
                
                # Save mock form
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                form_filename = f"filled_form_{timestamp}.json"
                form_filepath = organize_path("filled_forms", form_filename, task.roll_number)
                form_filepath.parent.mkdir(parents=True, exist_ok=True)
                
                with open(form_filepath, 'w', encoding='utf-8') as f:
                    json.dump(mock_form_data, f, indent=2, ensure_ascii=False)
                
                task.form_path = str(form_filepath)
                log_file_operation("CREATE mock form", form_filepath, task.roll_number)
                
            elif not DISABLE_LLM and task.transcript_path:
                # PRODUCTION MODE: Real form extraction
                # Read transcript content
                with open(task.transcript_path, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                
                # Extract fields using Mistral
                form_result = extract_fields_from_transcript(transcript_content, task.roll_number)
                
                if form_result and form_result.get('status') == 'saved':
                    task.form_path = form_result.get('file', '')
                    print(f"✅ Form extraction complete: {task.form_path}")
                else:
                    # Save a basic form file if extraction didn't save one
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    form_filename = f"filled_form_{timestamp}.json"
                    form_filepath = organize_path("filled_forms", form_filename, task.roll_number)
                    form_filepath.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(form_filepath, 'w', encoding='utf-8') as f:
                        json.dump(form_result or {}, f, indent=2, ensure_ascii=False)
                    
                    task.form_path = str(form_filepath)
                    log_file_operation("CREATE form", form_filepath, task.roll_number)
            else:
                # Create placeholder if LLM disabled
                task.form_path = f"filled_forms/disabled_form_{task.user_id}_{int(time.time())}.json"
            
            task.status = TaskStatus.FORM_COMPLETE
            task.phase_timestamps["form_complete"] = datetime.now()
            print(f"✅ Form extraction complete for {task.user_id}")
            
        except Exception as e:
            print(f"❌ Form extraction failed for {task.user_id}: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = f"Form extraction failed: {e}"
            self.stats["failed_tasks"] += 1
    def _process_rating_generation(self, task: ProcessingTask):
        """Process rating generation for a task"""
        try:
            print(f"⭐ Generating ratings with Mistral for {task.user_id}")
            
            if self.test_mode:
                # Create mock ratings for testing
                print(f"📋 [TEST MODE] Creating mock ratings for {task.user_id}")
                
                mock_profile_rating = {
                    "status": "success",
                    "data": {
                        "profile_rating": "7.5/10",
                        "grading_explanation": {
                            "technical_skills": "8.0",
                            "communication": "7.0",
                            "experience": "7.5"
                        },
                        "feedback": f"Mock profile evaluation for {task.roll_number}",
                        "grading_debug": {
                            "notes": f"Test mode profile rating for student {task.roll_number}"
                        }
                    }
                }
                
                mock_intro_rating = {
                    "status": "success", 
                    "data": {
                        "intro_rating": "8.0/10",
                        "grading_explanation": {
                            "content_rating": "8.0",
                            "delivery_rating": "8.0"
                        },
                        "feedback": [f"Mock intro evaluation for {task.roll_number}"],
                        "grading_debug": {
                            "notes": f"Test mode intro rating for student {task.roll_number}"
                        }
                    }
                }
                
                # Save mock ratings
                self._save_ratings(task, mock_profile_rating, mock_intro_rating)
            elif not DISABLE_LLM and task.form_path and task.transcript_path:
                # Generate profile rating using Mistral
                profile_rating = evaluate_profile_rating(task.form_path)
                
                # Generate intro rating using Mistral
                intro_rating = evaluate_intro_rating_sync(task.transcript_path)
                
                # Save ratings
                self._save_ratings(task, profile_rating, intro_rating)
            else:
                # Create placeholder files if LLM disabled
                task.profile_rating_path = f"ratings/disabled_profile_{task.user_id}_{int(time.time())}.json"
                task.intro_rating_path = f"ratings/disabled_intro_{task.user_id}_{int(time.time())}.json"
            
            # Mark task as complete and update timestamps
            task.status = TaskStatus.COMPLETE
            task.phase_timestamps["rating_complete"] = datetime.now()
            
            # Track processing time for statistics
            if task.phase_timestamps.get("rating_complete") and task.created_at:
                processing_time = (task.phase_timestamps["rating_complete"] - task.created_at).total_seconds()
                self._processing_times.append(processing_time)
                # Keep only the last 20 processing times to ensure average is current
                if len(self._processing_times) > 20:
                    self._processing_times.pop(0)
            
            self.stats["completed_tasks"] += 1
            print(f"🎉 Task {task.user_id} completed successfully!")
            
            # Check if this was the last task in the queue
            if self.evaluation_queue.empty() and self.stt_queue.empty():
                print(f"🏁 Task {task.user_id} was the last task in the queue")
            
        except Exception as e:
            print(f"❌ Rating generation failed for {task.user_id}: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = f"Rating generation failed: {e}"
            self.stats["failed_tasks"] += 1

    def _save_ratings(self, task: ProcessingTask, profile_rating, intro_rating):
        """Save rating files for a task"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save profile rating
        if profile_rating:
            profile_filename = f"profile_rating_{timestamp}.json"
            profile_path = organize_path("ratings", profile_filename, task.roll_number)
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_rating, f, indent=2, ensure_ascii=False)
            
            task.profile_rating_path = str(profile_path)
            log_file_operation("CREATE profile_rating", profile_path, task.roll_number)
        
        # Save intro rating
        if intro_rating:
            intro_filename = f"intro_rating_{timestamp}.json"
            intro_path = organize_path("ratings", intro_filename, task.roll_number)
            intro_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(intro_path, 'w', encoding='utf-8') as f:
                json.dump(intro_rating, f, indent=2, ensure_ascii=False)
            
            task.intro_rating_path = str(intro_path)
            log_file_operation("CREATE intro_rating", intro_path, task.roll_number)

    # Additional utility methods
    def get_user_tasks(self, user_id: str, roll_number: str = None) -> List[Dict]:
        """Get all tasks for a specific user"""
        user_tasks = []
        
        for task_id, task in self.task_registry.items():
            if task.user_id == user_id and (not roll_number or task.roll_number == roll_number):
                task_info = {
                    "task_id": task_id,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "file_path": task.file_path,
                    "transcript_path": task.transcript_path,
                    "form_path": task.form_path,
                    "profile_rating_path": task.profile_rating_path,
                    "intro_rating_path": task.intro_rating_path,
                    "error_message": task.error_message,
                    "queue_position": self._get_queue_position(task_id)
                }
                
                if task.status == TaskStatus.COMPLETE:
                    task_info["data"] = self._load_task_results(task)
                
                user_tasks.append(task_info)
        
        # Sort by creation time (newest first)
        user_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        return user_tasks

    def _load_task_results(self, task: ProcessingTask) -> Dict:
        """Load the actual file contents for a completed task"""
        result = {}
        
        try:
            # Load transcript
            if task.transcript_path and Path(task.transcript_path).exists():
                with open(task.transcript_path, 'r', encoding='utf-8') as f:
                    result["transcript_content"] = f.read()
            
            # Load form data
            if task.form_path and Path(task.form_path).exists():
                with open(task.form_path, 'r', encoding='utf-8') as f:
                    result["form_data"] = json.load(f)
            
            # Load ratings
            if task.profile_rating_path and Path(task.profile_rating_path).exists():
                with open(task.profile_rating_path, 'r', encoding='utf-8') as f:
                    result["profile_rating"] = json.load(f)
            
            if task.intro_rating_path and Path(task.intro_rating_path).exists():
                with open(task.intro_rating_path, 'r', encoding='utf-8') as f:
                    result["intro_rating"] = json.load(f)
                    
        except Exception as e:
            print(f"⚠️ Error loading file contents for task: {e}")
            result["load_error"] = str(e)
        
        return result

    def get_task_results(self, task_id: str) -> Optional[Dict]:
        """Get complete results for a finished task"""
        if task_id not in self.task_registry:
            return None
        
        task = self.task_registry[task_id]
        if task.status != TaskStatus.COMPLETE:
            return {
                "task_id": task_id,
                "status": task.status.value,
                "message": "Task not yet complete",
                "current_phase": self.current_phase.value
            }
        
        results = {
            "task_id": task_id,
            "status": task.status.value,
            "user_id": task.user_id,
            "roll_number": task.roll_number,
            "file_path": task.file_path,
            "transcript_path": task.transcript_path,
            "form_path": task.form_path,
            "profile_rating_path": task.profile_rating_path,
            "intro_rating_path": task.intro_rating_path,
            "phase_timestamps": {k: v.isoformat() for k, v in task.phase_timestamps.items()},
            "processing_time": self._calculate_processing_times(task)
        }
        
        # Load actual file contents
        results.update(self._load_task_results(task))
        return results

    def _calculate_processing_times(self, task: ProcessingTask) -> Dict:
        """Calculate processing times for different phases"""
        times = {
            "total": (task.phase_timestamps.get("rating_complete", datetime.now()) - task.created_at).total_seconds()
        }
        
        if task.phase_timestamps.get("stt_complete") and task.phase_timestamps.get("stt_start"):
            times["stt"] = (task.phase_timestamps["stt_complete"] - task.phase_timestamps["stt_start"]).total_seconds()
        
        if task.phase_timestamps.get("rating_complete") and task.phase_timestamps.get("evaluation_start"):
            times["evaluation"] = (task.phase_timestamps["rating_complete"] - task.phase_timestamps["evaluation_start"]).total_seconds()
        
        return times

    def start(self):
        """Start the queue manager system"""
        self.start_processing()

    def stop(self):
        """Stop the queue manager system"""
        self.stop_processing()
