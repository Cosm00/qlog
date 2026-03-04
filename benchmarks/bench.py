"""Benchmark qlog vs grep."""

import time
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qlog import LogIndexer, LogSearcher


def generate_test_logs(filename, num_lines=100000):
    """Generate test log file."""
    import random
    
    levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    messages = [
        "Request processed successfully",
        "Connection timeout to database",
        "User authentication failed",
        "Cache miss for key",
        "Exception in handler",
        "Request completed in 123ms",
    ]
    
    with open(filename, "w") as f:
        for i in range(num_lines):
            level = random.choice(levels)
            message = random.choice(messages)
            f.write(f"2024-01-{i%28+1:02d} 12:00:{i%60:02d} [{level}] {message} (request-id-{i})\n")
    
    print(f"✓ Generated {num_lines:,} lines in {filename}")


def bench_indexing(log_file):
    """Benchmark indexing speed."""
    print("\n🚀 Benchmarking Indexing...")
    
    indexer = LogIndexer(index_dir=".qlog_bench")
    
    start = time.time()
    stats = indexer.index_files([log_file], force=True)
    elapsed = time.time() - start
    
    print(f"  Lines: {stats['lines']:,}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Speed: {stats['lines_per_sec']:,} lines/sec")
    
    return indexer


def bench_search_qlog(indexer, query):
    """Benchmark qlog search."""
    print(f"\n⚡ Benchmarking qlog search: '{query}'...")
    
    searcher = LogSearcher(indexer)
    
    # Warmup
    searcher.search(query, max_results=10)
    
    # Actual benchmark
    times = []
    for _ in range(10):
        start = time.time()
        results = searcher.search(query, max_results=1000)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    
    print(f"  Results: {len(results)}")
    print(f"  Avg time: {avg_time*1000:.2f}ms")
    print(f"  Min time: {min(times)*1000:.2f}ms")


def bench_grep(log_file, query):
    """Benchmark grep."""
    print(f"\n🐌 Benchmarking grep: '{query}'...")
    
    times = []
    for _ in range(3):  # Fewer iterations (grep is slow)
        start = time.time()
        result = subprocess.run(
            ["grep", "-i", query, log_file],
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    
    print(f"  Avg time: {avg_time*1000:.2f}ms")
    print(f"  Speedup: {avg_time / (sum(times)/len(times)):.1f}x")


def main():
    """Run benchmarks."""
    print("=" * 60)
    print("qlog Benchmark Suite")
    print("=" * 60)
    
    # Generate test data
    log_file = "test_bench.log"
    num_lines = 500000
    
    if not Path(log_file).exists():
        generate_test_logs(log_file, num_lines)
    
    # Benchmark indexing
    indexer = bench_indexing(log_file)
    
    # Benchmark searches
    queries = ["ERROR", "timeout", "request-id"]
    
    for query in queries:
        bench_search_qlog(indexer, query)
        bench_grep(log_file, query)
    
    print("\n" + "=" * 60)
    print("✨ Benchmark Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
