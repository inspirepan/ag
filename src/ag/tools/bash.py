import subprocess
from typing import Annotated

from ..stdout import print_message
from ..tool import tool


@tool("Run a bash command; please clarify your rationale when running the bash command.")
def bash(command: Annotated[str, "The bash command to run"]) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    result_text = result.stdout.strip()
    return result_text
