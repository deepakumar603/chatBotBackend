# ChatBot Backend

A minimal FastAPI backend project scaffold for a chat bot service.

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
