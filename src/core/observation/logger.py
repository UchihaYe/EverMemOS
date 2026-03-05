import logging
import traceback
from typing import Any, Optional
from enum import Enum
from functools import lru_cache
import sys
import os
from datetime import datetime


class LogLevel(Enum):
    """Log level enumeration"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggerProvider:
    """Unified logging management class - hybrid mode + LRU cache optimization"""

    _instance: Optional['LoggerProvider'] = None
    _initialized: bool = False

    def __new__(cls) -> 'LoggerProvider':
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the logger provider"""
        if not self._initialized:
            self._setup_logging()
            self._initialized = True

    def _setup_root_logging(self):
        """Set up logging configuration"""
        # Get log level from environment variable, default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

        # Create formatters
        standard_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'

        # Configure handlers
        handlers = [logging.StreamHandler(sys.stdout)]

        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=standard_format,
            handlers=handlers,
        )

    def _setup_logging(self):
        """Set up logging configuration"""
        self._setup_root_logging()
        self._setup_llm_logging()

        # Disable redundant logs from third-party libraries
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('google').setLevel(logging.WARNING)
        logging.getLogger('googleapiclient').setLevel(logging.WARNING)
        # Disable INFO level logs from httpx to avoid frequent HTTP request logs
        logging.getLogger('httpx').setLevel(logging.WARNING)
        # Disable debug logs from HTTP-related libraries to avoid redundant network request logs
        logging.getLogger('hpack').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        logging.getLogger('pymongo').setLevel(logging.WARNING)
        logging.getLogger('aiokafka').setLevel(logging.WARNING)
        # Disable debug logs from websockets client to avoid redundant connection logs
        # logging.getLogger('websockets.client').setLevel(logging.WARNING)

        # Setup LLM logging if enabled
        self._setup_llm_logging()

    def _setup_llm_logging(self):
        """Setup LLM call logging to separate file"""
        llm_log_enabled = os.getenv('LLM_LOG_ENABLED', 'false').lower() == 'true'
        
        if not llm_log_enabled:
            return

        llm_log_file = os.getenv('LLM_LOG_FILE', 'llm_calls.log')
        llm_format = '%(asctime)s | %(levelname)s | %(message)s'

        # Ensure directory exists
        llm_log_dir = os.path.dirname(llm_log_file)
        if llm_log_dir and not os.path.exists(llm_log_dir):
            os.makedirs(llm_log_dir, exist_ok=True)

        # Create file handler for LLM calls
        try:
            llm_handler = logging.FileHandler(llm_log_file, encoding='utf-8')
            llm_handler.setFormatter(logging.Formatter(llm_format))
            llm_handler.setLevel(logging.INFO)

            # Get or create llm_calls logger
            llm_logger = logging.getLogger('llm_calls')
            llm_logger.setLevel(logging.INFO)
            llm_logger.addHandler(llm_handler)
            
            # Prevent propagation to root logger to avoid duplicate logs
            llm_logger.propagate = False
            
            # Test write to ensure file is created
            llm_logger.info("LLM logging initialized")
        except Exception as e:
            # If file creation fails, log error but don't crash
            error_logger = logging.getLogger('llm_logging_error')
            error_logger.error(f"Failed to setup LLM logging: {e}")

    @lru_cache(maxsize=1000)
    def _get_cached_logger(self, module_name: str) -> logging.Logger:
        """Get cached logger (LRU cache, up to 1000)

        Args:
            module_name: Module name

        Returns:
            logging.Logger: Cached logger instance
        """
        return logging.getLogger(f'{module_name}')

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Get logger with specified name (recommended usage: explicitly pass module name)

        Args:
            name: Logger name, if None uses caller's module name (lower performance)

        Returns:
            logging.Logger: Logger instance
        """
        if name is None:
            # Get caller's module name (convenient but lower performance)
            frame = sys._getframe(1)
            name = frame.f_globals.get('__name__', 'unknown')

        # Use LRU cache to avoid repeatedly creating logger
        return self._get_cached_logger(name)

    def debug(self, message: str, *args, **kwargs):
        """Log debug information"""
        logger = self._get_caller_logger()
        logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log information"""
        logger = self._get_caller_logger()
        logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning"""
        logger = self._get_caller_logger()
        logger.warning(message, *args, **kwargs)

    def warn(self, message: str, *args, **kwargs):
        """Log warning (alias)"""
        self.warning(message, *args, **kwargs)

    def error(self, message: str, exc_info: bool = True, *args, **kwargs):
        """Log error information

        Args:
            message: Error message
            exc_info: Whether to include exception stack trace, default True
        """
        logger = self._get_caller_logger()
        logger.error(message, exc_info=exc_info, *args, **kwargs)

    def exception(self, message: str, exc_info: bool = True, *args, **kwargs):
        """Log exception information (automatically includes stack trace)

        Args:
            message: Exception message
            exc_info: Whether to include exception stack trace, default True
        """
        logger = self._get_caller_logger()
        logger.exception(message, exc_info=exc_info, *args, **kwargs)

    def critical(self, message: str, exc_info: bool = True, *args, **kwargs):
        """Log critical error information

        Args:
            message: Error message
            exc_info: Whether to include exception stack trace, default True
        """
        logger = self._get_caller_logger()
        logger.critical(message, exc_info=exc_info, *args, **kwargs)

    def log_with_stack(self, level: LogLevel, message: str):
        """Log with full stack trace

        Args:
            level: Log level
            message: Log message
        """
        logger = self._get_caller_logger()
        stack_trace = traceback.format_stack()
        full_message = f"{message}\nStack trace:\n{''.join(stack_trace)}"

        log_method = getattr(logger, level.value.lower())
        log_method(full_message)

    def log_llm_call(self, prompt: str, response: str, model: str, **kwargs):
        """Log LLM call with input and output to separate file

        Args:
            prompt: Input prompt to LLM
            response: Output response from LLM
            model: Model name used
            **kwargs: Additional metadata (tokens, temperature, etc.)
        """
        if os.getenv('LLM_LOG_ENABLED', 'false').lower() != 'true':
            return

        # Get the llm_calls logger directly to ensure it has the file handler
        llm_logger = logging.getLogger('llm_calls')
        
        # Check if logger has file handler, if not, set it up
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in llm_logger.handlers)
        if not has_file_handler:
            llm_log_file = os.getenv('LLM_LOG_FILE', 'llm_calls.log')
            llm_format = '%(asctime)s | %(levelname)s | %(message)s'
            
            # Ensure directory exists
            llm_log_dir = os.path.dirname(llm_log_file)
            if llm_log_dir and not os.path.exists(llm_log_dir):
                os.makedirs(llm_log_dir, exist_ok=True)
            
            # Create file handler
            llm_handler = logging.FileHandler(llm_log_file, encoding='utf-8')
            llm_handler.setFormatter(logging.Formatter(llm_format))
            llm_handler.setLevel(logging.INFO)
            llm_logger.addHandler(llm_handler)
            llm_logger.setLevel(logging.INFO)
            llm_logger.propagate = False

        # Format metadata
        metadata_parts = []
        if 'tokens' in kwargs:
            metadata_parts.append(f"Tokens: {kwargs['tokens']}")
        if 'temperature' in kwargs:
            metadata_parts.append(f"Temperature: {kwargs['temperature']}")
        metadata_str = ' | '.join(metadata_parts) if metadata_parts else ''

        # Create log entry
        log_entry = f"Model: {model} | {metadata_str}\n"
        log_entry += f"=== INPUT ===\n{prompt}\n"
        log_entry += f"=== OUTPUT ===\n{response}\n"
        log_entry += "=" * 80

        llm_logger.info(log_entry)

    def log_llm_error(self, prompt: str, error: str, model: str, **kwargs):
        """Log LLM error with input and error message

        Args:
            prompt: Input prompt to LLM
            error: Error message
            model: Model name used
            **kwargs: Additional metadata
        """
        if os.getenv('LLM_LOG_ENABLED', 'false').lower() != 'true':
            return

        llm_logger = logging.getLogger('llm_calls')
        llm_logger.setLevel(logging.ERROR)

        # Format metadata
        metadata_parts = []
        if 'temperature' in kwargs:
            metadata_parts.append(f"Temperature: {kwargs['temperature']}")
        metadata_str = ' | '.join(metadata_parts) if metadata_parts else ''

        # Create log entry
        log_entry = f"Model: {model} | ERROR | {metadata_str}\n"
        log_entry += f"=== INPUT ===\n{prompt}\n"
        log_entry += f"=== ERROR ===\n{error}\n"
        log_entry += "=" * 80

        llm_logger.error(log_entry)

    def _get_caller_logger(self) -> logging.Logger:
        """Get caller's logger (with LRU cache optimization)"""
        frame = sys._getframe(2)  # Skip current method and the called logging method
        module_name = frame.f_globals.get('__name__', 'unknown')
        # Use LRU cache to avoid repeatedly creating logger
        return self._get_cached_logger(module_name)


