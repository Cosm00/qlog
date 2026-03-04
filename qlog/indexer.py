"""Fast log indexer with inverted index."""

import mmap
import os
import re
import pickle
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime


class LogIndexer:
    """Lightning-fast log indexer using inverted index."""
    
    def __init__(self, index_dir: str = ".qlog"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        
        # Inverted index: word -> [(file_id, line_num, offset), ...]
        self.index: Dict[str, List[Tuple[int, int, int]]] = defaultdict(list)
        
        # File metadata
        self.files: Dict[int, Dict] = {}
        self.file_id_counter = 0
        
        # Load existing index if available
        self._load_index()
    
    def index_files(self, patterns: List[str], force: bool = False) -> Dict:
        """Index log files matching patterns."""
        from glob import glob
        
        files_indexed = 0
        lines_indexed = 0
        start_time = datetime.now()
        
        for pattern in patterns:
            for filepath in glob(pattern, recursive=True):
                if not os.path.isfile(filepath):
                    continue
                
                # Check if file needs reindexing
                file_hash = self._file_hash(filepath)
                if not force and self._is_indexed(filepath, file_hash):
                    continue
                
                # Index the file
                lines = self._index_file(filepath, file_hash)
                files_indexed += 1
                lines_indexed += lines
        
        # Save index
        self._save_index()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        return {
            "files": files_indexed,
            "lines": lines_indexed,
            "elapsed": elapsed,
            "lines_per_sec": int(lines_indexed / elapsed) if elapsed > 0 else 0,
        }
    
    def _index_file(self, filepath: str, file_hash: str) -> int:
        """Index a single file using mmap for speed."""
        file_id = self.file_id_counter
        self.file_id_counter += 1
        
        self.files[file_id] = {
            "path": filepath,
            "hash": file_hash,
            "size": os.path.getsize(filepath),
            "indexed_at": datetime.now().isoformat(),
        }
        
        lines_indexed = 0
        
        try:
            with open(filepath, "r+b") as f:
                # Use mmap for fast reading
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped:
                    line_num = 0
                    offset = 0
                    
                    while True:
                        line_start = offset
                        # Find next newline
                        newline_pos = mmapped.find(b'\n', offset)
                        
                        if newline_pos == -1:
                            # Last line
                            line_bytes = mmapped[offset:]
                            if not line_bytes:
                                break
                            offset = len(mmapped)
                        else:
                            line_bytes = mmapped[offset:newline_pos]
                            offset = newline_pos + 1
                        
                        try:
                            line = line_bytes.decode('utf-8', errors='ignore')
                        except:
                            continue
                        
                        # Tokenize and index
                        tokens = self._tokenize(line)
                        for token in tokens:
                            self.index[token].append((file_id, line_num, line_start))
                        
                        line_num += 1
                        lines_indexed += 1
                        
                        if newline_pos == -1:
                            break
        
        except Exception as e:
            print(f"Error indexing {filepath}: {e}")
        
        return lines_indexed
    
    def _tokenize(self, line: str) -> Set[str]:
        """Tokenize log line into searchable terms."""
        # Split on non-alphanumeric, keep words 2+ chars
        tokens = set()
        
        # Extract words
        words = re.findall(r'\b\w{2,}\b', line.lower())
        tokens.update(words)
        
        # Extract common patterns
        # IPs
        ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', line)
        tokens.update(ips)
        
        # UUIDs/IDs
        ids = re.findall(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', line.lower())
        tokens.update(ids)
        
        # HTTP status codes
        status = re.findall(r'\b[45]\d{2}\b', line)
        tokens.update(status)
        
        return tokens
    
    def _file_hash(self, filepath: str) -> str:
        """Quick file hash for change detection."""
        stat = os.stat(filepath)
        # Hash based on size + mtime (fast, good enough)
        return hashlib.md5(
            f"{stat.st_size}:{stat.st_mtime}".encode()
        ).hexdigest()
    
    def _is_indexed(self, filepath: str, file_hash: str) -> bool:
        """Check if file is already indexed."""
        for file_id, meta in self.files.items():
            if meta["path"] == filepath and meta["hash"] == file_hash:
                return True
        return False
    
    def _save_index(self):
        """Save index to disk."""
        index_file = self.index_dir / "index.pkl"
        with open(index_file, "wb") as f:
            pickle.dump({
                "index": dict(self.index),
                "files": self.files,
                "file_id_counter": self.file_id_counter,
            }, f)
    
    def _load_index(self):
        """Load index from disk."""
        index_file = self.index_dir / "index.pkl"
        if index_file.exists():
            try:
                with open(index_file, "rb") as f:
                    data = pickle.load(f)
                    self.index = defaultdict(list, data["index"])
                    self.files = data["files"]
                    self.file_id_counter = data.get("file_id_counter", 0)
            except Exception as e:
                print(f"Warning: Could not load index: {e}")
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        total_lines = sum(len(positions) for positions in self.index.values())
        return {
            "files": len(self.files),
            "unique_terms": len(self.index),
            "total_positions": total_lines,
            "index_size_mb": os.path.getsize(self.index_dir / "index.pkl") / 1024 / 1024
                if (self.index_dir / "index.pkl").exists() else 0,
        }
