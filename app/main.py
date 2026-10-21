"""
CLI Entry Point for the Self-Evaluating Lesson Content Generator.
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DEFAULT_TOPIC, DEFAULT_MODEL, MAX_RETRIES
from app.generator import LessonGenerator
from app.evaluator import RubricEvaluator
from app.memory import MemoryManager
from app.output import OutputManager
from app.orchestrator import WorkflowOrchestrator
from app.logger import SystemLogger, console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


def list_saved_runs(memory: MemoryManager):
    runs = memory.list_runs()
    if not runs:
        console.print("[yellow]No historical runs found in database.[/yellow]")
        return

    table = Table(title="Historical Lesson Generator Runs", show_header=True, header_style="bold cyan")
    table.add_column("Run ID", style="dim", width=34)
    table.add_column("Topic", style="white")
    table.add_column("Status", justify="center", width=12)
    table.add_column("Versions", justify="center", width=10)
    table.add_column("Retries", justify="center", width=10)
    table.add_column("Created At", style="dim", width=22)

    for r in runs:
        status_color = "green" if r["status"] == "APPROVED" else ("red" if r["status"] == "REJECTED" else "yellow")
        table.add_row(
            r["run_id"],
            r["topic"],
            f"[{status_color}]{r['status']}[/{status_color}]",
            str(r["total_versions"]),
            str(r["retry_count"]),
            r["created_at"]
        )
    console.print(table)


def inspect_run(memory: MemoryManager, run_id: str):
    record = memory.get_run(run_id)
    if not record:
        console.print(f"[bold red]Run '{run_id}' not found.[/bold red]")
        return

    console.print(Panel(
        f"[bold cyan]Run Details:[/bold cyan] {record.run_id}\n"
        f"[bold]Topic:[/bold] {record.topic}\n"
        f"[bold]Status:[/bold] {record.status.value}\n"
        f"[bold]Versions Generated:[/bold] {record.total_versions}\n"
        f"[bold]Retries Used:[/bold] {record.retry_count}\n"
        f"[bold]Created At:[/bold] {record.created_at}",
        title="Run Metadata",
        border_style="cyan"
    ))

    for v in record.versions:
        if v.evaluation:
            SystemLogger.render_evaluation_report(v.evaluation, version=v.version_number)


def inspect_memory(memory: MemoryManager):
    data = memory.load_json_memory()
    patterns = data.get("repeated_failure_patterns", [])
    insights = data.get("run_insights", [])

    console.print(Panel("[bold magenta]Self-Evolving Persistent Memory[/bold magenta]", border_style="magenta"))

    # Patterns Table
    p_table = Table(title="Repeated Failure Patterns & Guidance", show_header=True, header_style="bold yellow")
    p_table.add_column("ID", width=10)
    p_table.add_column("Dimension", width=28)
    p_table.add_column("Issue", width=30)
    p_table.add_column("Corrective Guidance", style="green")

    for p in patterns:
        p_table.add_row(p.get("pattern_id", ""), p.get("dimension", ""), p.get("issue", ""), p.get("guidance", ""))
    console.print(p_table)

    # Insights Table
    if insights:
        i_table = Table(title="Recent Run Insights & Adaptations", show_header=True, header_style="bold blue")
        i_table.add_column("Run ID", width=25)
        i_table.add_column("Insight", width=35)
        i_table.add_column("Applied Correction", style="cyan")

        for ins in insights[-5:]:
            i_table.add_row(ins.get("run_id", ""), ins.get("insight", ""), ins.get("applied_correction", ""))
        console.print(i_table)


def main():
    parser = argparse.ArgumentParser(description="Self-Evaluating Lesson Content Generator CLI")
    parser.add_argument("--topic", type=str, default=DEFAULT_TOPIC, help="Lesson topic to generate")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Model name for generation & evaluation")
    parser.add_argument("--mock", action="store_true", help="Force internal pedagogical engine (deterministic)")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES, help="Maximum regeneration attempts (default: 2)")
    parser.add_argument("--demo-error", type=str, choices=["fact_error", "unexplained_jargon"], help="Inject deliberate error for testing")
    parser.add_argument("--list-runs", action="store_true", help="List all historical runs stored in SQLite")
    parser.add_argument("--inspect-run", type=str, help="Inspect detailed records of a specific run ID")
    parser.add_argument("--inspect-memory", action="store_true", help="Display persistent memory and learned patterns")

    args = parser.parse_args()

    memory = MemoryManager()

    if args.list_runs:
        list_saved_runs(memory)
        return

    if args.inspect_run:
        inspect_run(memory, args.inspect_run)
        return

    if args.inspect_memory:
        inspect_memory(memory)
        return

    # Pipeline execution
    generator = LessonGenerator(model_name=args.model, use_mock=args.mock)
    evaluator = RubricEvaluator(model_name=args.model, use_mock=args.mock)
    output_mgr = OutputManager()

    orchestrator = WorkflowOrchestrator(
        generator=generator,
        evaluator=evaluator,
        memory=memory,
        output_manager=output_mgr,
        max_retries=args.max_retries
    )

    record = orchestrator.run_pipeline(
        topic=args.topic,
        inject_flaw=args.demo_error
    )

    if record.status == "APPROVED":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