# Create global logger provider instance
logger_provider = LoggerProvider()

# Hybrid mode interface: provide two usage methods


# Method 1: High-performance usage (recommended) - explicitly get logger, suitable for frequent calls
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger (recommended usage: explicitly pass __name__)

    Recommended usage:
        logger = get_logger(__name__)  # Get once at module top
        logger.info("High-frequency log calls")    # Use directly afterwards

    Args:
        name: Module name, recommended to pass __name__. If None, automatically get (lower performance)
    """
    return logger_provider.get_logger(name)


# Method 2: Convenient usage - directly call functions, suitable for occasional calls (with LRU cache optimization)
def debug(message: str, *args, **kwargs):
    """Log debug information (convenient usage, suitable for occasional calls)"""
    logger_provider.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log information (convenient usage, suitable for occasional calls)"""
    logger_provider.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log warning (convenient usage, suitable for occasional calls)"""
    logger_provider.warning(message, *args, **kwargs)


def warn(message: str, *args, **kwargs):
    """Log warning (alias)"""
    logger_provider.warn(message, *args, **kwargs)


def error(message: str, exc_info: bool = True, *args, **kwargs):
    """Log error information (automatically includes stack trace)"""
    logger_provider.error(message, exc_info=exc_info, *args, **kwargs)


def exception(message: str, exc_info: bool = True, *args, **kwargs):
    """Log exception information (automatically includes stack trace)"""
    logger_provider.exception(message, exc_info=exc_info, *args, **kwargs)


def critical(message: str, exc_info: bool = True, *args, **kwargs):
    """Log critical error information (automatically includes stack trace)"""
    logger_provider.critical(message, exc_info=exc_info, *args, **kwargs)


def log_with_stack(level: LogLevel, message: str):
    """Log with full stack trace"""
    logger_provider.log_with_stack(level, message)


def log_llm_call(prompt: str, response: str, model: str, **kwargs):
    """Log LLM call with input and output to separate file

    Args:
        prompt: Input prompt to LLM
        response: Output response from LLM
        model: Model name used
        **kwargs: Additional metadata (tokens, temperature, etc.)
    """
    logger_provider.log_llm_call(prompt, response, model, **kwargs)


def log_llm_error(prompt: str, error: str, model: str, **kwargs):
    """Log LLM error with input and error message

    Args:
        prompt: Input prompt to LLM
        error: Error message
        model: Model name used
        **kwargs: Additional metadata
    """
    logger_provider.log_llm_error(prompt, error, model, **kwargs)
