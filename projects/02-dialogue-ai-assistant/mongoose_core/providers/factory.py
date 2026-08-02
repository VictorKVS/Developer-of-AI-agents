from django.conf import settings

from mongoose_core.ports.llm import LLMProvider
from mongoose_core.providers.gemini import GeminiProvider
from mongoose_core.providers.gigachat import GigaChatProvider


def build_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "gigachat":
        return GigaChatProvider(
            credentials=settings.GIGACHAT_CREDENTIALS,
            model=settings.GIGACHAT_MODEL,
            scope=settings.GIGACHAT_SCOPE,
            verify_ssl_certs=settings.GIGACHAT_VERIFY_SSL_CERTS,
            ca_bundle_file=settings.GIGACHAT_CA_BUNDLE_FILE,
        )

    if provider == "gemini":
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_DIALOGUE_MODEL,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
