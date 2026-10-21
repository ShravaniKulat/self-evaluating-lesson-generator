import sys
import logging
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from app.models import EvaluationReport, PassFailResult, RunDecision

# Reconfigure stdout and stderr for UTF-8 compatibility on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(force_terminal=True)

# Configure standard python logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
app_logger = logging.getLogger("SelfEvaluatingLessonGenerator")


class SystemLogger:
    @staticmethod
    def banner(title: str, subtitle: Optional[str] = None):
        text = Text(title, style="bold cyan")
        if subtitle:
            text.append(f"\n{subtitle}", style="dim white")
        console.print(Panel(text, border_style="cyan", padding=(1, 2)))

    @staticmethod
    def step(step_num: int, title: str, description: str):
        console.print(f"\n[bold yellow]--- Step {step_num}: {title} ---[/bold yellow]")
        console.print(f"[dim]{description}[/dim]")

    @staticmethod
    def info(msg: str):
        console.print(f"[blue][INFO][/blue] {msg}")

    @staticmethod
    def success(msg: str):
        console.print(f"[bold green][PASS][/bold green] {msg}")

    @staticmethod
    def warning(msg: str):
        console.print(f"[bold yellow][WARN][/bold yellow] {msg}")

    @staticmethod
    def error(msg: str):
        console.print(f"[bold red][FAIL][/bold red] {msg}")

    @staticmethod
    def render_evaluation_report(report: EvaluationReport, version: int):
        status_color = "green" if report.is_approved() else "red"
        status_text = "PASS (Approved)" if report.is_approved() else "FAIL (Revision Required)"

        table = Table(
            title=f"Evaluation Report — Version {version} [{status_color}]{status_text}[/{status_color}]",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("ID", style="dim", width=12)
        table.add_column("Dimension", style="cyan", width=26)
        table.add_column("Result", justify="center", width=8)
        table.add_column("Evidence & Reason", style="white")

        for cp in report.checkpoints:
            res_text = (
                "[bold green]PASS[/bold green]"
                if cp.result == PassFailResult.PASS
                else "[bold red]FAIL[/bold red]"
            )
            evidence_desc = cp.evidence
            if cp.failure_reason:
                evidence_desc += f"\n[bold red]Failure Reason:[/bold red] {cp.failure_reason}"
            table.add_row(cp.checkpoint_id, cp.dimension, res_text, evidence_desc)

        console.print(table)
        console.print(
            f"[bold {status_color}]Result: {report.passed_checkpoints}/{report.total_checkpoints} checkpoints passed.[/bold {status_color}]\n"
        )

    @staticmethod
    def render_decision(decision: RunDecision, retry_count: int, run_id: str):
        if decision == RunDecision.APPROVED:
            panel = Panel(
                Text(
                    f"DECISION: APPROVED\nRun ID: {run_id}\nAll mandatory checkpoints satisfied. Lesson approved for shipping!\nTotal Retries: {retry_count}",
                    justify="center",
                    style="bold green"
                ),
                border_style="green",
                padding=(1, 2)
            )
        elif decision == RunDecision.REJECTED:
            panel = Panel(
                Text(
                    f"DECISION: REJECTED\nRun ID: {run_id}\nMaximum retry limit reached without passing all mandatory checkpoints.\nTotal Retries: {retry_count}",
                    justify="center",
                    style="bold red"
                ),
                border_style="red",
                padding=(1, 2)
            )
        else:
            panel = Panel(
                Text(
                    f"DECISION: ERROR\nRun ID: {run_id}\nAn operational error occurred during execution.",
                    justify="center",
                    style="bold yellow"
                ),
                border_style="yellow",
                padding=(1, 2)
            )
        console.print(panel)
