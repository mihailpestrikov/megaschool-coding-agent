from google import genai
from google.genai.types import GenerateContentConfig

from coding_agent.config import Settings
from coding_agent.llm.schemas import CodeGenerationResult, ReviewResult
from coding_agent.llm.prompts import CODE_GENERATION_PROMPT, REVIEW_PROMPT, FIX_PROMPT


class LLMClient:
    def __init__(self, settings: Settings):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def generate_code(self, issue_title: str, issue_body: str, context: str) -> CodeGenerationResult:
        """Сгенерировать код по описанию Issue."""
        prompt = CODE_GENERATION_PROMPT.format(
            issue_title=issue_title,
            issue_body=issue_body,
            context=context,
        )
        return self._generate_json(prompt, CodeGenerationResult)

    def generate_review(
        self, diff: str, issue_title: str, issue_body: str, ci_status: str
    ) -> ReviewResult:
        """Сгенерировать ревью для PR."""
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
        """Сгенерировать исправления по замечаниям."""
        prompt = FIX_PROMPT.format(
            feedback=feedback,
            issue_title=issue_title,
            issue_body=issue_body,
            context=context,
        )
        return self._generate_json(prompt, CodeGenerationResult)

    def _generate_json[T](self, prompt: str, schema: type[T]) -> T:
        """Сгенерировать ответ в формате JSON по схеме."""
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
