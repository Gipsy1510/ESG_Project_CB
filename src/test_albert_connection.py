import os
from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    api_key = os.getenv("ALBERT_API_KEY")
    base_url = os.getenv("ALBERT_BASE_URL")
    model = os.getenv("ALBERT_CHAT_MODEL", "albert-large")

    if not api_key:
        raise ValueError("ALBERT_API_KEY is missing. Check your .env file.")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with only this sentence: Albert API connection works.",
            }
        ],
        temperature=0,
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()