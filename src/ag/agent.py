from typing import Annotated

from openai.types.chat import ChatCompletionMessageParam
from prompt_toolkit import PromptSession

from .env import env_config
from .llm import LLM
from .stdout import console, print_message
from .tool import Tool, tool
from .tools import bash
from .prompt import SYSTEM_PROMPT


class Agent:
    def __init__(self, system_prompt: str, llm: LLM, tools: list[Tool] = []):
        self.model_call_count = 0
        self.tool_call_count = 0

        self.llm = llm
        self.tool_dict = {tool.name: tool for tool in tools}
        self.system_prompt = system_prompt
        self.session_messages: list[ChatCompletionMessageParam] = [{"role": "system", "content": self.system_prompt}]

    async def chat(self):
        """Chat Loop"""
        while True:
            user_input = await PromptSession().prompt_async("> ")
            if user_input == "exit":
                break
            if user_input == "":
                continue
            print("")
            await self.run(user_input)

    async def run(self, input: str, max_steps: int = 20):
        """ReAct Loop"""
        if not input:
            return
        self.session_messages.append({"role": "user", "content": input})
        for _ in range(max_steps):
            response = await self.llm.call(self.session_messages, list(self.tool_dict.values()))
            self.model_call_count += 1
            self.session_messages.append(response)
            if response.content:
                print_message(response.content)
            if not response.tool_calls:
                return response.content
            for tool_call in response.tool_calls:
                if tool_call.function.name not in self.tool_dict:
                    print_message(f"[red]Tool [bold]{tool_call.function.name}[/bold] not found[/red]", mark_style="red")
                    continue
                tool_match = self.tool_dict[tool_call.function.name]
                tool_result = await tool_match(tool_call.function.arguments)
                self.tool_call_count += 1
                self.session_messages.append({"role": "tool", "content": tool_result, "tool_call_id": tool_call.id})
        return f"Max steps {max_steps} reached"

    def print_cost(self):
        console.print(f"[gray]Total model calls: {self.model_call_count}[/gray]")
        console.print(f"[gray]Total tool calls: {self.tool_call_count}[/gray]")


@tool("Run a new agent to solve a task")
async def agent(task: str) -> str:
    llm = LLM(env_config.model_name, env_config.base_url, env_config.api_key, env_config.model_is_azure)
    sub_agent = Agent(system_prompt=SYSTEM_PROMPT, llm=llm, tools=[bash])
    result = await sub_agent.run(task)
    return result


def get_agent():
    llm = LLM(env_config.model_name, env_config.base_url, env_config.api_key, env_config.model_is_azure)
    return Agent(system_prompt=SYSTEM_PROMPT, llm=llm, tools=[agent, bash])
