"""
Logging infrastructure for HARVEST trading system.
Provides structured logging with rotation and different log levels.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs JSON structured logs"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields if present
        if hasattr(record, 'trade_data'):
            log_data["trade_data"] = record.trade_data
        
        if hasattr(record, 'account_data'):
            log_data["account_data"] = record.account_data
            
        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for console output"""
    
    def format(self, record):
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        level_colors = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[35m',  # Magenta
        }
        reset = '\033[0m'
        
        color = level_colors.get(record.levelname, '')
        
        return f"{color}[{timestamp}] {record.levelname:8} {record.name:20} | {record.getMessage()}{reset}"


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True
) -> logging.Logger:
    """
    Set up logging infrastructure.
    
    Args:
        log_dir: Directory to store log files
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable console logging
        enable_file: Enable file logging (human-readable)
        enable_json: Enable JSON structured logging
    
    Returns:
        Configured logger instance
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger("harvest")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler (human-readable)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(HumanReadableFormatter())
        logger.addHandler(console_handler)
    
    # File handler (human-readable, rotating)
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "harvest.log"),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s')
        )
        logger.addHandler(file_handler)
    
    # JSON structured logs (for analysis/monitoring)
    if enable_json:
        json_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "harvest_structured.json"),
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(StructuredFormatter())
        logger.addHandler(json_handler)
    
    # Trade-specific log file
    trade_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "trades.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=20
    )
    trade_handler.setLevel(logging.INFO)
    trade_handler.addFilter(lambda record: 'TRADE' in record.getMessage() or hasattr(record, 'trade_data'))
    trade_handler.setFormatter(StructuredFormatter())
    logger.addHandler(trade_handler)
    
    # Error-specific log file
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "errors.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s\n%(exc_info)s')
    )
    logger.addHandler(error_handler)
    
    logger.info("Logging infrastructure initialized")
    logger.info(f"Log directory: {os.path.abspath(log_dir)}")
    logger.info(f"Log level: {log_level}")
    
    return logger


def log_trade(logger: logging.Logger, trade_data: Dict[str, Any]):
    """Log trade execution with structured data"""
    extra = {'trade_data': trade_data}
    logger.info(f"TRADE: {trade_data.get('side', 'UNKNOWN')} {trade_data.get('symbol', 'UNKNOWN')}", extra=extra)


def log_account_state(logger: logging.Logger, account_data: Dict[str, Any]):
    """Log account state with structured data"""
    extra = {'account_data': account_data}
    logger.info(f"ACCOUNT: Equity ${account_data.get('equity', 0):,.2f}", extra=extra)


def log_error_with_context(logger: logging.Logger, error: Exception, context: Dict[str, Any]):
    """Log error with additional context"""
    logger.error(
        f"Error in {context.get('function', 'unknown')}: {str(error)}",
        exc_info=True,
        extra={'context': context}
    )


# Example usage and testing
if __name__ == '__main__':
    # Initialize logging
    logger = setup_logging(log_level="DEBUG")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test trade logging
    log_trade(logger, {
        'symbol': 'BTCUSDT',
        'side': 'LONG',
        'entry': 50000.0,
        'stop': 49000.0,
        'leverage': 15.0,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Test account logging
    log_account_state(logger, {
        'equity': 10000.0,
        'daily_pnl': -150.0,
        'consecutive_losses': 1,
        'active_positions': 0
    })
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error_with_context(logger, e, {
            'function': 'test_function',
            'symbol': 'BTCUSDT',
            'operation': 'data_fetch'
        })
    
    print("\n✅ Logging test complete. Check the 'logs' directory for output files.")
