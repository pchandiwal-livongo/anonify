"""
Enhanced logging utility for anonify package.

Provides comprehensive audit trails with structured logging for compliance
and debugging purposes.
"""

import logging
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import sys


class AuditLogger:
    """Enhanced logger with audit trail capabilities."""
    
    def __init__(self, 
                 name: str,
                 log_level: str = "INFO",
                 log_to_file: bool = False,
                 log_dir: str = "anonify_logs",
                 json_format: bool = False,
                 include_audit: bool = True):
        """
        Initialize enhanced audit logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            log_to_file: Whether to log to file
            log_dir: Directory for log files
            json_format: Whether to use JSON format for logs
            include_audit: Whether to include audit trail functionality
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_to_file = log_to_file
        self.log_dir = Path(log_dir)
        self.json_format = json_format
        self.include_audit = include_audit
        
        # Create log directory
        if self.log_to_file:
            self.log_dir.mkdir(exist_ok=True)
        
        # Setup logger
        self.logger = self._setup_logger()
        
        # Audit trail storage
        self.audit_trail = []
        
    def _setup_logger(self) -> logging.Logger:
        """Setup the logger with appropriate handlers."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        if self.json_format:
            console_formatter = JSONFormatter()
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if self.log_to_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = self.log_dir / f"{self.name}_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(self.log_level)
            
            if self.json_format:
                file_formatter = JSONFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Also create audit-specific log file
            if self.include_audit:
                audit_file = self.log_dir / f"audit_{self.name}_{timestamp}.jsonl"
                self.audit_file_path = audit_file
        
        return logger
    
    def log_audit_event(self, 
                       event_type: str, 
                       details: Dict[str, Any],
                       level: str = "INFO") -> None:
        """
        Log an audit event with structured data.
        
        Args:
            event_type: Type of audit event (e.g., 'ANONYMIZATION_START', 'COLUMN_PROCESSED')
            details: Dictionary with event details
            level: Log level
        """
        if not self.include_audit:
            return
            
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'logger_name': self.name,
            'level': level,
            'details': details,
            'session_id': getattr(self, 'session_id', None)
        }
        
        # Store in memory
        self.audit_trail.append(audit_entry)
        
        # Log to main logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"AUDIT: {event_type} - {json.dumps(details)}")
        
        # Append to audit file
        if hasattr(self, 'audit_file_path'):
            try:
                with open(self.audit_file_path, 'a') as f:
                    f.write(json.dumps(audit_entry) + '\n')
            except Exception as e:
                self.logger.warning(f"Failed to write audit entry: {e}")
    
    def start_session(self, session_details: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new audit session.
        
        Args:
            session_details: Additional session information
            
        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.session_id = session_id
        
        details = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            **(session_details or {})
        }
        
        self.log_audit_event('SESSION_START', details)
        return session_id
    
    def end_session(self, session_summary: Optional[Dict[str, Any]] = None) -> None:
        """
        End the current audit session.
        
        Args:
            session_summary: Summary information for the session
        """
        if not hasattr(self, 'session_id'):
            return
            
        details = {
            'session_id': self.session_id,
            'end_time': datetime.now().isoformat(),
            'total_events': len(self.audit_trail),
            **(session_summary or {})
        }
        
        self.log_audit_event('SESSION_END', details)
    
    def log_anonymization_start(self, 
                               input_shape: tuple, 
                               config: Dict[str, Any],
                               input_file: Optional[str] = None) -> None:
        """Log the start of anonymization process."""
        details = {
            'input_shape': input_shape,
            'total_records': input_shape[0] if input_shape else 0,
            'total_columns': input_shape[1] if input_shape else 0,
            'input_file': input_file,
            'config_columns': list(config.get('columns', {}).keys()) if config else [],
            'anonymization_methods': self._extract_methods_from_config(config)
        }
        self.log_audit_event('ANONYMIZATION_START', details)
    
    def log_column_processing(self, 
                            column_name: str, 
                            method: str, 
                            parameters: Dict[str, Any],
                                                         original_stats: Optional[Dict[str, Any]] = None,
                             processing_time: Optional[float] = None) -> None:
        """Log processing of individual column."""
        details = {
            'column_name': column_name,
            'method': method,
            'parameters': parameters,
            'original_stats': original_stats,
            'processing_time_ms': processing_time * 1000 if processing_time else None
        }
        self.log_audit_event('COLUMN_PROCESSED', details)
    
    def log_anonymization_complete(self, 
                                 output_shape: tuple,
                                 processing_time: Optional[float] = None,
                                 output_file: Optional[str] = None,
                                 scores: Optional[Dict[str, Any]] = None) -> None:
        """Log completion of anonymization process."""
        details = {
            'output_shape': output_shape,
            'total_processing_time_ms': processing_time * 1000 if processing_time else None,
            'output_file': output_file,
            'anonymization_score': scores.get('anonify_score') if scores else None,
            'score_interpretation': scores.get('score_interpretation') if scores else None
        }
        self.log_audit_event('ANONYMIZATION_COMPLETE', details)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with context."""
        details = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        self.log_audit_event('ERROR', details, level='ERROR')
    
    def export_audit_trail(self, 
                          output_file: str,
                          format_type: str = 'json') -> str:
        """
        Export audit trail to file.
        
        Args:
            output_file: Path to output file
            format_type: Export format ('json', 'csv')
            
        Returns:
            Path to exported file
        """
        output_path = Path(output_file)
        
        if format_type == 'json':
            with open(output_path, 'w') as f:
                json.dump(self.audit_trail, f, indent=2)
        elif format_type == 'csv':
            if self.audit_trail:
                fieldnames = set()
                for entry in self.audit_trail:
                    fieldnames.update(entry.keys())
                    if 'details' in entry and isinstance(entry['details'], dict):
                        fieldnames.update([f"details.{k}" for k in entry['details'].keys()])
                
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                    writer.writeheader()
                    
                    for entry in self.audit_trail:
                        row = entry.copy()
                        if 'details' in row and isinstance(row['details'], dict):
                            for k, v in row['details'].items():
                                row[f'details.{k}'] = v
                            del row['details']
                        writer.writerow(row)
        
        self.logger.info(f"Audit trail exported to {output_path}")
        return str(output_path)
    
    def _extract_methods_from_config(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract anonymization methods from configuration."""
        if not config or 'columns' not in config:
            return {}
            
        methods = {}
        for column, column_config in config['columns'].items():
            methods[column] = list(column_config.keys())
        
        return methods
    
    # Standard logging methods
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        self.logger.error(message, extra=extra)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra') and record.extra:
            log_entry.update(record.extra)
        
        return json.dumps(log_entry)


def setup_logger(name: str, 
                log_level: str = "INFO",
                enhanced: bool = True,
                log_to_file: bool = False,
                **kwargs) -> Union[logging.Logger, AuditLogger]:
    """
    Setup logger with optional enhanced audit capabilities.
    
    Args:
        name: Logger name
        log_level: Logging level
        enhanced: Whether to use enhanced audit logger
        **kwargs: Additional arguments for AuditLogger
        
    Returns:
        Logger instance
    """
    if enhanced:
        return AuditLogger(name, log_level=log_level, log_to_file=log_to_file, **kwargs)
    else:
        # Fallback to basic logger
        logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level.upper()))
        return logger


# Convenience function for backwards compatibility
def get_audit_logger(name: str = "anonify", **kwargs) -> AuditLogger:
    """Get an audit logger instance."""
    return AuditLogger(name, **kwargs)
