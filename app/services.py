import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)


class ChatService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.invoke_url = os.getenv("NVIDIA_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")

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
            "model": "mistralai/mistral-medium-3.5-128b",
            "reasoning_effort": "high",
            "max_tokens": 16384,
            "stream": stream,
            "temperature": 0.7,
            "top_p": 1,
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
