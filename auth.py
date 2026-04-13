import requests
from config import OPENAI_API_KEY, SESSION_CONFIG


def create_client_secret() -> str:
    resp = requests.post(
        "https://api.openai.com/v1/realtime/client_secrets",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "expires_after": {
                "anchor": "created_at",
                "seconds": 600,
            },
            "session": SESSION_CONFIG,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["value"]