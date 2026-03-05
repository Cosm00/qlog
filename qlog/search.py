"""Fast log search engine."""

from __future__ import annotations

import mmap
from typing import List, Dict, Tuple

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
        query_tokens = self._parse_query(query)
        if not query_tokens:
            return []

        matching_positions = self._find_matches(query_tokens)
        if not matching_positions:
            return []

        matching_positions = matching_positions[:max_results]

        results: List[Dict] = []
        for file_id, line_num, offset in matching_positions:
            file_meta = self.indexer.files.get(file_id)
            if not file_meta:
                continue

            lines = self._read_lines_mmap(
                file_meta["path"],
                offset=offset,
                context=context,
            )

            if lines:
                results.append(
                    {
                        "file": file_meta["path"],
                        "line_num": line_num,
                        "line": lines.get("match", ""),
                        "before": lines.get("before", []),
                        "after": lines.get("after", []),
                        "query": query,
                    }
                )

        return results

    def _parse_query(self, query: str) -> List[str]:
        # Simple for now - split on whitespace, lowercase
        return [t for t in query.lower().split() if t]

    def _find_matches(self, query_tokens: List[str]) -> List[Tuple[int, int, int]]:
        if not query_tokens:
            return []

        positions_sets = []
        for token in query_tokens:
            positions = self.indexer.index.get(token, [])
            if not positions:
                return []

            pos_set = {(file_id, line_num) for file_id, line_num, _ in positions}
            positions_sets.append((token, pos_set, positions))

        if len(positions_sets) == 1:
            _, _, positions = positions_sets[0]
            return sorted(positions, key=lambda x: (x[0], x[1]))

        common_positions = positions_sets[0][1]
        for _, pos_set, _ in positions_sets[1:]:
            common_positions &= pos_set

        # Convert back to full tuples using the offset from the first token
        first_positions = positions_sets[0][2]
        offsets = {(fid, lnum): off for fid, lnum, off in first_positions}
        result = [(fid, lnum, offsets[(fid, lnum)]) for (fid, lnum) in common_positions if (fid, lnum) in offsets]
        return sorted(result, key=lambda x: (x[0], x[1]))

    def _read_lines_mmap(self, filepath: str, offset: int, context: int = 0) -> Dict:
        """Read a line (and context) from a file using mmap + byte offsets.

        This avoids `readlines()` and scales much better for large files.
        """
        try:
            with open(filepath, "rb") as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    before, match, after = self._slice_with_context(mm, offset=offset, context=context)
                    return {
                        "before": before,
                        "match": match,
                        "after": after,
                    }
        except Exception:
            return {}

    @staticmethod
    def _slice_with_context(mm: mmap.mmap, offset: int, context: int) -> Tuple[List[str], str, List[str]]:
        # Match line
        line_start = max(0, offset)
        line_end = mm.find(b"\n", line_start)
        if line_end == -1:
            line_end = len(mm)
        match_bytes = mm[line_start:line_end]
        match = match_bytes.decode("utf-8", errors="ignore").rstrip("\r")

        before: List[str] = []
        after: List[str] = []

        # Before context (walk backwards)
        cur_start = line_start
        for _ in range(context):
            if cur_start <= 0:
                break
            prev_nl = mm.rfind(b"\n", 0, cur_start - 1)
            prev_start = 0 if prev_nl == -1 else prev_nl + 1
            prev_end = cur_start - 1 if mm[cur_start - 1 : cur_start] == b"\n" else cur_start
            b = mm[prev_start:prev_end]
            before.append(b.decode("utf-8", errors="ignore").rstrip("\r"))
            cur_start = prev_start
        before.reverse()

        # After context (walk forwards)
        cur_end = line_end
        for _ in range(context):
            if cur_end >= len(mm):
                break
            # skip the newline
            nxt_start = cur_end + 1 if cur_end < len(mm) and mm[cur_end : cur_end + 1] == b"\n" else cur_end
            nxt_end = mm.find(b"\n", nxt_start)
            if nxt_end == -1:
                nxt_end = len(mm)
            b = mm[nxt_start:nxt_end]
            after.append(b.decode("utf-8", errors="ignore").rstrip("\r"))
            cur_end = nxt_end

        return before, match, after

    def stats(self) -> Dict:
        return self.indexer.get_stats()
