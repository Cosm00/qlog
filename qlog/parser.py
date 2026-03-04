"""Auto-detect and parse log formats."""

import re
import json
from typing import Dict, Optional
from datetime import datetime


class LogParser:
    """Auto-detect and parse common log formats."""
    
    FORMATS = {
        "json": r'^\s*\{.*\}\s*$',
        "syslog": r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',
        "apache": r'^\S+\s+\S+\s+\S+\s+\[',
        "nginx": r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s+-\s+-\s+\[',
        "generic": r'^\d{4}-\d{2}-\d{2}',  # ISO timestamp
    }
    
    @staticmethod
    def detect_format(line: str) -> str:
        """Detect log format from a sample line."""
        for fmt, pattern in LogParser.FORMATS.items():
            if re.match(pattern, line):
                return fmt
        return "unknown"
    
    @staticmethod
    def parse(line: str, fmt: Optional[str] = None) -> Dict:
        """Parse log line into structured data."""
        if fmt is None:
            fmt = LogParser.detect_format(line)
        
        if fmt == "json":
            return LogParser._parse_json(line)
        elif fmt == "syslog":
            return LogParser._parse_syslog(line)
        elif fmt in ("apache", "nginx"):
            return LogParser._parse_web(line)
        elif fmt == "generic":
            return LogParser._parse_generic(line)
        else:
            return {"raw": line, "format": "unknown"}
    
    @staticmethod
    def _parse_json(line: str) -> Dict:
        """Parse JSON log line."""
        try:
            data = json.loads(line)
            return {
                "format": "json",
                "timestamp": data.get("timestamp") or data.get("time") or data.get("@timestamp"),
                "level": data.get("level") or data.get("severity"),
                "message": data.get("message") or data.get("msg"),
                "data": data,
            }
        except json.JSONDecodeError:
            return {"raw": line, "format": "json", "error": "invalid_json"}
    
    @staticmethod
    def _parse_syslog(line: str) -> Dict:
        """Parse syslog format."""
        # Example: Jan 15 10:30:45 hostname program[pid]: message
        match = re.match(
            r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(\[\d+\])?:\s+(.+)$',
            line
        )
        if match:
            return {
                "format": "syslog",
                "timestamp": match.group(1),
                "hostname": match.group(2),
                "program": match.group(3),
                "pid": match.group(4)[1:-1] if match.group(4) else None,
                "message": match.group(5),
            }
        return {"raw": line, "format": "syslog"}
    
    @staticmethod
    def _parse_web(line: str) -> Dict:
        """Parse Apache/Nginx combined log format."""
        # Example: 127.0.0.1 - - [01/Jan/2020:12:00:00 +0000] "GET / HTTP/1.1" 200 1234
        match = re.match(
            r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(\S+)\s+(\S+)\s+\S+"\s+(\d+)\s+(\S+)',
            line
        )
        if match:
            return {
                "format": "web",
                "ip": match.group(1),
                "timestamp": match.group(2),
                "method": match.group(3),
                "path": match.group(4),
                "status": int(match.group(5)),
                "size": match.group(6),
            }
        return {"raw": line, "format": "web"}
    
    @staticmethod
    def _parse_generic(line: str) -> Dict:
        """Parse generic ISO timestamp logs."""
        # Example: 2020-01-01 12:00:00 [INFO] message
        match = re.match(
            r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(?:\[(\w+)\])?\s*(.+)$',
            line
        )
        if match:
            return {
                "format": "generic",
                "timestamp": match.group(1),
                "level": match.group(2),
                "message": match.group(3),
            }
        return {"raw": line, "format": "generic"}
