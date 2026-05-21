import os
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from src.rag.retrieval import retrieve_top_chunks

def get_chat_client() -> OpenAI:
    """
    Create an Albert API client for chat completions.
    """
    load_dotenv()

    api_key = os.getenv("ALBERT_API_KEY")
    base_url = os.getenv("ALBERT_BASE_URL")

    if not api_key:
        raise ValueError("ALBERT_API_KEY is missing. Check your .env file.")

    if not base_url:
        raise ValueError("ALBERT_BASE_URL is missing. Check your .env file.")

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


def format_context(chunks: List[Dict]) -> str:
    """
    Format retrieved chunks as evidence for the LLM.
    """
    context_blocks = []

    for idx, chunk in enumerate(chunks, start=1):
        block = f"""
[Source {idx}]
Company: {chunk["company"]}
Year: {chunk["year"]}
Page: {chunk["page"]}
Chunk ID: {chunk["chunk_id"]}
Text:
{chunk["text"]}
"""
        context_blocks.append(block.strip())

    return "\n\n".join(context_blocks)


def generate_answer(question: str, retrieved_chunks: List[Dict]) -> str:
    """
    Generate an ESG answer using only retrieved evidence.
    """
    load_dotenv()

    model = os.getenv(
        "ALBERT_CHAT_MODEL",
        "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
    )

    client = get_chat_client()
    context = format_context(retrieved_chunks)

    system_prompt = """
You are an ESG analyst assistant.

Answer the question using only the provided report excerpts.
Do not use external knowledge.
Do not invent numbers, targets, dates, or claims.
If the evidence is not sufficient, say so clearly.

Your disclosure status must be internally consistent with the limitations.
Use Fully disclosed only if the retrieved context directly answers all parts of the question.
Use Partially disclosed if the answer is approximate, aggregated, incomplete, or lacks a required breakdown.
Use Not found if the retrieved context does not contain enough evidence.

Be especially careful with tables and numerical ESG indicators.
When answering questions about EU Taxonomy, always distinguish between:
1. eligible activities
2. aligned activities
3. turnover
4. CapEx
5. controlled perimeter
6. proportional view

If the question asks for aligned CapEx, do not answer with eligible CapEx.
If the question asks for total company CapEx, use the TOTAL row.
Do not answer with a specific activity row, such as Electricity and renewables, unless the question explicitly asks for that activity.
If both eligible CapEx and aligned CapEx appear in the same table, identify both and explain which one answers the question.
If the table structure is ambiguous, say that the evidence is ambiguous instead of choosing a number silently.

When reading EU Taxonomy tables:
1. If the question asks for a general company percentage, use the TOTAL row.
2. Do not answer with a specific activity row unless the question explicitly asks for that activity.
3. If several rows appear, first identify whether the value comes from an activity row or from the TOTAL row.
4. For aligned CapEx, the final answer must come from the aligned activities CapEx column, not from eligible activities and not from turnover.
5. If you provide a table check, use these labels exactly:
   Eligible Turnover 2023:
   Eligible CapEx 2023:
   Aligned Turnover 2023:
   Aligned CapEx 2023:
   Row used:
   Perimeter used:

Do not label a turnover value as CapEx.
If you cannot confidently identify all table values, only report the value needed to answer the question and state the ambiguity.

For numerical answers:
1. quote the exact value used
2. explain what the value refers to
3. mention the page number
4. mention any relevant perimeter or scope
5. explain why this value answers the question and why nearby values do not

Use this structure:

1. Direct answer
2. Disclosure status: Fully disclosed / Partially disclosed / Not found
3. Evidence from the report
4. Sources used, with page numbers
5. Limitations
"""
    user_prompt = f"""
Question:
{question}

Retrieved context:
{context}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    input_path = "data/processed_text/totalenergies_2024_chunk_embeddings.json"

    chunks = load_chunks_with_embeddings(input_path)

    questions = [
    "What are TotalEnergies Scope 1 and Scope 2 greenhouse gas emissions?",
    "What is TotalEnergies climate transition plan?",
    "What percentage of TotalEnergies total CapEx is aligned with the EU Taxonomy in 2023 under the controlled perimeter?",
]

    for question in questions:
        retrieved_chunks = retrieve_top_chunks(
            query=question,
            chunks=chunks,
            top_k=5,
        )

        answer = generate_answer(
            question=question,
            retrieved_chunks=retrieved_chunks,
        )

        print("\n" + "=" * 100)
        print("QUESTION")
        print("-" * 100)
        print(question)

        print("\nANSWER")
        print("-" * 100)
        print(answer)

        print("\nRETRIEVED SOURCES")
        print("-" * 100)
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            print(
                f"Source {idx}: page {chunk['page']} | "
                f"score={chunk['score']:.4f} | "
                f"chunk_id={chunk['chunk_id']}"
            )