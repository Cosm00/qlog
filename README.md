# 🚀 qlog - Query Logs at Ludicrous Speed

[![PyPI](https://img.shields.io/pypi/v/qlog-cli.svg)](https://pypi.org/project/qlog-cli/) [![Python](https://img.shields.io/pypi/pyversions/qlog-cli.svg)](https://pypi.org/project/qlog-cli/)

**grep is too slow. Elasticsearch is too heavy. qlog is just right.**

```bash
# Index your logs once
qlog index './logs/**/*.log'

# Search millions of lines in milliseconds
qlog search "status=500" --context 3

# Find errors across all services
qlog search "exception" -n 50

# Get stats
qlog stats
```

![qlog demo](demo.gif)

## Why qlog?

| Feature | grep | qlog | Elasticsearch |
|---------|------|------|---------------|
| **Speed** | Slow on large files | ⚡ 10-100x faster | Fast but heavy |
| **Setup** | None | `pip install qlog-cli` | Complex setup |
| **Memory** | Low | Low | High (GB) |
| **Offline** | ✅ | ✅ | ❌ Needs server |
| **Context Lines** | ❌ Clunky | ✅ Built-in | ✅ |
| **Beautiful Output** | ❌ | ✅ | ✅ |
| **Auto-format Detection** | ❌ | ✅ | With config |

## When to Use qlog

✅ **Use qlog when:**
- Developing locally and need to search app logs quickly
- Debugging CI/CD pipelines with large log artifacts  
- Running small projects/side projects where Elasticsearch is overkill
- You want grep-speed search but for repeated queries
- Monitoring local log files with live filtering

❌ **Don't use qlog for:**
- Production observability at scale (use Datadog, Splunk, ELK, etc.)
- Team collaboration on live production logs (use centralized logging)
- Real-time alerting across distributed systems (use an observability platform)

**Think of qlog like ripgrep for logs** - it complements (not replaces) your production logging stack.

## Features

- ⚡ **Blazingly Fast** - Inverted index searches millions of lines/second
- 🎯 **Smart Indexing** - Only re-indexes changed files
- 👁️ **Watch Mode** - Monitor files and auto-reindex with live filtering
- 🎨 **Beautiful Output** - Color-coded, context-aware results
- 📊 **Format Detection** - Auto-detects JSON, syslog, nginx, apache, and more
- 🔍 **Context Aware** - See lines before/after matches
- 💾 **Efficient** - Index stored locally, works offline
- 🐍 **Pure Python** - Easy to install, extend, and understand

## Installation

```bash
pip install qlog-cli
```

Or install from source:

```bash
git clone https://github.com/Cosm00/qlog
cd qlog
pip install -e .
```

## Quick Start

### 1. Index Your Logs

```bash
# Index all logs in current directory
qlog index './**/*.log'

# Index specific patterns
qlog index './app.log' './errors.log' '/var/log/nginx/*.log'

# Force re-indexing
qlog index './**/*.log' --force
```

**Indexing is fast:** 1M+ lines/second on modern hardware.

### 2. Search

```bash
# Simple search
qlog search "error"

# Search with context (3 lines before/after)
qlog search "connection refused" --context 3

# Limit results
qlog search "timeout" -n 50

# JSON output (for piping)
qlog search "critical" --json | jq '.[] | .file'
```

### 3. Watch for Live Changes

```bash
# Monitor logs with auto-reindexing
qlog watch './logs/**/*.log' --filter "error"
```

Perfect for monitoring local services during development.

### 4. Check Statistics

```bash
qlog stats
```

Shows indexed files, unique terms, index size, and performance metrics.

## Examples

### Finding Errors Across Multiple Services

```bash
# Index all service logs
qlog index './logs/**/*.log'

# Find all 500 errors with context
qlog search "500" --context 5
```

### Debugging Production Issues

```bash
# Search for specific request ID
qlog search "request-id-12345" -c 10

# Find all exceptions
qlog search "exception" -n 100
```

### Analyzing Access Logs

```bash
# Index nginx logs
qlog index '/var/log/nginx/*.log'

# Find slow requests
qlog search "upstream_response_time" --context 2
```

### Live Monitoring with Watch Mode

```bash
# Watch logs and auto-reindex on changes
qlog watch './logs/**/*.log'

# Watch with live filtering (only show errors)
qlog watch './logs/**/*.log' --filter "error"

# Watch with custom interval (default: 5s)
qlog watch './app.log' --filter "exception" --interval 2
```

## Performance

Tested on a MacBook Pro (M1) with 10GB of mixed log files:

| Operation | Time | Speed |
|-----------|------|-------|
| **Indexing** | 8.2s | ~1.2M lines/sec |
| **Search (single term)** | 0.003s | ⚡ Instant |
| **Search (multi-term)** | 0.012s | ⚡ Instant |
| **Grep equivalent** | 45s | 💤 Slow |

**qlog is ~3750x faster than grep for indexed searches.**

## How It Works

qlog uses an **inverted index** (like search engines):

1. **Indexing Phase:**
   - Scans log files using memory-mapped I/O (fast!)
   - Tokenizes each line (words, IPs, UUIDs, status codes)
   - Builds an inverted index: `term → [(file, line, offset), ...]`
   - Stores index locally in `.qlog/` (efficient, fast to load)

2. **Search Phase:**
   - Looks up terms in the index (O(1) hash lookup)
   - Finds intersection of matching lines (set operations)
   - Retrieves actual lines from files
   - Formats and displays with context

## Format Auto-Detection

qlog automatically detects and parses common log formats:

- **JSON** - Structured JSON logs
- **Syslog** - Traditional Unix syslog
- **Apache/Nginx** - Combined web server logs
- **ISO Timestamps** - Generic `YYYY-MM-DD HH:MM:SS` logs
- **Plain Text** - Falls back to full-text indexing

## Advanced Usage

### Programmatic API

```python
from qlog import LogIndexer, LogSearcher

# Create indexer
indexer = LogIndexer(index_dir=".qlog")

# Index files
stats = indexer.index_files(["./logs/**/*.log"])
print(f"Indexed {stats['lines']:,} lines in {stats['elapsed']:.2f}s")

# Search
searcher = LogSearcher(indexer)
results = searcher.search("error", context=3, max_results=100)

for result in results:
    print(f"{result['file']}:{result['line_num']}")
    print(f"  {result['line']}")
```

### Custom Tokenization

Extend the indexer to recognize domain-specific patterns:

```python
from qlog import LogIndexer

class CustomIndexer(LogIndexer):
    def _tokenize(self, line):
        tokens = super()._tokenize(line)
        # Add custom patterns
        # e.g., extract trace IDs, custom codes, etc.
        return tokens
```

## Comparison with Other Tools

### vs. grep

- **Pros:** qlog is 10-100x faster on repeated searches
- **Cons:** Requires one-time indexing step

### vs. Elasticsearch

- **Pros:** Much simpler, no server, works offline, lower resource usage
- **Cons:** Single-machine only, no clustering

### vs. Splunk

- **Pros:** Free, open-source, no licensing, simpler
- **Cons:** Fewer features, no distributed search

## Changelog

### 0.2.1
- Faster result retrieval (mmap offset reads; no full-file readlines per match)
- Index hygiene: stable file IDs + purge old postings on reindex
- New command: `qlog watch <patterns> [--filter QUERY]`
- GitHub issue templates

## Roadmap

- [ ] Time-based queries (`qlog search "error" --since "1h ago"`)
- [ ] Cross-service correlation (trace IDs)
- [ ] Export to CSV/JSON with aggregations
- [ ] TUI (interactive terminal UI)
- [ ] Regular expression queries
- [ ] Fuzzy search
- [ ] Web UI for non-CLI users

## Contributing

Contributions welcome! This is a community project.

```bash
# Clone repo
git clone https://github.com/Cosm00/qlog
cd qlog

# Install dev dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Run benchmarks
python benchmarks/bench.py
```

## Support qlog

If qlog saves you time, consider supporting development:

- Ko-fi: https://ko-fi.com/cosm00

(Once GitHub Sponsors is approved, I’ll add it here too.)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built with:
- [rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [click](https://github.com/pallets/click) - CLI framework

Inspired by:
- grep, ag, ripgrep - Fast text search
- Elasticsearch - Inverted index architecture
- lnav - Log file navigation

---

**Made with ❤️ for developers who hate waiting for grep**

⭐ Star this repo if qlog saved you time!
