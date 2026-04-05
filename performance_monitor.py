"""
Performance Monitoring Module for Smart Attendance System v2
Tracks system metrics and performance indicators
"""

import time
import psutil
import threading
from datetime import datetime
from collections import deque
from logger import get_logger

logger = get_logger()


class PerformanceMonitor:
    """Monitor and track system performance metrics"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        
        self.frame_times = deque(maxlen=max_history)
        self.db_query_times = deque(maxlen=max_history)
        self.camera_fps = deque(maxlen=max_history)
        self.memory_usage = deque(maxlen=max_history)
        
        self._start_time = time.time()
        self._frame_count = 0
        self._monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring thread"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self._monitoring:
            self.log_memory_usage()
            time.sleep(interval)
    
    def log_frame_processing_time(self, processing_time: float):
        """Log time taken to process a frame"""
        self.frame_times.append({
            'time': processing_time,
            'timestamp': datetime.now()
        })
    
    def log_database_query_time(self, query_time: float, query_type: str = 'unknown'):
        """Log database query execution time"""
        self.db_query_times.append({
            'time': query_time,
            'type': query_type,
            'timestamp': datetime.now()
        })
    
    def log_camera_fps(self, fps: float):
        """Log camera frames per second"""
        self.camera_fps.append({
            'fps': fps,
            'timestamp': datetime.now()
        })
        self._frame_count += 1
    
    def log_memory_usage(self):
        """Log current memory usage"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        
        self.memory_usage.append({
            'mb': memory_mb,
            'percent': process.memory_percent(),
            'timestamp': datetime.now()
        })
    
    def get_metrics(self) -> dict:
        """Get current performance metrics summary"""
        uptime = time.time() - self._start_time
        
        avg_frame_time = 0
        if self.frame_times:
            avg_frame_time = sum(f['time'] for f in self.frame_times) / len(self.frame_times)
        
        avg_db_query = 0
        if self.db_query_times:
            avg_db_query = sum(q['time'] for q in self.db_query_times) / len(self.db_query_times)
        
        avg_fps = 0
        if self.camera_fps:
            avg_fps = sum(f['fps'] for f in self.camera_fps) / len(self.camera_fps)
        
        current_memory = 0
        memory_percent = 0
        if self.memory_usage:
            current_memory = self.memory_usage[-1]['mb']
            memory_percent = self.memory_usage[-1]['percent']
        
        return {
            'uptime_seconds': uptime,
            'frames_processed': self._frame_count,
            'avg_frame_time_ms': round(avg_frame_time * 1000, 2),
            'avg_db_query_ms': round(avg_db_query * 1000, 2),
            'avg_fps': round(avg_fps, 1),
            'current_memory_mb': round(current_memory, 2),
            'memory_percent': round(memory_percent, 2),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_slow_queries(self, threshold_ms: float = 100) -> list:
        """Get database queries that exceeded threshold"""
        slow = []
        for query in self.db_query_times:
            if query['time'] * 1000 > threshold_ms:
                slow.append(query)
        return slow
    
    def get_low_fps_frames(self, threshold: float = 15) -> list:
        """Get frame samples where FPS dropped below threshold"""
        low = []
        for sample in self.camera_fps:
            if sample['fps'] < threshold:
                low.append(sample)
        return low
    
    def print_report(self):
        """Print performance report to console"""
        metrics = self.get_metrics()
        
        print("\n" + "=" * 50)
        print("  PERFORMANCE REPORT")
        print("=" * 50)
        print(f"Uptime: {metrics['uptime_seconds']:.0f}s")
        print(f"Frames Processed: {metrics['frames_processed']}")
        print(f"Avg Frame Time: {metrics['avg_frame_time_ms']}ms")
        print(f"Avg DB Query: {metrics['avg_db_query_ms']}ms")
        print(f"Avg FPS: {metrics['avg_fps']}")
        print(f"Memory: {metrics['current_memory_mb']}MB ({metrics['memory_percent']}%)")
        print(f"CPU: {metrics['cpu_percent']}%")
        print("=" * 50)
    
    def __str__(self) -> str:
        metrics = self.get_metrics()
        return (
            f"PerformanceMonitor(frames={metrics['frames_processed']}, "
            f"fps={metrics['avg_fps']}, memory={metrics['current_memory_mb']}MB)"
        )


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor
