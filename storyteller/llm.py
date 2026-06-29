import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError(
        "OPENAI_API_KEY is not set. "
        "Create a .env file with OPENAI_API_KEY=sk-... "
        "or set it as an environment variable."
    )

_client = OpenAI()


def call_model(prompt: str, max_tokens: int = 3000, temperature: float = 0.1) -> str:
    response = _client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""

