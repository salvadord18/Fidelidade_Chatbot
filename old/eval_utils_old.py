# Imports
import csv
import os
import time
import pandas as pd
import numpy as np
from tqdm import tqdm

import matplotlib.pyplot as plt
import seaborn as sns

import pdfplumber
from fuzzywuzzy import fuzz
from sentence_transformers import util
import re

from api import *
from app import assistant, client
from bot import instructions
import app as app


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
            full_question = f"[{current_section}] " + " ".join(question_lines).strip()
            full_answer = " ".join(answer_lines).strip()
            qa_pairs.append((full_question, full_answer))

    qa_pairs = []
    question_lines, answer_lines = [], []
    current_section = ""
    mode = None  # 'question' or 'answer'

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    for line in full_text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Get section name
        section_match = re.match(r'^(\d+)\)\s*(.+)', line)
        if section_match:
            current_section = section_match.group(2).strip()
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
def evaluate_string_and_save(qa_pairs, threshold=70, run_once=False, show_print=False):
    total = len(qa_pairs)
    correct = 0
    total_time = 0.0

    results = []

    # Use a single tqdm progress bar and keep output clean
    for idx, (question, expected) in enumerate(tqdm(qa_pairs, desc="Evaluating", leave=True), 1):
        start = time.time()
        answer = query_assistant(question)
        response_time = time.time() - start
        total_time += response_time

        similarity = fuzz.ratio(answer.lower(), expected.lower())
        match = "Yes" if similarity >= threshold else "No"
        if match == "Yes":
            correct += 1

        results.append({
            "Question_ID": idx,
            "Question": question,
            "Expected_Answer": expected,
            "Chatbot_Answer": answer,
            "Similarity": similarity,
            "Match": match,
            "Response_Time_s": round(response_time, 2)
        })

        if show_print:
            tqdm.write(f"\n--- Q{idx} ---")
            tqdm.write(f"Question: {question}")
            tqdm.write(f"Answer: {answer}")
            tqdm.write(f"Expected: {expected}")
            tqdm.write(f"Similarity: {similarity}, Match: {match}, Time: {response_time:.2f}s")
            tqdm.write('----------------------------------')

    accuracy = (correct / total * 100) if total else 0
    avg_response = (total_time / total) if total else 0

    summary = {
        "Total": total,
        "Correct": correct,
        "Accuracy": accuracy,
        "Average_Similarity": sum(r['Similarity'] for r in results) / total if total else 0,
        "Average_Response_Time_s": avg_response,
        "Threshold": threshold,
        "Chatbot_instructions": instructions
    }

    print("\n===== Summary =====")
    print(f"Total: {total}, Correct: {correct}, Accuracy: {accuracy:.2f}%, Avg Response Time: {avg_response:.2f}s")
    
    if run_once:
        save_results_seq(results, folder="eval_string", base_filename="eval_results")
    else:
        return results, summary

def evaluate_semantic_and_save(qa_pairs, model, model_name_str, threshold=0.7, run_once=True, show_print=False):
    total = len(qa_pairs)
    correct = 0
    total_time = 0.0

    results = []

    for idx, (question, expected) in enumerate(tqdm(qa_pairs, desc="Evaluating", leave=True), 1):
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

        result_row = {
            "Question_ID": idx,
            "Question": question,
            "Expected Answer": expected,
            "Chatbot_Answer": answer,
            "Cosine_Similarity": round(cosine_sim, 2),
            "Match": match,
            "Response_Time_s": round(response_time, 2)
        }
        results.append(result_row)

        if show_print:
            tqdm.write(f"\n--- Q{idx} ---")
            tqdm.write(f"Question: {question}")
            tqdm.write(f"Answer: {answer}")
            tqdm.write(f"Expected: {expected}")
            tqdm.write(f"Cosine Similarity: {cosine_sim:.2f}, Match: {match}, Time: {response_time:.2f}s")
            tqdm.write('----------------------------------')

    accuracy = (correct / total * 100) if total else 0
    avg_response = (total_time / total) if total else 0

    summary = {
        "Total": total,
        "Correct": correct,
        "Accuracy": accuracy,
        "Average_Similarity": sum(r['Cosine_Similarity'] for r in results) / total if total else 0,
        "Average_Response_Time_s": avg_response,
        "Threshold": threshold,
        "Model": str(model),
        "Chatbot_instructions": instructions
    }

    print("\n===== Summary =====")
    print(f"Total: {total}, Correct: {correct}, Accuracy: {accuracy:.2f}%, Avg Response Time: {avg_response:.2f}s")

    if run_once:
        save_results_seq(results, folder="evaluation", base_filename=f"{model_name_str}_eval_results_{threshold}")

    return results, summary 
    

