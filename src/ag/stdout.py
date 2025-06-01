import asyncio
from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator

from rich.console import Console, Group
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.spinner import Spinner

light_theme = Theme({
    "orange": "rgb(201,125,92)",
    "blue": "rgb(62,99,153)",
    "gray": "rgb(137,136,131)",
    "red": "rgb(158,57,66)",
    "black": "rgb(0,0,0)",
    "green": "rgb(65,120,64)"
})


def get_console():
    is_dark_mode = False
    theme = light_theme if is_dark_mode else light_theme
    return Console(theme=theme)


class IndentedConsole:
    def __init__(self):
        self.console = get_console()
        self.indent = 0

    def print(self, *args, **kwargs):
        self.console.print(*[Padding.indent(arg, self.indent) for arg in args], **kwargs)

    def incr_indent(self, n=2):
        self.indent += n

    def decr_indent(self, n=2):
        self.indent -= n


console = IndentedConsole()


def print_hello(env_config):
    console.print(Panel(Group(
        "[orange]✻[/orange] Welcome to [bold]Agent CLI[/bold]!",
        "",
        f"  [gray]model: {env_config.model_name}[/gray]",
        f"  [gray]cwd: {os.getcwd()}[/gray]",
    ), border_style="orange", expand=False))


def print_message(content: str, mark="⏺", mark_style="black", end_new_line=True):
    table = Table.grid(padding=(0, 1))
    table.add_column(width=0, no_wrap=True)
    table.add_column(overflow="fold")
    if isinstance(mark, str):
        mark = Text(mark, style=mark_style)
    table.add_row(mark, content)
    console.print(table)
    if end_new_line:
        print("")


@asynccontextmanager
async def waiting_dots(text: str = " Waiting...", style: str | None = None) -> AsyncGenerator[None, None]:
    async def _run_animation(status_text: Text) -> None:
        spinner = Spinner("bouncingBall", text=status_text)
        with Live(spinner, refresh_per_second=10, transient=True, vertical_overflow="visible") as live:
            try:
                while True:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                pass
            finally:
                await asyncio.sleep(0.02)

    status_text = Text(text, style=style)
    animation_task = asyncio.create_task(_run_animation(status_text))

    try:
        yield
    finally:
        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass
