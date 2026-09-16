"""Inference engine interfacing with apple-fm-sdk."""

import asyncio
from typing import Optional, Tuple
import apple_fm_sdk as fm

from git_afm.models import ConventionalCommit, PullRequestSummary
from git_afm.git_utils import filter_and_truncate_diff

COMMIT_SYSTEM_INSTRUCTIONS = {
    "en": (
        "You are an expert software engineer and git commit assistant. "
        "Analyze the provided git diff and generate an accurate Conventional Commit. "
        "Rules: "
        "1. type must be one of: feat, fix, refactor, perf, test, docs, chore, build, ci. "
        "2. scope should be a concise lowercase noun (e.g. cli, engine, models, ui, auth) or empty if global. "
        "3. subject must be in imperative mood (e.g. 'add feature', not 'added' or 'adds'), no trailing period, maximum 72 chars. "
        "4. bullet_points should highlight 1 to 4 key functional or architectural changes. "
        "5. Output must strictly adhere to the requested schema."
    ),
    "pt": (
        "Você é um engenheiro de software especialista e assistente de commits git. "
        "Analise o git diff fornecido e gere um Conventional Commit preciso. "
        "Regras: "
        "1. type deve ser um de: feat, fix, refactor, perf, test, docs, chore, build, ci. "
        "2. scope deve ser um substantivo curto em minúsculas (ex: cli, engine, models, ui, auth) ou vazio se geral. "
        "3. subject deve estar no imperativo em português (ex: 'adiciona suporte', 'corrige bug', 'refatora lógica'), sem ponto final. "
        "4. bullet_points deve listar de 1 a 4 pontos chave explicando o que mudou e por quê, em português. "
        "5. A saída deve aderir estritamente ao schema solicitado."
    ),
}

PR_SYSTEM_INSTRUCTIONS = {
    "en": (
        "You are an expert tech lead reviewing pull requests. "
        "Generate a comprehensive, high quality Pull Request description in Markdown based on the git diff. "
        "Include an executive summary, list of key changes, and verification steps."
    ),
    "pt": (
        "Você é um tech lead especialista revisando pull requests. "
        "Gere uma descrição completa e de alta qualidade de Pull Request em Markdown com base no git diff. "
        "Inclua um resumo executivo, lista de mudanças chave e passos para teste e verificação em português."
    ),
}


class AFMEngine:
    """Manages sessions and structured generation with Apple Foundation Models."""

    def __init__(self):
        self._model: Optional[fm.SystemLanguageModel] = None

    def check_availability(self) -> Tuple[bool, Optional[str]]:
        """Verify if Apple Foundation Models are available on this machine."""
        try:
            self._model = fm.SystemLanguageModel()
            return self._model.is_available()
        except Exception as e:
            return False, str(e)

    def _get_model(self) -> fm.SystemLanguageModel:
        if self._model is None:
            self._model = fm.SystemLanguageModel()
            available, reason = self._model.is_available()
            if not available:
                raise fm.FoundationModelsError(
                    f"Apple Foundation Model is not available on this device: {reason}"
                )
        return self._model

    async def generate_commit(
        self,
        diff_text: str,
        language: str = "en",
        extra_context: Optional[str] = None,
    ) -> ConventionalCommit:
        """Generate a structured Conventional Commit from diff."""
        model = self._get_model()
        instructions = COMMIT_SYSTEM_INSTRUCTIONS.get(language, COMMIT_SYSTEM_INSTRUCTIONS["en"])

        prompt_parts = []
        if extra_context:
            prompt_parts.append(f"Developer note/intent: {extra_context}\n")

        cleaned_diff = filter_and_truncate_diff(diff_text, max_chars=12000)
        prompt_parts.append(f"Git Diff:\n```diff\n{cleaned_diff}\n```")
        full_prompt = "\n".join(prompt_parts)

        session = fm.LanguageModelSession(model=model, instructions=instructions)

        try:
            result = await session.respond(full_prompt, generating=ConventionalCommit)
            return result
        except fm.ExceededContextWindowSizeError:
            # Fallback: aggressively truncate diff to 4000 chars and retry
            shrunk_diff = filter_and_truncate_diff(diff_text, max_chars=4000)
            shrunk_prompt = f"Git Diff (summarized):\n```diff\n{shrunk_diff}\n```"
            session = fm.LanguageModelSession(model=model, instructions=instructions)
            return await session.respond(shrunk_prompt, generating=ConventionalCommit)

    async def generate_pr_summary(
        self,
        diff_text: str,
        language: str = "en",
        extra_context: Optional[str] = None,
    ) -> PullRequestSummary:
        """Generate a structured Pull Request description from diff."""
        model = self._get_model()
        instructions = PR_SYSTEM_INSTRUCTIONS.get(language, PR_SYSTEM_INSTRUCTIONS["en"])

        prompt_parts = []
        if extra_context:
            prompt_parts.append(f"Developer context: {extra_context}\n")

        cleaned_diff = filter_and_truncate_diff(diff_text, max_chars=12000)
        prompt_parts.append(f"Git Diff:\n```diff\n{cleaned_diff}\n```")
        full_prompt = "\n".join(prompt_parts)

        session = fm.LanguageModelSession(model=model, instructions=instructions)
        try:
            return await session.respond(full_prompt, generating=PullRequestSummary)
        except fm.ExceededContextWindowSizeError:
            shrunk_diff = filter_and_truncate_diff(diff_text, max_chars=4000)
            session = fm.LanguageModelSession(model=model, instructions=instructions)
            return await session.respond(
                f"Git Diff:\n```diff\n{shrunk_diff}\n```",
                generating=PullRequestSummary,
            )

    async def explain_diff(
        self,
        diff_text: str,
        language: str = "en",
    ) -> str:
        """Explain the diff in conversational paragraphs."""
        model = self._get_model()
        instr = (
            "Explain in 2-3 concise paragraphs what changes are introduced in this diff, "
            "focusing on architectural and business logic impact. "
            f"Respond in {'Portuguese' if language == 'pt' else 'English'}."
        )
        cleaned_diff = filter_and_truncate_diff(diff_text, max_chars=10000)
        session = fm.LanguageModelSession(model=model, instructions=instr)
        return await session.respond(f"```diff\n{cleaned_diff}\n```")
