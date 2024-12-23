import openai
from token_gpt import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


async def get_gpt_response(prompt: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — помощник для управления событиями. "
                    "Отвечай только необходимым текстом, строго в соответствии с запросом, без лишних комментариев."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()
