import requests
import api
import langdetect

# Path for FAISS database
DB_FAISS_PATH = 'vectorstore/db_faiss'

# Replace with actual values
# These values should be set in .env location for safety reasons
api_key = api.local_settings.API_KEY
endpoint = api.local_settings.endpoint


def llama_completion(prompt, max_tokens=1024):
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
    return response.json()

def detect_language(text):
    """Detect the language of the input text."""
    try:
        return langdetect.detect(text)
    except:
        return 'en' 
    
def build_prompt(history, user_input):
    """Build the prompt including language-based instructions."""
    detected_lang = detect_language(user_input)
    
    # System prompt in English, but you can adjust for other languages
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
    
    # Load vector store
    vectorstore = load_vectorstore()
    relevant_docs = vectorstore.similarity_search(user_input, k=3)
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    # Ensure we are always returning a valid string
    #prompt = system_prompt + "\n"
    #for msg in history:
        #prompt += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"

    #return prompt if prompt else ""

    # Build prompt
    prompt = system_prompt + "\n"
    prompt += f"\nContext from documents:\n{context}\n"
    for msg in history:
        prompt += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"
    
    return prompt
    
import os
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader  # Or use pdfplumber
import pickle

PDF_DIR = "docs/Documents for training and evaluation-20250507/PPR Evoluir_Documents/PPR Evoluir - Public"

def load_pdfs_from_directory(directory):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            path = os.path.join(directory, filename)
            text = extract_text_from_pdf(path)
            documents.append(Document(page_content=text, metadata={"source": filename}))
    return documents

def extract_text_from_pdf(filepath):
    reader = PdfReader(filepath)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    return full_text

def create_vectorstore_from_pdfs():
    docs = load_pdfs_from_directory(PDF_DIR)
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(DB_FAISS_PATH)


def load_vectorstore():
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return FAISS.load_local(DB_FAISS_PATH, embeddings)
