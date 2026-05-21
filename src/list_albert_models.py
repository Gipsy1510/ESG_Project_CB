import os
from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("ALBERT_API_KEY"),
        base_url=os.getenv("ALBERT_BASE_URL"),
    )

    models = client.models.list()

    print("Available models:")
    for model in models.data:
        print(model.id)


if __name__ == "__main__":
    main()