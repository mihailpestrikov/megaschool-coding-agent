import os
from typing import TypeVar

import litellm

from coding_agent.config import Settings
from coding_agent.llm.prompts import CODE_GENERATION_PROMPT, FIX_PROMPT, REVIEW_PROMPT
from coding_agent.llm.schemas import CodeGenerationResult, ReviewResult

T = TypeVar("T")


class LLMClient:
    def __init__(self, settings: Settings):
        self.model = settings.llm_model
        self._setup_api_keys(settings)

    def _setup_api_keys(self, settings: Settings):
        if settings.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        if settings.xai_api_key:
            os.environ["XAI_API_KEY"] = settings.xai_api_key

    def generate_code(
        self, issue_title: str, issue_body: str, context: str
    ) -> CodeGenerationResult:
        prompt = CODE_GENERATION_PROMPT.format(
            issue_title=issue_title,
            issue_body=issue_body,
            context=context,
        )
        return self._generate_json(prompt, CodeGenerationResult)

    def generate_review(
        self, diff: str, issue_title: str, issue_body: str, ci_status: str
    ) -> ReviewResult:
        prompt = REVIEW_PROMPT.format(
            diff=diff,
            issue_title=issue_title,
            issue_body=issue_body,
            ci_status=ci_status,
        )
        return self._generate_json(prompt, ReviewResult)

    def generate_fix(
        self, feedback: str, issue_title: str, issue_body: str, context: str
    ) -> CodeGenerationResult:
        prompt = FIX_PROMPT.format(
            feedback=feedback,
            issue_title=issue_title,
            issue_body=issue_body,
            context=context,
        )
        return self._generate_json(prompt, CodeGenerationResult)

    def _generate_json(self, prompt: str, schema: type[T]) -> T:
        schema_json = schema.model_json_schema()

        system_msg = (
            "Ты должен ответить ТОЛЬКО валидным JSON объектом по схеме.\n"
            f"JSON Schema: {schema_json}"
        )

        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        text = response.choices[0].message.content
        return schema.model_validate_json(text)
