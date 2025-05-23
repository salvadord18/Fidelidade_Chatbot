# Imports
import csv
import os
import time

import pdfplumber
from fuzzywuzzy import fuzz
from sentence_transformers import util

from api import *
from app import assistant, client
from bot import instructions


def get_next_seq_filename(folder, base_filename, ext="csv"):
    # Create folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    
    existing_files = [f for f in os.listdir(folder) if f.startswith(base_filename) and f.endswith(f".{ext}")]
    
    # Extract sequence numbers from filenames like base_filename_1.csv, base_filename_2.csv, ...
    seq_numbers = []
    for f in existing_files:
        parts = f.replace(f".{ext}", "").split("_")
        if parts[-1].isdigit():
            seq_numbers.append(int(parts[-1]))
    
    next_seq = max(seq_numbers, default=0) + 1
    return os.path.join(folder, f"{base_filename}_{next_seq}.{ext}")

def save_results_seq(results, folder, base_filename="results"):
    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)
    
    filepath = get_next_seq_filename(folder, base_filename)
    
    if results:
        with open(filepath, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"Saved results to: {filepath}")
    return filepath

def extract_qa_pairs_from_pdf(pdf_path):
    def save_current_pair():
        if question_lines and answer_lines:
            qa_pairs.append((
                " ".join(question_lines).strip(),
                " ".join(answer_lines).strip()
            ))

    qa_pairs = []
    question_lines, answer_lines = [], []
    mode = None  # 'question' or 'answer'

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    for line in full_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("•"):
            save_current_pair()
            question_lines = [line.removeprefix("•").strip()]
            answer_lines = []
            mode = 'question'

        elif line.startswith("R:"):
            answer_lines = [line.removeprefix("R:").strip()]
            mode = 'answer'

        elif mode == 'question':
            question_lines.append(line)
        elif mode == 'answer':
            answer_lines.append(line)

    save_current_pair()  # Save any remaining pair
    return qa_pairs

# --- Ask a Question using your Assistant ---
def query_assistant(question):
    thread = client.beta.threads.create()

    # Add system instructions + user question
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"{instructions}\n\n{question}"
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Wait for the run to complete
    while run.status in ['queued', 'in_progress']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status != 'completed':
        return "[ERROR] Assistant run failed."

    # Get assistant message
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for msg in messages.data:
        if msg.role == "assistant":
            return msg.content[0].text.value.strip()

    return "[No assistant response]"


# --- Evaluate and Save Results ---
def evaluate_string_and_save(qa_pairs, threshold=0.7):
    total = len(qa_pairs)
    correct = 0
    total_time = 0.0

    results = []

    for idx, (question, expected) in enumerate(qa_pairs, 1):
        print(f"\n--- Q{idx} ---")
        print("Question:", question)

        start = time.time()
        answer = query_assistant(question)
        response_time = time.time() - start
        total_time += response_time

        similarity = fuzz.ratio(answer.lower(), expected.lower())
        match = "Yes" if similarity >= threshold else "No"
        if match == "Yes":
            correct += 1

        print()
        print("Answer:", answer)
        print()
        print("Expected:", expected)
        print()
        print(f"Similarity: {similarity}, Match: {match}, Time: {response_time:.2f}s")

        results.append({
            "Question": question,
            "Expected Answer": expected,
            "Chatbot Answer": answer,
            "Similarity": similarity,
            "Match": match,
            "Response Time (s)": round(response_time, 2)
        })

    accuracy = (correct / total * 100) if total else 0
    avg_response = (total_time / total) if total else 0

    # Save to CSV
    save_results_seq(results, folder="eval_string", base_filename="eval_results")


    print("\n===== Summary =====")
    print(f"Total: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Average Response Time: {avg_response:.2f}s")

def get_next_seq_filename(folder, base_filename, ext="csv"):
    os.makedirs(folder, exist_ok=True)
    existing_files = [f for f in os.listdir(folder) if f.startswith(base_filename) and f.endswith(f".{ext}")]
    seq_numbers = []
    for f in existing_files:
        parts = f.replace(f".{ext}", "").split("_")
        if parts[-1].isdigit():
            seq_numbers.append(int(parts[-1]))
    next_seq = max(seq_numbers, default=0) + 1
    return os.path.join(folder, f"{base_filename}_{next_seq}.{ext}")

def save_results_seq(results, folder="evaluation_results", base_filename="results"):
    os.makedirs(folder, exist_ok=True)
    filepath = get_next_seq_filename(folder, base_filename)
    if results:
        with open(filepath, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"Saved results to: {filepath}")
    return filepath

def evaluate_semantic_and_save(qa_pairs, model, threshold=0.7, save_results_seq=None):
    total = len(qa_pairs)
    correct = 0
    total_time = 0.0

    results = []
    mismatches = []

    for idx, (question, expected) in enumerate(qa_pairs, 1):
        print(f"\n--- Q{idx} ---")
        print("Question:", question)

        start = time.time()
        answer = query_assistant(question)
        response_time = time.time() - start
        total_time += response_time

        emb_answer = model.encode(answer, convert_to_tensor=True)
        emb_expected = model.encode(expected, convert_to_tensor=True)

        cosine_sim = util.pytorch_cos_sim(emb_answer, emb_expected).item()
        match = "Yes" if cosine_sim >= threshold else "No"
        if match == "Yes":
            correct += 1

        print("Answer:", answer)
        print("Expected:", expected)
        print('----------------------------------')
        print(f"Cosine Similarity: {cosine_sim:.2f}, Match: {match}, Time: {response_time:.2f}s")

        result_row = {
            "Question": question,
            "Expected Answer": expected,
            "Chatbot Answer": answer,
            "Cosine Similarity": round(cosine_sim, 2),
            "Match": match,
            "Response Time (s)": round(response_time, 2)
        }
        results.append(result_row)

        if match == "No":
            mismatches.append(result_row)

    accuracy = (correct / total * 100) if total else 0
    avg_response = (total_time / total) if total else 0

    if save_results_seq:
        save_results_seq(results, folder="eval_semantic", base_filename="eval_results")

    print("\n===== Summary =====")
    print(f"Total Questions: {total}")
    print(f"Correct Answers: {correct}")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Average Response Time: {avg_response:.2f}s")
