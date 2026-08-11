import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROVIDER_CONFIGS = ["NVIDIA", "OPENAI", "GEMINI", "LLAMA"]
PROVIDER_DISPLAY_NAMES = {
    "nvidia": "NVIDIA",
    "openai": "OpenAI",
    "gemini": "Gemini",
    "llama": "Llama",
}


class ChatService:
    def __init__(self, api_key: str | None = None):
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
        self.default_provider = os.getenv("DEFAULT_PROVIDER", "nvidia").strip().lower()
        supported_providers_env = os.getenv("SUPPORTED_PROVIDERS", "")
        if supported_providers_env:
            self.supported_providers = [
                provider.strip().lower()
                for provider in supported_providers_env.split(",")
                if provider.strip()
            ]
        else:
            self.supported_providers = [provider.lower() for provider in PROVIDER_CONFIGS]

        self.providers = {
            provider.lower(): self._load_provider_config(provider)
            for provider in PROVIDER_CONFIGS
        }

        if api_key:
            self.providers[self.default_provider]["api_key"] = api_key

    def _load_provider_config(self, prefix: str) -> dict[str, str | int | float | list[str]]:
        return {
            "api_key": os.getenv(f"{prefix}_API_KEY"),
            "api_url": os.getenv(f"{prefix}_API_URL"),
            "model": os.getenv(f"{prefix}_MODEL"),
            "supported_models": [
                model.strip()
                for model in os.getenv(f"{prefix}_SUPPORTED_MODELS", "").split(",")
                if model.strip()
            ],
        }

    def get_response(self, message: str, model: str | None = None, provider: str | None = None) -> str:
        chosen_provider = (provider or self.default_provider).strip().lower()
        if chosen_provider not in self.supported_providers:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Provider '{chosen_provider}' is not supported. "
                    f"Supported providers: {', '.join(self.supported_providers)}"
                ),
            )

        provider_config = self.providers.get(chosen_provider, {})

        if chosen_provider == "llama":
            chosen_model = model or provider_config.get("model")
            if not chosen_model:
                raise HTTPException(status_code=500, detail="Model is not configured for llama")
            return self._call_ollama(chosen_model, message)

        api_key = provider_config.get("api_key")
        invoke_url = provider_config.get("api_url")
        default_model = provider_config.get("model")
        supported_models = provider_config.get("supported_models", [])

        if not api_key:
            raise HTTPException(status_code=500, detail=f"{chosen_provider.upper()}_API_KEY is not configured")
        if not invoke_url:
            raise HTTPException(status_code=500, detail=f"{chosen_provider.upper()}_API_URL is not configured")

        chosen_model = model or default_model
        if not chosen_model:
            raise HTTPException(status_code=500, detail=f"Model is not configured for {chosen_provider}")

        if supported_models and chosen_model not in supported_models:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Model '{chosen_model}' is not supported for {chosen_provider}. "
                    f"Supported models: {', '.join(supported_models)}"
                ),
            )

        if chosen_provider == "gemini":
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": api_key,
            }
        else:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }

        payload = self._build_payload(chosen_provider, chosen_model, message, provider_config)

        response = requests.post(invoke_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid JSON returned from provider API") from exc

        if chosen_provider == "gemini":
            content = self._extract_gemini_content(data)
        else:
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content:
            raise HTTPException(status_code=502, detail="No content returned from provider API")

        return content

    def _build_payload(self, provider: str, model: str, message: str, config: dict) -> dict:
        if provider == "gemini":
            return {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": message,
                            }
                        ]
                    }
                ],
            }

        if provider == "nvidia":
            return {
                "model": model,
                "messages": [{"role": "user", "content": message}],
            }

        return {
            "model": model,
            "messages": [{"role": "user", "content": message}]
        }

    def _call_ollama(self, model: str, message: str) -> str:
        try:
            from ollama import chat as ollama_chat
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="Ollama SDK is not installed. Install it with 'pip install ollama'.",
            ) from exc

        try:
            response = ollama_chat(
                model=model,
                messages=[{"role": "user", "content": message}],
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        content = ""
        if hasattr(response, "message"):
            message_obj = getattr(response, "message")
            if hasattr(message_obj, "content"):
                content = getattr(message_obj, "content")
            elif isinstance(message_obj, dict):
                content = message_obj.get("content", "")
        elif isinstance(response, dict):
            content = response.get("message", {}).get("content", "")
        elif response is not None:
            content = str(response)

        if not content:
            raise HTTPException(status_code=502, detail="No content returned from Ollama chat response")

        return content

    def _extract_gemini_content(self, data: dict) -> str:
        candidates = data.get("candidates") or []
        if isinstance(candidates, dict):
            candidates = [candidates]

        for candidate in candidates:
            content = candidate.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if text := item.get("text"):
                            return text
                        if content_text := item.get("content"):
                            return content_text
                    elif item is not None:
                        return str(item)
            elif isinstance(content, dict):
                if text := content.get("text"):
                    return text
                if content_text := content.get("content"):
                    return content_text
                parts = content.get("parts") or []
                if isinstance(parts, list) and parts:
                    first_part = parts[0]
                    if isinstance(first_part, dict):
                        if text := first_part.get("text"):
                            return text
                        if content_text := first_part.get("content"):
                            return content_text
                    elif first_part is not None:
                        return str(first_part)
            elif content:
                return str(content)

        # fallback for alternative Gemini structures
        output = data.get("output") or data.get("response") or {}
        if isinstance(output, dict):
            if "text" in output:
                return output["text"]
            if "content" in output:
                output_content = output["content"]
                if isinstance(output_content, list):
                    for part in output_content:
                        if isinstance(part, dict):
                            if text := part.get("text"):
                                return text
                            if content_text := part.get("content"):
                                return content_text
                        elif part is not None:
                            return str(part)
                elif isinstance(output_content, str):
                    return output_content

        return ""

    def get_integrated_models(self) -> list[dict[str, str]]:
        models = []
        for provider in self.supported_providers:
            config = self.providers.get(provider, {})
            default_model = config.get("model")
            supported_models = config.get("supported_models", [])

            seen: set[str] = set()
            provider_model_names = []

            if default_model:
                provider_model_names.append(default_model)
            provider_model_names.extend(supported_models)

            for model in provider_model_names:
                short_name = self._short_model_name(model)
                if not short_name or short_name in seen:
                    continue
                seen.add(short_name)
                models.append({
                    "provider": PROVIDER_DISPLAY_NAMES.get(provider, provider.title()),
                    "model": short_name,
                })
        return models

    def _short_model_name(self, model_name: str) -> str:
        return model_name
