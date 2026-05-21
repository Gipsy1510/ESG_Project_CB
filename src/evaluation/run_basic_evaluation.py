import csv
from pathlib import Path

import pandas as pd

from src.rag.retrieval import load_chunks_with_embeddings, retrieve_top_chunks
from src.rag.answer_generation import generate_answer


ROOT = Path(__file__).resolve().parents[2]
def load_questions(path: str) -> list[dict]:
    questions_path = ROOT / path

    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")

    with questions_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_expected_pages(value: str) -> list[int]:
    pages = []

    for item in value.split("|"):
        item = item.strip()

        if item:
            pages.append(int(item))

    return pages


def parse_required_terms(value: str) -> list[str]:
    if not value:
        return []

    terms = []

    for item in value.split(";"):
        item = item.strip()

        if item:
            terms.append(item)

    return terms

def normalize_text(text: str) -> str:
    """
    Normalize text for simple evaluation checks.

    This makes the term matching less brittle by ignoring punctuation,
    capitalization, and small formatting differences.
    """
    text = text.lower()
    text = text.replace("-", " ")
    text = text.replace("–", " ")
    text = text.replace("—", " ")

    for char in [".", ",", ":", ";", "(", ")", "[", "]", "%"]:
        text = text.replace(char, " ")

    return " ".join(text.split())

def check_required_terms(answer: str, required_terms: list[str]) -> dict:
    normalized_answer = normalize_text(answer)

    found_terms = []
    missing_terms = []

    for term in required_terms:
        normalized_term = normalize_text(term)

        if normalized_term in normalized_answer:
            found_terms.append(term)
        else:
            missing_terms.append(term)

    if not required_terms:
        score = None
    else:
        score = len(found_terms) / len(required_terms)

    return {
        "required_terms": required_terms,
        "found_terms": found_terms,
        "missing_terms": missing_terms,
        "required_terms_score": score,
    }


def evaluate_question(question_row: dict, chunks: list[dict], top_k: int = 5) -> dict:
    question = question_row["question"]
    expected_pages = parse_expected_pages(question_row["expected_pages"])

    retrieved_chunks = retrieve_top_chunks(
        query=question,
        chunks=chunks,
        top_k=top_k,
    )

    retrieved_pages = [chunk["page"] for chunk in retrieved_chunks]

    expected_page_in_top_k = any(
        page in retrieved_pages
        for page in expected_pages
    )

    answer = generate_answer(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )

    manual_answer_available = (
        question_row.get("manual_answer_available", "").strip().lower() == "yes"
    )

    required_terms = parse_required_terms(question_row.get("answer_must_contain", ""))

    term_check = check_required_terms(
        answer=answer,
        required_terms=required_terms,
    )

    return {
        "question_id": question_row["question_id"],
        "company": question_row["company"],
        "question_type": question_row["question_type"],
        "topic": question_row["topic"],
        "question": question,
        "expected_pages": expected_pages,
        "retrieved_pages": retrieved_pages,
        "expected_page_in_top_k": expected_page_in_top_k,
        "top_page": retrieved_pages[0] if retrieved_pages else None,
        "answer": answer,
        "human_answer": question_row.get("human_answer", ""),
        "human_evidence": question_row.get("human_evidence", ""),
        "manual_answer_available": manual_answer_available,
        "required_terms": term_check["required_terms"],
        "found_terms": term_check["found_terms"],
        "missing_terms": term_check["missing_terms"],
        "required_terms_score": term_check["required_terms_score"],
    }


def summarize_results(results: list[dict]) -> None:
    df = pd.DataFrame(results)

    print("\nOverall retrieval performance")
    print("=" * 80)
    print(f"Questions evaluated: {len(df)}")
    print(f"Expected page in top 5: {df['expected_page_in_top_k'].mean():.2%}")

    if "required_terms_score" in df.columns:
        scored = df.dropna(subset=["required_terms_score"])

        if len(scored) > 0:
            print(f"Average required terms score: {scored['required_terms_score'].mean():.2%}")

    print("\nPerformance by question type")
    print("=" * 80)

    summary = (
        df.groupby("question_type")
        .agg(
            questions=("question_id", "count"),
            expected_page_in_top_k=("expected_page_in_top_k", "mean"),
            required_terms_score=("required_terms_score", "mean"),
        )
        .reset_index()
    )

    for _, row in summary.iterrows():
        print(
            f"{row['question_type']}: "
            f"{int(row['questions'])} questions, "
            f"{row['expected_page_in_top_k']:.2%} expected page in top 5, "
            f"{row['required_terms_score']:.2%} required terms score"
        )


def save_results(results: list[dict], output_path: str) -> None:
    output_file = ROOT / output_path
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"\nSaved evaluation results to: {output_file}")


if __name__ == "__main__":
    questions = load_questions("data/evaluation/esg_questions.csv")

    chunks = load_chunks_with_embeddings(
        "data/processed_text/totalenergies_2024_chunk_embeddings.json"
    )

    results = []

    for row in questions:
        print(f"\nEvaluating {row['question_id']}: {row['question_type']} / {row['topic']}")

        result = evaluate_question(
            question_row=row,
            chunks=chunks,
            top_k=5,
        )

        print(f"Expected pages: {result['expected_pages']}")
        print(f"Retrieved pages: {result['retrieved_pages']}")
        print(f"Expected page in top 5: {result['expected_page_in_top_k']}")

        if result["manual_answer_available"]:
            print(f"Required terms score: {result['required_terms_score']:.2%}")
            print(f"Missing terms: {result['missing_terms']}")

        results.append(result)

    summarize_results(results)

    save_results(
        results=results,
        output_path="outputs/answers/basic_evaluation_results.csv",
    )