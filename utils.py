# [i]                                                                                            #
# [i] Libraries                                                                                   #
# [i]  

import api
import langdetect
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz

# Path for FAISS database
DB_FAISS_PATH = 'vectorstore/db_faiss'

# These values should be set in .env location for safety reasons
api_key = api.local_settings.API_KEY
endpoint = api.local_settings.endpoint


"""def llama_completion(prompt, max_tokens=1024):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "Gemma3:12b",
        "prompt": prompt,
        "max_tokens": max_tokens
    }
    response = requests.post(endpoint, headers=headers, json=data)
    return response.json()"""

from openai import AzureOpenAI

# Azure OpenAI client setup
client = AzureOpenAI(
    api_key=api.local_settings.API_KEY,
    api_version="2024-02-01",
    azure_endpoint=api.local_settings.endpoint 
)

def llama_completion(user_input, history=None, top_k=5):
    """Calls Azure OpenAI with retrieved context and chat history."""
    # Detect language
    detected_lang = detect_language(user_input)

    system_prompt = (
        "És o **Gemma3**, um assistente financeiro amigável e conciso. "
        "Responde em português, se o utilizador escrever em português. "
        "Se o utilizador escrever em inglês, responde em inglês, e assim por diante. "
        "Utiliza sempre markdown quando necessário."
        if detected_lang == 'pt' else
        "You are **Gemma3**, a friendly and concise financial assistant. "
        "Respond in the same language as the user writes in. "
        "Always use markdown when appropriate."
    )

    # Get vector DB context
    context = retrieve_relevant_context(user_input, top_k=top_k)

    # Build full conversation context
    message_history = [{"role": "system", "content": system_prompt}]
    
    if history:
        for msg in history:
            message_history.append({"role": "user", "content": msg['user']})
            message_history.append({"role": "assistant", "content": msg['bot']})
    
    # Latest question with context
    message_history.append({
        "role": "user",
        "content": (
            f"Use the following information to answer the user's question.\n\n"
            f"Context:\n{context}\n\n"
            f"User question: {user_input}"
        )
    })

    # Call model
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=message_history,
        max_tokens=512,
        temperature=0.2
    )
    return response.choices[0].message.content

def detect_language(text):
    """Detect the language of the input text."""
    try:
        return langdetect.detect(text)
    except:
        return 'en' 

"""def build_prompt(history, user_input):
    """"Build the full prompt with history and relevant PDF context.""""
    detected_lang = detect_language(user_input)

    if detected_lang == 'pt':
        system_prompt = (
            "És o **Gemma3**, um assistente financeiro amigável e conciso. "
            "Responde em português, se o utilizador escrever em português. "
            "Se o utilizador escrever em inglês, responde em inglês, e assim por diante. "
            "Utiliza sempre markdown quando necessário."
        )
    else:
        system_prompt = (
            "You are **Gemma3**, a friendly and concise financial assistant. "
            "Respond in the same language as the user writes in. "
            "Always use markdown when appropriate."
        )

    # Load vectorstore and search for relevant context
    vectorstore = load_vectorstore()
    relevant_docs = vectorstore.similarity_search(user_input, k=3)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    prompt = system_prompt + "\n\n"
    prompt += f"Context:\n{context}\n\n"

    for msg in history:
        prompt += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"
    
    return prompt"""


PDF_DIR = "docs/Documents for training and evaluation-20250507/PPR Evoluir_Documents/PPR Evoluir - Public Information"

def load_pdfs_from_directory(directory):
    documents = {}
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            path = os.path.join(directory, filename)
            text = extract_text_from_pdf(path)
            documents[filename] = text
    return documents

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)

def chunk_texts(file_texts, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    file_chunks = {}
    for fname, text in file_texts.items():
        docs = splitter.create_documents([text])
        file_chunks[fname] = [chunk.page_content for chunk in docs]
    return file_chunks

def create_vectorstore_from_pdfs():
    docs = load_pdfs_from_directory(PDF_DIR)
    print(f"Loaded {len(docs)} documents.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    
    # Wrap docs into Document objects
    all_docs = []
    for fname, text in docs.items():
        doc_objs = splitter.create_documents([text])
        for d in doc_objs:
            d.metadata = {"source": fname}
        all_docs.extend(doc_objs)

    print(f"Split into {len(all_docs)} chunks.")
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    vectorstore = FAISS.from_documents(all_docs, embeddings)
    
    print(f"Saving FAISS index to {DB_FAISS_PATH}")
    vectorstore.save_local(DB_FAISS_PATH)

def retrieve_relevant_context(user_input, top_k=5):
    vectorstore = load_vectorstore()
    relevant_docs = vectorstore.similarity_search(user_input, k=top_k)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    return context

def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)

