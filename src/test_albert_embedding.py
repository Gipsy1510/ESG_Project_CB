import os
from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("ALBERT_API_KEY"),
        base_url=os.getenv("ALBERT_BASE_URL"),
    )

    model = os.getenv("ALBERT_EMBEDDING_MODEL", "BAAI/bge-m3")

    response = client.embeddings.create(
        model=model,
        input="This is a simple embedding test for an ESG report.",
    )

    embedding = response.data[0].embedding

    print("Embedding test works.")
    print(f"Model: {model}")
    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    main()