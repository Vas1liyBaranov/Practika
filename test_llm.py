import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

resp = client.chat.completions.create(
    model="microsoft/phi-3-mini-128k-instruct:free",
    messages=[{"role": "user", "content": "Привет! Ответь одним словом: работает?"}],
)

print(resp.choices[0].message.content)
