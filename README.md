# ChatBot Backend

A FastAPI backend project that can be connected to any compatible model by updating the model details in the .env file. It is designed to work as a configurable chat agent service. This is tested with NVIDIA's open source model.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /` - root status
- `GET /api/health` - health check
- `POST /api/chat` - send a chat request

## Environment variables

Add these fields to your `.env` file:

```env
NVIDIA_API_KEY=your_api_key_here
NVIDIA_API_URL=your_model_endpoint_url
NVIDIA_MODEL=your_model_name
NVIDIA_TEMPERATURE=your_temperature_value
NVIDIA_TOP_P=your_top_p_value
NVIDIA_MAX_TOKENS=your_max_tokens_value
LLAMA_MODEL=llama3.1
```

For Ollama local Llama 3.1 usage, you only need `LLAMA_MODEL=llama3.1` and the Ollama SDK. The service uses the `ollama.chat()` call directly, so no API key or URL is required for local Ollama installs.

## Example request

URL:

```bash
http://127.0.0.1:8000/api/chat
```

Body:

```json
{
  "message": "Hello, how are you?"
}
```

Curl example:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, how are you?"}'
```
