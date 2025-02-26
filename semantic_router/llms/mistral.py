import os
from typing import List, Optional

from mistralai.client import MistralClient

from semantic_router.llms import BaseLLM
from semantic_router.schema import Message
from semantic_router.utils.logger import logger


class MistralAILLM(BaseLLM):
    client: Optional[MistralClient]
    temperature: Optional[float]
    max_tokens: Optional[int]

    def __init__(
        self,
        name: Optional[str] = None,
        mistralai_api_key: Optional[str] = None,
        temperature: float = 0.01,
        max_tokens: int = 200,
    ):
        if name is None:
            name = os.getenv("MISTRALAI_CHAT_MODEL_NAME", "mistral-tiny")
        super().__init__(name=name)
        api_key = mistralai_api_key or os.getenv("MISTRALAI_API_KEY")
        if api_key is None:
            raise ValueError("MistralAI API key cannot be 'None'.")
        try:
            self.client = MistralClient(api_key=api_key)
        except Exception as e:
            raise ValueError(
                f"MistralAI API client failed to initialize. Error: {e}"
            ) from e
        self.temperature = temperature
        self.max_tokens = max_tokens

    def __call__(self, messages: List[Message]) -> str:
        if self.client is None:
            raise ValueError("MistralAI client is not initialized.")
        try:
            completion = self.client.chat(
                model=self.name,
                messages=[m.to_mistral() for m in messages],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            output = completion.choices[0].message.content

            if not output:
                raise Exception("No output generated")
            return output
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise Exception(f"LLM error: {e}") from e
