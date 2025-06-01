import openai
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam

from .tool import Tool
from .utils import retry
from .stdout import waiting_dots


class LLM:
    def __init__(self, model_name: str, base_url: str, api_key: str, is_azure: bool):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key
        self.is_azure = is_azure
        if is_azure:
            self.client = openai.AsyncAzureOpenAI(
                azure_endpoint=self.base_url,
                api_version="2024-03-01-preview",
                api_key=self.api_key,
            )
        else:
            self.client = openai.AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )

    @retry(retry_count=5, backoff=1.0)
    async def call(self, msgs: list[ChatCompletionMessageParam], tools: list[Tool] = []) -> ChatCompletionMessage:
        async with waiting_dots("Thinking..."):
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=msgs,
                tools=[tool.schema() for tool in tools],
                extra_headers={"X-TT-LOGID": "fake-logid"} if self.is_azure else None
            )
            return completion.choices[0].message
