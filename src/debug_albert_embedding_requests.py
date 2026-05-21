import os
import requests
from dotenv import load_dotenv


def test_embedding(model_name: str):
    load_dotenv()

    api_key = os.getenv("ALBERT_API_KEY")
    base_url = os.getenv("ALBERT_BASE_URL", "https://albert.api.etalab.gouv.fr/v1")

    url = f"{base_url}/embeddings"

    payload = {
        "model": model_name,
        "input": ["This is a simple embedding test for an ESG report."]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"\nTesting model: {model_name}")
    print(f"URL: {url}")

    response = requests.post(url, json=payload, headers=headers, timeout=60)

    print(f"Status code: {response.status_code}")

    try:
        data = response.json()
        print("Response JSON:")
        print(data)

        if response.status_code == 200:
            embedding = data["data"][0]["embedding"]
            print(f"Embedding length: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")

    except Exception:
        print("Raw response:")
        print(response.text)


if __name__ == "__main__":
    test_embedding("BAAI/bge-m3")
    test_embedding("openweight-embeddings")