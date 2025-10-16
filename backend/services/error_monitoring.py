"""
Error Monitoring Service
Centralized error tracking and alerting
"""

import os
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)


class ErrorMonitor:
    """
    Centralized error monitoring and alerting
    """
    
    def __init__(self):
        """Initialize error monitor"""
        self.log_file = os.getenv('ERROR_LOG_FILE', '/var/log/purposeful-errors.log')
        self.alert_threshold = int(os.getenv('ERROR_ALERT_THRESHOLD', 10))
        self.error_counts = {}
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None
    ) -> None:
        """
        Log an error with context
        
        Args:
            error: Exception object
            context: Additional context dictionary
            user_id: User ID if applicable
            endpoint: API endpoint where error occurred
        """
        try:
            error_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'user_id': user_id,
                'endpoint': endpoint,
                'context': context or {}
            }
            
            # Log to application logger
            logger.error(
                f"Error: {error_data['error_type']} - {error_data['error_message']}",
                extra=error_data
            )
            
            # Write to error log file
            self._write_to_file(error_data)
            
            # Track error counts
            error_key = f"{error_data['error_type']}:{endpoint}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Check if we should alert
            if self.error_counts[error_key] >= self.alert_threshold:
                self._send_alert(error_data, self.error_counts[error_key])
                self.error_counts[error_key] = 0  # Reset counter
            
        except Exception as e:
            # Don't let error monitoring crash the app
            logger.critical(f"Error in error monitoring: {e}")
    
    def _write_to_file(self, error_data: Dict[str, Any]) -> None:
        """Write error to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(error_data) + '\n')
        except Exception as e:
            logger.critical(f"Failed to write error log: {e}")
    
    def _send_alert(self, error_data: Dict[str, Any], count: int) -> None:
        """
        Send alert for repeated errors
        
        Args:
            error_data: Error information
            count: Number of occurrences
        """
        try:
            # In production, this would send to Slack, email, or monitoring service
            alert_message = (
                f"⚠️ ERROR ALERT ⚠️\n"
                f"Error: {error_data['error_type']}\n"
                f"Endpoint: {error_data['endpoint']}\n"
                f"Occurrences: {count}\n"
                f"Message: {error_data['error_message']}\n"
                f"Time: {error_data['timestamp']}"
            )
            
            logger.critical(alert_message)
            
            # TODO: Integrate with alerting service (Slack, PagerDuty, etc.)
            # Example:
            # slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
            # if slack_webhook:
            #     requests.post(slack_webhook, json={'text': alert_message})
            
        except Exception as e:
            logger.critical(f"Failed to send error alert: {e}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get error summary for the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with error statistics
        """
        try:
            cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
            
            # Read recent errors from log file
            errors = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    for line in f:
                        try:
                            error = json.loads(line)
                            error_time = datetime.fromisoformat(error['timestamp']).timestamp()
                            if error_time >= cutoff_time:
                                errors.append(error)
                        except:
                            continue
            
            # Aggregate statistics
            error_types = {}
            endpoints = {}
            
            for error in errors:
                error_type = error.get('error_type', 'Unknown')
                endpoint = error.get('endpoint', 'Unknown')
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
                endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
            
            return {
                'total_errors': len(errors),
                'time_range_hours': hours,
                'error_types': error_types,
                'affected_endpoints': endpoints,
                'recent_errors': errors[-10:]  # Last 10 errors
            }
            
        except Exception as e:
            logger.error(f"Failed to get error summary: {e}")
            return {'error': str(e)}


# Singleton instance
_error_monitor_instance = None

def get_error_monitor() -> ErrorMonitor:
    """Get or create error monitor instance"""
    global _error_monitor_instance
    if _error_monitor_instance is None:
        _error_monitor_instance = ErrorMonitor()
    return _error_monitor_instance


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    endpoint: Optional[str] = None
) -> None:
    """
    Convenience function to log an error
    
    Args:
        error: Exception object
        context: Additional context
        user_id: User ID if applicable
        endpoint: API endpoint
    """
    monitor = get_error_monitor()
    monitor.log_error(error, context, user_id, endpoint)

