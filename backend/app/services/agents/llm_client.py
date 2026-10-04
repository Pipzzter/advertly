"""
OpenAI LLM Client
=================

Client for OpenAI's Responses API using the official openai SDK.
Model and reasoning effort come from OPENAI_TEXT_MODEL / OPENAI_REASONING_EFFORT.
"""

import logging
from functools import cached_property
from typing import Any, Optional, Type, TypeVar

from openai import AsyncOpenAI
from openai.types.responses import Response
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OpenAIResponse(BaseModel):
    """Response from the OpenAI API."""

    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None


class OpenAIClient:
    """
    Client for the OpenAI Responses API using the official openai SDK.

    Supports:
    - Configurable model (default gpt-6-luna) and reasoning effort
    - Structured output via Pydantic models (strict JSON schema)
    - Retry logic with exponential backoff for rate limits and transient errors

    Usage:
        client = OpenAIClient()
        response = await client.generate("Your prompt here")
        structured = await client.generate_structured("Your prompt", MySchema)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.openai_text_model
        self.reasoning_effort = settings.openai_reasoning_effort
        self._api_key = api_key or settings.openai_api_key
        self._max_retries = max_retries

    @cached_property
    def client(self) -> AsyncOpenAI:
        # Created on first use so a missing API key surfaces as a request error
        return AsyncOpenAI(api_key=self._api_key, max_retries=self._max_retries)

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
    ) -> OpenAIResponse:
        """
        Generate text using the OpenAI API.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum output tokens, reasoning included (default: model limit)

        Returns:
            OpenAIResponse with generated text and token usage
        """
        logger.debug("Sending request to OpenAI API: model=%s", self.model)

        response = await self.client.responses.create(
            input=prompt,
            **self._request_options(max_tokens),
        )
        return OpenAIResponse(text=response.output_text, **self._log_usage(response))

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        max_tokens: Optional[int] = None,
    ) -> T:
        """
        Generate structured output parsed directly into a Pydantic model.

        Args:
            prompt: The prompt to send to the model
            schema: Pydantic model class to parse the response into
            max_tokens: Maximum output tokens, reasoning included (default: model limit)

        Returns:
            Instance of the provided Pydantic schema
        """
        logger.debug(
            "Sending structured request to OpenAI API: model=%s, schema=%s",
            self.model,
            schema.__name__,
        )

        response = await self.client.responses.parse(
            input=prompt,
            text_format=schema,
            **self._request_options(max_tokens),
        )
        self._log_usage(response)

        parsed = response.output_parsed
        if parsed is None:
            refusal = next(
                (
                    content.refusal
                    for item in response.output
                    if item.type == "message"
                    for content in item.content
                    if content.type == "refusal"
                ),
                None,
            )
            raise ValueError(
                refusal
                or f"OpenAI returned no structured output for schema {schema.__name__} "
                f"(status={response.status})"
            )

        logger.debug(
            "Parsed structured response for schema=%s, preview=%s",
            schema.__name__,
            response.output_text[:200],
        )

        return parsed

    def _request_options(self, max_tokens: Optional[int]) -> dict[str, Any]:
        """Build the request options shared by all calls."""
        options: dict[str, Any] = {"model": self.model, "store": False}
        # Only sent when configured, since non-reasoning models reject the parameter
        if self.reasoning_effort:
            options["reasoning"] = {"effort": self.reasoning_effort}
        if max_tokens:
            options["max_output_tokens"] = max_tokens
        return options

    @staticmethod
    def _log_usage(response: Response) -> dict[str, Optional[int]]:
        """Log token usage and return it in OpenAIResponse field names."""
        usage = response.usage
        tokens = {
            "prompt_tokens": getattr(usage, "input_tokens", None),
            "completion_tokens": getattr(usage, "output_tokens", None),
            "cached_tokens": getattr(
                getattr(usage, "input_tokens_details", None), "cached_tokens", None
            ),
        }
        reasoning_tokens = getattr(
            getattr(usage, "output_tokens_details", None), "reasoning_tokens", None
        )

        logger.info(
            "OpenAI response received: model=%s, prompt_tokens=%s, completion_tokens=%s "
            "(reasoning=%s), cached=%s",
            response.model,
            tokens["prompt_tokens"],
            tokens["completion_tokens"],
            reasoning_tokens,
            tokens["cached_tokens"],
        )
        return tokens
