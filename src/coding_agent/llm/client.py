from typing import TypeVar

from google import genai
from google.genai.types import GenerateContentConfig

from coding_agent.config import Settings
from coding_agent.llm.prompts import CODE_GENERATION_PROMPT, FIX_PROMPT, REVIEW_PROMPT
from coding_agent.llm.schemas import CodeGenerationResult, ReviewResult

T = TypeVar("T")


class LLMClient:
    def __init__(self, settings: Settings):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

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
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return schema.model_validate_json(response.text)