def run_multiple_evaluations(qa_pairs, num_runs, threshold,
                             evaluation_func=None,
                             model=None,
                             summary_folder="evaluation",
                             summary_filename="summary_results",
                             detailed_filename="detailed_results"):

    if evaluation_func is None:
        raise ValueError("You must provide an evaluation function.")

    os.makedirs(summary_folder, exist_ok=True)

    all_detailed = []
    all_summaries = []

    for run_idx in range(1, num_runs + 1):
        print(f"\n### Running Evaluation {run_idx}/{num_runs} ###")

        # Pass the model to the evaluation function if it's a semantic eval
        if model is not None:
            results, summary = evaluation_func(qa_pairs=qa_pairs, model=model, threshold=threshold, run_once=False)
        else:
            results, summary = evaluation_func(qa_pairs=qa_pairs, threshold=threshold, run_once=False)

        # Add run index to each detailed result
        for r in results:
            r["Run"] = run_idx
        all_detailed.extend(results)

        summary["Run"] = run_idx
        all_summaries.append(summary)

    # Save detailed results CSV
    detailed_df = pd.DataFrame(all_detailed)
    detailed_csv_path = os.path.join(summary_folder, f"{detailed_filename}.csv")
    detailed_df.to_csv(detailed_csv_path, index=False)

    # Save summary CSV
    summary_df = pd.DataFrame(all_summaries)
    summary_csv_path = os.path.join(summary_folder, f"{summary_filename}.csv")
    summary_df.to_csv(summary_csv_path, index=False)

    print(f"\nSaved detailed results to: {detailed_csv_path}")
    print(f"Saved summary results to: {summary_csv_path}")


# --- Evaluattion Bot ---
instructions2 = ('Give a general similarity score between expected answer and actual answer. \
                 The answers are supposed to be similar and transmite more or less the same message. \
                 If the actual answer looks more complete than the expected answer, the similarity score should be higher.\
                 Output should be a whole number between 0-10. Do not write anything else')


assistant2 = client.beta.assistants.create(
  model="gpt-4o-mini", 
  instructions="",
  tools=[{"type":"file_search"}],
  tool_resources={"file_search":{"vector_store_ids":["vs_ezpssNVZDpwb0RjgcxSwbNZz"]}},
  temperature=0.2,
  top_p=1
)

def eval_chat(question, expected_answer, actual_answer):

    client = app.client

    instructions = instructions2

    # Create a new thread
    thread = client.beta.threads.create()

    # Prepare the prompt
    prompt = f"{instructions}\n\nQuestion: {question}\nExpected Answer: {expected_answer}\nActual Answer: {actual_answer}"

    # Send the message
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant2.id
    )

    # Wait until it's done
    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve and return the response
    if run.status == "completed":
        messages_list = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages_list.data):
            if msg.role == "assistant":
                response = msg.content[0].text.value.strip()
                return response
    return "[ERROR] Failed to get assistant response."

