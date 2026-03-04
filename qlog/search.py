"""Fast log search engine."""

import re
from typing import List, Dict, Set, Tuple
from pathlib import Path
from .indexer import LogIndexer


class LogSearcher:
    """Lightning-fast log searcher using inverted index."""
    
    def __init__(self, indexer: LogIndexer):
        self.indexer = indexer
    
    def search(self, query: str, context: int = 0, max_results: int = 1000) -> List[Dict]:
        """Search indexed logs.
        
        Args:
            query: Search query (word or phrase)
            context: Number of context lines before/after
            max_results: Maximum results to return
        
        Returns:
            List of matching log entries with metadata
        """
        # Tokenize query
        query_tokens = self._parse_query(query)
        
        if not query_tokens:
            return []
        
        # Find matching positions using inverted index
        matching_positions = self._find_matches(query_tokens)
        
        if not matching_positions:
            return []
        
        # Limit results
        matching_positions = matching_positions[:max_results]
        
        # Retrieve actual log lines
        results = []
        for file_id, line_num, offset in matching_positions:
            file_meta = self.indexer.files.get(file_id)
            if not file_meta:
                continue
            
            # Read the line (and context if requested)
            lines = self._read_lines(
                file_meta["path"],
                line_num,
                context
            )
            
            if lines:
                results.append({
                    "file": file_meta["path"],
                    "line_num": line_num,
                    "line": lines.get("match", ""),
                    "before": lines.get("before", []),
                    "after": lines.get("after", []),
                    "query": query,
                })
        
        return results
    
    def _parse_query(self, query: str) -> List[str]:
        """Parse search query into tokens."""
        # Simple for now - split on whitespace, lowercase
        tokens = query.lower().split()
        return tokens
    
    def _find_matches(self, query_tokens: List[str]) -> List[Tuple[int, int, int]]:
        """Find positions matching all query tokens."""
        if not query_tokens:
            return []
        
        # Get positions for first token
        positions_sets = []
        
        for token in query_tokens:
            positions = self.indexer.index.get(token, [])
            if not positions:
                # No matches for this token = no overall matches
                return []
            
            # Convert to set of (file_id, line_num) for intersection
            pos_set = set((file_id, line_num) for file_id, line_num, offset in positions)
            positions_sets.append((token, pos_set, positions))
        
        # Find intersection (lines containing ALL tokens)
        if len(positions_sets) == 1:
            # Single token - return all positions
            _, _, positions = positions_sets[0]
            return sorted(positions, key=lambda x: (x[0], x[1]))
        
        # Multiple tokens - find intersection
        common_positions = positions_sets[0][1]
        for _, pos_set, _ in positions_sets[1:]:
            common_positions &= pos_set
        
        # Convert back to full position tuples
        result = []
        for file_id, line_num in common_positions:
            # Get offset from first token's positions
            for fid, lnum, offset in positions_sets[0][2]:
                if fid == file_id and lnum == line_num:
                    result.append((file_id, line_num, offset))
                    break
        
        return sorted(result, key=lambda x: (x[0], x[1]))
    
    def _read_lines(self, filepath: str, target_line: int, context: int = 0) -> Dict:
        """Read specific line with context from file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                if target_line >= len(lines):
                    return {}
                
                start = max(0, target_line - context)
                end = min(len(lines), target_line + context + 1)
                
                return {
                    "before": [line.rstrip() for line in lines[start:target_line]],
                    "match": lines[target_line].rstrip(),
                    "after": [line.rstrip() for line in lines[target_line + 1:end]],
                }
        except Exception as e:
            return {}
    
    def stats(self) -> Dict:
        """Get search engine stats."""
        return self.indexer.get_stats()
