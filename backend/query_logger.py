"""
Query Logger
Logs all user queries and responses to date-based log files.
Each day gets its own log file: YYYY-MM-DD.log
Located in: backend/logs/
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class QueryLogger:
    """Log queries and responses to date-based files"""
    
    def __init__(self, logs_dir: str = "logs"):
        """Initialize logger with logs directory"""
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
    
    def log_query(self, user_query: str, response: Dict[str, Any], 
                  operation: str = "", records_count: int = 0, 
                  additional_data: Optional[Dict] = None) -> None:
        """
        Log a query and its response to today's log file
        
        Args:
            user_query: The user's input query
            response: The response from the pipeline
            operation: The detected operation type (COUNT, METRICS, etc.)
            records_count: Number of records returned
            additional_data: Optional extra data to log
        """
        
        now = datetime.now()
        log_date = now.strftime("%Y-%m-%d")
        log_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create log entry
        log_entry = {
            "timestamp": log_timestamp,
            "query": user_query,
            "operation": operation,
            "records_count": records_count,
            "response": response if isinstance(response, str) else str(response),
        }
        
        # Add any additional data
        if additional_data:
            log_entry["additional_data"] = additional_data
        
        # Get today's log file path
        log_file = self.logs_dir / f"{log_date}.log"
        
        # Append to log file
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to write to log file {log_file}: {str(e)}")
    
    def get_today_logs(self) -> list:
        """Get all logs for today"""
        now = datetime.now()
        log_date = now.strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{log_date}.log"
        
        if not log_file.exists():
            return []
        
        logs = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            print(f"[ERROR] Failed to read log file {log_file}: {str(e)}")
        
        return logs
    
    def get_logs_by_date(self, date_str: str) -> list:
        """Get all logs for a specific date (format: YYYY-MM-DD)"""
        log_file = self.logs_dir / f"{date_str}.log"
        
        if not log_file.exists():
            return []
        
        logs = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            print(f"[ERROR] Failed to read log file {log_file}: {str(e)}")
        
        return logs
    
    def get_all_logs(self) -> Dict[str, list]:
        """Get all logs organized by date"""
        all_logs = {}
        
        try:
            for log_file in self.logs_dir.glob("*.log"):
                date = log_file.stem  # Get filename without extension
                logs = []
                with open(log_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            logs.append(json.loads(line))
                if logs:
                    all_logs[date] = logs
        except Exception as e:
            print(f"[ERROR] Failed to read logs directory: {str(e)}")
        
        return all_logs


if __name__ == "__main__":
    print("[OK] Query Logger Module Loaded")
    logger = QueryLogger()
    print(f"Log directory: {logger.logs_dir.absolute()}")
