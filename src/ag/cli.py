import asyncio
from typing import Optional

import typer

from .agent import get_agent
from .env import env_config
from .stdout import console, print_hello

app = typer.Typer(help="AG - AI Agent CLI Tool")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt: Optional[str] = typer.Option(None, "-p", "--prompt", help="Run in headless mode with the given prompt")
):
    if ctx.invoked_subcommand is None:
        if prompt:
            asyncio.run(headless_mode(prompt))
        else:
            asyncio.run(chat_mode())


async def chat_mode():
    print_hello(env_config)
    agent = get_agent()
    try:
        await agent.chat()
    except KeyboardInterrupt:
        console.print("")
    finally:
        agent.print_cost()
        console.print("\nBye!")


async def headless_mode(prompt: str):
    """Run agent in headless mode with the given prompt"""
    agent = get_agent()
    try:
        result = await agent.run(prompt)
        if result:
            console.print(f"\n[green]Result:[/green] {result}")
    except KeyboardInterrupt:
        console.print("\nInterrupted!")
    finally:
        agent.print_cost()


if __name__ == "__main__":
    app()
