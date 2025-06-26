"""
Optimized Centralized Logging Configuration for ConvAi-IntroEval

This module provides production-ready logging configuration to eliminate performance
bottlenecks from excessive print statements and inefficient logging practices.

Key optimizations:
- Structured logging with appropriate levels
- Minimal overhead formatters
- Performance-focused configuration
- Centralized control for all modules
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Create logs directory
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class PerformanceFormatter(logging.Formatter):
    """Optimized formatter that reduces CPU overhead"""
    
    def format(self, record):
        # Only add timestamp for WARNING and above in production
        if record.levelno >= logging.WARNING:
            return f"{datetime.now().strftime('%H:%M:%S')} [{record.levelname}] {record.getMessage()}"
        else:
            # For DEBUG/INFO, use minimal formatting to reduce overhead
            return f"[{record.levelname}] {record.getMessage()}"

def setup_production_logging(
    debug_mode: bool = False, 
    log_to_file: bool = True,
    console_level: int = logging.INFO
):
    """
    Set up optimized logging configuration for production use
    
    Args:
        debug_mode: Enable debug logging (use sparingly in production)
        log_to_file: Enable file logging
        console_level: Minimum level for console output
    """
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler with optimized formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(PerformanceFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        log_file = LOGS_DIR / f"convai_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        )
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return root_logger

def get_optimized_logger(name: str) -> logging.Logger:
    """Get a logger instance optimized for the given module"""
    return logging.getLogger(name)

def log_performance_metric(operation: str, duration: float, threshold: float = 1.0):
    """Log performance metrics only if duration exceeds threshold (reduces log noise)"""
    if duration > threshold:
        logger = get_optimized_logger('performance')
        logger.warning(f"SLOW OPERATION: {operation} took {duration:.2f}s (threshold: {threshold}s)")

def configure_queue_logging():
    """Configure logging specifically for queue manager with reduced verbosity"""
    queue_logger = get_optimized_logger('queue_manager')
    
    # In production, only log important events
    # DEBUG and INFO logs should be minimal for performance
    queue_logger.setLevel(logging.INFO)
    
    return queue_logger

def configure_stt_logging():
    """Configure logging for STT module with performance focus"""
    stt_logger = get_optimized_logger('stt')
    
    # STT operations are CPU-intensive, minimize logging overhead
    stt_logger.setLevel(logging.INFO)
    
    return stt_logger

# Initialize default logger
logger = get_optimized_logger(__name__)

# Default setup call
setup_production_logging()

# Export commonly used functions
__all__ = [
    'setup_production_logging',
    'get_optimized_logger', 
    'log_performance_metric',
    'configure_queue_logging',
    'configure_stt_logging',
    'logger'
]
