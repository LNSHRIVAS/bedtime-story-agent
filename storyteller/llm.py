from openai import OpenAI


_client = OpenAI()


def call_model(prompt: str, max_tokens: int = 3000, temperature: float = 0.1) -> str:
    response = _client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""

