#!/usr/bin/env python3
"""
ConvAI Performance Monitor
Real-time system performance tracking and optimization alerts

Date: June 11, 2025
Purpose: Monitor system performance and provide optimization insights
"""

import time
import psutil
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Import queue-related classes
from app.llm.queue_manager import TaskStatus

@dataclass
class PerformanceMetrics:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_processes: int
    database_size_mb: float
    file_count: Dict[str, int]
    response_times: Dict[str, float]
    queue_status: Dict[str, int]
    
class ConvAIPerformanceMonitor:
    """Real-time performance monitoring for ConvAI system"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent
        self.metrics_history: List[PerformanceMetrics] = []
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_usage_percent': 90.0,
            'response_time': 5.0,  # seconds
            'queue_backlog': 10     # number of tasks
        }
        
    def collect_system_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive system performance metrics"""
        
        # System resource metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.project_root))
        
        # Process metrics
        active_processes = len([p for p in psutil.process_iter() if p.is_running()])
        
        # Database metrics
        db_path = self.project_root / "users.db"
        database_size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0
        
        # File system metrics
        file_count = self._count_files_by_type()
        
        # Response time metrics (simulate with file operation timing)
        response_times = self._measure_response_times()
        
        # Queue status (if queue system is available)
        queue_status = self._get_queue_status()
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=(disk.used / disk.total) * 100,
            active_processes=active_processes,
            database_size_mb=database_size_mb,
            file_count=file_count,
            response_times=response_times,
            queue_status=queue_status
        )
        
        self.metrics_history.append(metrics)
        
        # Keep only last 100 metrics to prevent memory bloat
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
            
        return metrics
    
    def _count_files_by_type(self) -> Dict[str, int]:
        """Count files in each main directory"""
        counts = {}
        
        for directory in ['videos', 'transcription', 'filled_forms', 'ratings']:
            dir_path = self.project_root / directory
            if dir_path.exists():
                counts[directory] = len(list(dir_path.rglob('*.*')))
            else:
                counts[directory] = 0
                
        return counts
    
    def _measure_response_times(self) -> Dict[str, float]:
        """Measure response times for key operations"""
        times = {}
        
        # Database query time
        start_time = time.time()
        try:
            db_path = self.project_root / "users.db"
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                cursor.fetchone()
                conn.close()
            times['database_query'] = time.time() - start_time
        except Exception:
            times['database_query'] = -1  # Error indicator
        
        # File system operation time
        start_time = time.time()
        try:
            test_files = list(self.project_root.glob('*.py'))[:5]  # Sample 5 Python files
            for file_path in test_files:
                file_path.stat()  # Just stat, don't read
            times['file_operations'] = time.time() - start_time
        except Exception:
            times['file_operations'] = -1
            
        return times
    
    def _get_queue_status(self) -> Dict[str, int]:
        """Get current queue system status"""
        try:
            # Try to import and check queue manager
            from app.llm.queue_manager import TwoPhaseQueueManager
            
            # This would normally connect to running queue manager
            # For now, return simulated data
            try:
                # Look for an existing queue manager instance in the main module
                import main
                if hasattr(main, 'queue_manager') and main.queue_manager is not None:
                    manager = main.queue_manager
                    return {
                        'stt_queue': manager.stt_queue.qsize(),
                        'evaluation_queue': manager.evaluation_queue.qsize(),
                        'completed_tasks': manager.stats.get('completed_tasks', 0),
                        'failed_tasks': manager.stats.get('failed_tasks', 0),
                        'current_phase': manager.current_phase.value,
                        'phase_switch_count': manager.stats.get('phase_switch_count', 0),
                        'processing_active': manager.processing_active,
                        'total_tasks': manager.stats.get('total_tasks', 0),
                        'average_wait_time': self._calculate_average_wait_time(manager),
                        'task_completion_rate': self._calculate_completion_rate(manager),
                        'error_rate': self._calculate_error_rate(manager)
                    }
            except (ImportError, AttributeError) as e:
                print(f"Unable to access live queue manager: {e}")
                
            # Fallback to simulated data
            return {
                'stt_queue': 0,
                'evaluation_queue': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'current_phase': 'idle',
                'phase_switch_count': 0,
                'processing_active': False,
                'total_tasks': 0,
                'average_wait_time': 0,
                'task_completion_rate': 0,
                'error_rate': 0
            }
        except Exception as e:
            print(f"Error retrieving queue status: {e}")
            return {
                'stt_queue': -1,  # Error indicators
                'evaluation_queue': -1,
                'completed_tasks': -1,
                'failed_tasks': -1,
                'error': str(e)
            }
            
    def _calculate_average_wait_time(self, queue_manager) -> float:
        """Calculate average wait time based on completed tasks"""
        try:
            # Get timestamps of completed tasks
            completed_tasks = [task for task in queue_manager.task_registry.values() 
                              if task.status == TaskStatus.COMPLETE]
            
            if not completed_tasks:
                return 0
                
            # Calculate wait times
            wait_times = []
            for task in completed_tasks:
                if 'stt_start' in task.phase_timestamps and task.created_at:
                    wait_time = (task.phase_timestamps['stt_start'] - task.created_at).total_seconds()
                    wait_times.append(wait_time)
                    
            if not wait_times:
                return 0
                
            return sum(wait_times) / len(wait_times)
        except Exception as e:
            print(f"Error calculating average wait time: {e}")
            return 0
            
    def _calculate_completion_rate(self, queue_manager) -> float:
        """Calculate task completion rate (completed tasks / total tasks)"""
        try:
            total = queue_manager.stats.get('total_tasks', 0)
            if total == 0:
                return 0
                
            completed = queue_manager.stats.get('completed_tasks', 0)
            return (completed / total) * 100
        except Exception as e:
            print(f"Error calculating completion rate: {e}")
            return 0
            
    def _calculate_error_rate(self, queue_manager) -> float:
        """Calculate task error rate (failed tasks / total tasks)"""
        try:
            total = queue_manager.stats.get('total_tasks', 0)
            if total == 0:
                return 0
                
            failed = queue_manager.stats.get('failed_tasks', 0)
            return (failed / total) * 100
        except Exception as e:
            print(f"Error calculating error rate: {e}")
            return 0
    
    def check_alerts(self, metrics: PerformanceMetrics) -> List[str]:
        """Check for performance alerts and return alert messages"""
        alerts = []
        
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append(f"🔥 HIGH CPU USAGE: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append(f"🧠 HIGH MEMORY USAGE: {metrics.memory_percent:.1f}%")
        
        if metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
            alerts.append(f"💾 HIGH DISK USAGE: {metrics.disk_usage_percent:.1f}%")
        
        for operation, response_time in metrics.response_times.items():
            if response_time > self.alert_thresholds['response_time']:
                alerts.append(f"⏱️ SLOW {operation.upper()}: {response_time:.2f}s")
        
        # Check queue backlog
        total_queued = metrics.queue_status.get('stt_queue', 0) + metrics.queue_status.get('evaluation_queue', 0)
        if total_queued > self.alert_thresholds['queue_backlog']:
            alerts.append(f"📋 QUEUE BACKLOG: {total_queued} tasks")
            
        return alerts
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No metrics collected yet"}
        
        latest = self.metrics_history[-1]
        
        # Calculate averages over last 10 measurements
        recent_metrics = self.metrics_history[-10:]
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        
        # Performance trends
        if len(self.metrics_history) >= 2:
            cpu_trend = latest.cpu_percent - self.metrics_history[-2].cpu_percent
            memory_trend = latest.memory_percent - self.metrics_history[-2].memory_percent
        else:
            cpu_trend = 0
            memory_trend = 0
        
        # Generate alerts
        alerts = self.check_alerts(latest)
        
        report = {
            "timestamp": latest.timestamp,
            "current_metrics": asdict(latest),
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2)
            },
            "trends": {
                "cpu_trend": round(cpu_trend, 2),
                "memory_trend": round(memory_trend, 2)
            },
            "alerts": alerts,
            "system_health": self._calculate_health_score(latest),
            "recommendations": self._generate_recommendations(latest, alerts)
        }
        
        return report
    
    def _calculate_health_score(self, metrics: PerformanceMetrics) -> Dict[str, str]:
        """Calculate overall system health score"""
        score = 100
        
        # Deduct points for high resource usage
        if metrics.cpu_percent > 70: score -= 15
        elif metrics.cpu_percent > 50: score -= 5
        
        if metrics.memory_percent > 80: score -= 15
        elif metrics.memory_percent > 60: score -= 5
        
        if metrics.disk_usage_percent > 85: score -= 10
        elif metrics.disk_usage_percent > 70: score -= 3
        
        # Deduct for slow response times
        for response_time in metrics.response_times.values():
            if response_time > 2.0: score -= 10
            elif response_time > 1.0: score -= 5
        
        # Determine health status
        if score >= 90:
            status = "🟢 EXCELLENT"
        elif score >= 75:
            status = "🟡 GOOD"
        elif score >= 50:
            status = "🟠 NEEDS ATTENTION"
        else:
            status = "🔴 CRITICAL"
        
        return {
            "score": score,
            "status": status
        }
    
    def _generate_recommendations(self, metrics: PerformanceMetrics, alerts: List[str]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if metrics.cpu_percent > 70:
            recommendations.append("Consider upgrading CPU or reducing concurrent processes")
        
        if metrics.memory_percent > 80:
            recommendations.append("Clear cache files or increase system RAM")
        
        if metrics.disk_usage_percent > 80:
            recommendations.append("Archive old files or expand storage capacity")
        
        # Check for inefficient file operations
        file_ops_time = metrics.response_times.get('file_operations', 0)
        if file_ops_time > 1.0:
            recommendations.append("Consider SSD upgrade for faster file operations")
        
        # Database optimization
        if metrics.database_size_mb > 100:
            recommendations.append("Consider database optimization and cleanup")
        
        if not alerts:
            recommendations.append("System is performing optimally! 🚀")
        
        return recommendations
    
    def save_metrics_to_file(self, filename: str = None):
        """Save performance metrics to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        metrics_file = self.project_root / filename
        
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(m) for m in self.metrics_history], f, indent=2)
        
        print(f"📊 Performance metrics saved to: {metrics_file}")

def main():
    """Main monitoring function"""
    print("🚀 ConvAI Performance Monitor")
    print("=" * 50)
    
    monitor = ConvAIPerformanceMonitor()
    
    try:
        # Collect current metrics
        print("📊 Collecting performance metrics...")
        metrics = monitor.collect_system_metrics()
        
        # Generate and display report
        print("\n📋 Performance Report:")
        report = monitor.generate_performance_report()
        
        print(f"⏰ Timestamp: {report['timestamp']}")
        print(f"🖥️  CPU Usage: {report['current_metrics']['cpu_percent']:.1f}%")
        print(f"🧠 Memory Usage: {report['current_metrics']['memory_percent']:.1f}%")
        print(f"💾 Disk Usage: {report['current_metrics']['disk_usage_percent']:.1f}%")
        print(f"🗄️  Database Size: {report['current_metrics']['database_size_mb']:.1f} MB")
        
        print(f"\n📈 System Health: {report['system_health']['status']} (Score: {report['system_health']['score']}/100)")
        
        # Display alerts
        if report['alerts']:
            print("\n⚠️ ALERTS:")
            for alert in report['alerts']:
                print(f"   {alert}")
        else:
            print("\n✅ No alerts - system running smoothly!")
        
        # Display recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        
        # Display file counts
        print(f"\n📁 FILE COUNTS:")
        for directory, count in report['current_metrics']['file_count'].items():
            print(f"   {directory}: {count} files")
        
        # Save metrics
        monitor.save_metrics_to_file()
        
        print(f"\n🎯 Monitoring complete! System is {report['system_health']['status']}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

if __name__ == "__main__":
    main()
