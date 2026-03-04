"""Command-line interface for qlog."""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .indexer import LogIndexer
from .search import LogSearcher
from .parser import LogParser


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """qlog - Lightning-fast local log search and analysis.
    
    \b
    Examples:
      qlog index './logs/**/*.log'
      qlog search "error" --context 3
      qlog search "status=500" --json
      qlog stats
    """
    pass


@main.command()
@click.argument("patterns", nargs=-1, required=True)
@click.option("--force", is_flag=True, help="Re-index even if files haven't changed")
def index(patterns, force):
    """Index log files for fast searching."""
    console.print("[bold blue]🚀 Indexing logs...[/bold blue]")
    
    indexer = LogIndexer()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Indexing...", total=None)
        
        stats = indexer.index_files(list(patterns), force=force)
        
        progress.remove_task(task)
    
    # Display results
    table = Table(title="Indexing Complete", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Files indexed", str(stats["files"]))
    table.add_row("Lines indexed", f"{stats['lines']:,}")
    table.add_row("Time elapsed", f"{stats['elapsed']:.2f}s")
    table.add_row("Speed", f"{stats['lines_per_sec']:,} lines/sec")
    
    console.print(table)


@main.command()
@click.argument("query")
@click.option("--context", "-c", default=0, help="Lines of context before/after match")
@click.option("--max-results", "-n", default=100, help="Maximum results to show")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def search(query, context, max_results, output_json):
    """Search indexed logs."""
    indexer = LogIndexer()
    searcher = LogSearcher(indexer)
    
    if not indexer.files:
        console.print("[bold red]❌ No indexed files found. Run 'qlog index' first.[/bold red]")
        return
    
    results = searcher.search(query, context=context, max_results=max_results)
    
    if not results:
        console.print(f"[yellow]No results found for:[/yellow] {query}")
        return
    
    if output_json:
        import json
        print(json.dumps(results, indent=2))
        return
    
    # Beautiful terminal output
    console.print(f"\n[bold green]✨ Found {len(results)} results[/bold green]")
    console.print()
    
    for i, result in enumerate(results, 1):
        # Create panel for each result
        content = []
        
        # Context before
        if result.get("before"):
            for line in result["before"]:
                content.append(f"[dim]{line}[/dim]")
        
        # Matched line (highlighted)
        matched_line = result["line"]
        # Highlight query terms
        for term in query.split():
            matched_line = matched_line.replace(
                term,
                f"[bold yellow on red]{term}[/bold yellow on red]"
            )
            matched_line = matched_line.replace(
                term.upper(),
                f"[bold yellow on red]{term.upper()}[/bold yellow on red]"
            )
        content.append(f"[bold white]{matched_line}[/bold white]")
        
        # Context after
        if result.get("after"):
            for line in result["after"]:
                content.append(f"[dim]{line}[/dim]")
        
        panel_content = "\n".join(content)
        
        console.print(
            Panel(
                panel_content,
                title=f"[cyan]{result['file']}[/cyan]:[green]{result['line_num']}[/green]",
                border_style="blue",
                expand=False,
            )
        )
        
        if i < len(results):
            console.print()


@main.command()
def stats():
    """Show index statistics."""
    indexer = LogIndexer()
    stats = indexer.get_stats()
    
    if stats["files"] == 0:
        console.print("[yellow]No index found. Run 'qlog index' first.[/yellow]")
        return
    
    table = Table(title="Index Statistics", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Indexed files", str(stats["files"]))
    table.add_row("Unique terms", f"{stats['unique_terms']:,}")
    table.add_row("Total positions", f"{stats['total_positions']:,}")
    table.add_row("Index size", f"{stats['index_size_mb']:.2f} MB")
    
    console.print(table)
    
    # Show file list
    if indexer.files:
        console.print("\n[bold]Indexed Files:[/bold]")
        for file_id, meta in list(indexer.files.items())[:10]:
            console.print(f"  [cyan]•[/cyan] {meta['path']}")
        
        if len(indexer.files) > 10:
            console.print(f"  [dim]... and {len(indexer.files) - 10} more[/dim]")


@main.command()
def clear():
    """Clear the index."""
    import shutil
    
    index_dir = Path(".qlog")
    if index_dir.exists():
        shutil.rmtree(index_dir)
        console.print("[green]✓ Index cleared[/green]")
    else:
        console.print("[yellow]No index to clear[/yellow]")


if __name__ == "__main__":
    main()
