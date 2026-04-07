from langchain_core.messages import HumanMessage

from typing import AsyncIterator
import os


class LLMProvider:
    """
    Provides a unified interface to access different LLM APIs.

    This class handles the initialization of various Language Model providers
    (Anthropic, OpenAI, Ollama) using environment variables for configuration.

    Attributes:
        provider (str): The name of the AI provider to use.

    Configuration:
        The following environment variables are supported:

        Ollama:
            - OLLAMA_BASE_URL: Ollama server URL (default: http://host.docker.internal:11434).
            - OLLAMA_MODEL: Model to use (default: llama3.2).

        Anthropic:
            - ANTHROPIC_API_KEY: Your Anthropic API key.
            - ANTHROPIC_MODEL: Model to use (default: claude-haiku-4-5-20251001).

        OpenAI:
            - OPENAI_API_KEY: Your OpenAI API key.
            - OPENAI_MODEL: Model to use (default: gpt-4o-mini).
    """

    def __init__(self, provider: str):

        self.llm = None

        try:
            if provider == "ollama":
                from langchain_ollama import ChatOllama
                self.llm = ChatOllama(
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/"),
                    model=os.getenv("OLLAMA_MODEL", "llama3.2"),
                )

            if provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    model_name=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
                )

            if provider == "openai":
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                )

        except Exception:
            pass


    async def stream(self, prompt: str) -> AsyncIterator[str]:
        async for chunk in self.llm.astream([HumanMessage(content=prompt)]):
            if chunk.content:
                yield chunk.content