def answer_faq(qa_pairs, model, show_print=False):
    data = []
    for idx, (question, expected) in enumerate(tqdm(qa_pairs, desc="Answering the FAQ"), 1):
        start = time.time()
        answer = query_assistant(question)
        response_time = time.time() - start

        emb_answer = model.encode(answer, convert_to_tensor=True)
        emb_expected = model.encode(expected, convert_to_tensor=True)

        cosine_sim = util.pytorch_cos_sim(emb_answer, emb_expected).item()

        data.append({
            "Question_ID": idx,
            "Question": question,
            "Expected Answer": expected,
            "Chatbot_Answer": answer,
            "Embedding_Answer": emb_answer,
            "Embedding_Expected": emb_expected,
            "Cosine_Similarity": cosine_sim,
            "Response_Time_s": response_time
        })

        if show_print:
            print(f"\n--- Q{idx} ---")
            print(f"Question: {question}")
            print(f"Answer: {answer}")
            print(f"Expected: {expected}")
            print(f"Cosine Similarity: {cosine_sim:.2f}, Time: {response_time:.2f}s")
            print('----------------------------------')

    return data

def evaluate_precomputed(data, model_name_str, thresholds=[0.5, 0.6, 0.7, 0.8, 0.9]):
    total = len(data)
    questions = [item["Question"] for item in data]

    all_results = {}
    total_time = sum(item["Response_Time_s"] for item in data)

    for threshold in thresholds:
        correct = 0
        results = []

        for item in data:
            match = "Yes" if item["Cosine_Similarity"] >= threshold else "No"
            if match == "Yes":
                correct += 1

            result_row = {
                "Question_ID": item["Question_ID"],
                "Question": item["Question"],
                "Expected Answer": item["Expected Answer"],
                "Chatbot_Answer": item["Chatbot_Answer"],
                "Cosine_Similarity": round(item["Cosine_Similarity"], 2),
                "Match": match,
                "Response_Time_s": round(item["Response_Time_s"], 2)
            }
            results.append(result_row)

        accuracy = (correct / total * 100) if total else 0
        avg_response = (total_time / total) if total else 0
        avg_similarity = sum(item['Cosine_Similarity'] for item in data) / total if total else 0

        summary = {
            "Total": total,
            "Correct": correct,
            "Accuracy": accuracy,
            "Average_Similarity": avg_similarity,
            "Average_Response_Time_s": avg_response,
            "Threshold": threshold,
            "Model": model_name_str
        }

        print(f"\n===== Summary at threshold {threshold} =====")
        print(f"Total: {total}, Correct: {correct}, Accuracy: {accuracy:.2f}%, Avg Response Time: {avg_response:.2f}s")

        all_results[threshold] = {
            "results": results,
            "summary": summary
        }

    # Save results
    save_results_seq(all_results, folder="evaluation", base_filename=f"{model_name_str}_eval_results_all_thresholds")

    return questions, all_results

def plot_evaluation_metrics(evaluations):
    """
    Plots accuracy (%) and median cosine similarity across thresholds.

    Parameters:
    - evaluations: dict
        Dictionary where keys are thresholds and values are dicts
        containing 'results' (list of dicts) and 'summary' (dict).
    """
    thresholds = sorted(evaluations.keys())
    accuracies = []
    median_sims = []

    for t in thresholds:
        results = evaluations[t]['results']
        sims = [r['Cosine_Similarity'] for r in results]
        median_sim = np.median(sims)
        median_sims.append(median_sim)

        accuracy = evaluations[t]['summary'].get('Accuracy')
        if accuracy is None:
            correct = sum(1 for r in results if r['Match'] == 'Yes')
            accuracy = 100 * correct / len(results) if results else 0
        accuracies.append(accuracy)

    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_xlabel('Threshold')
    ax1.set_ylabel('Accuracy (%)', color=color)
    ax1.plot(thresholds, accuracies, marker='o', color=color, label='Accuracy')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.set_ylim(0, 100)

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Median Cosine Similarity', color=color)
    ax2.plot(thresholds, median_sims, marker='x', linestyle='--', color=color, label='Median Similarity')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 1)

    plt.title('Threshold Tuning: Accuracy and Median Similarity')
    fig.tight_layout()
    plt.show()