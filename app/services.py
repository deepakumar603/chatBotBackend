import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ChatService:
    def __init__(self, api_key: str | None = None):
        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.invoke_url = os.getenv("NVIDIA_API_URL")
        self.model = os.getenv("NVIDIA_MODEL")
        self.temperature = float(os.getenv("NVIDIA_TEMPERATURE"))
        self.top_p = float(os.getenv("NVIDIA_TOP_P"))
        self.max_tokens = int(os.getenv("NVIDIA_MAX_TOKENS"))

    def get_response(self, message: str) -> str:
        if not self.api_key:
            raise HTTPException(status_code=500, detail="NVIDIA_API_KEY is not configured")

        stream = False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream" if stream else "application/json",
        }

        payload = {
            "messages": [{"role": "user", "content": message}],
            "model": self.model,
            "max_tokens": self.max_tokens,
            "stream": False,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        response = requests.post(self.invoke_url, headers=headers, json=payload, stream=stream, timeout=60)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid JSON returned from NVIDIA API") from exc

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise HTTPException(status_code=502, detail="No content returned from NVIDIA API")

        return content
