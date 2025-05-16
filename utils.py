# [i]                                                                                            #
# [i] Libraries                                                                                   #
# [i]  

import api
import langdetect
import os
from openai import AzureOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz

# Path for FAISS database
DB_FAISS_PATH = 'vectorstore/db_faiss'

# Path for PDF documents
PDF_DIR = "docs/Documents for training and evaluation-20250507/PPR Evoluir_Documents/PPR Evoluir - Public Information"

# These values should be set in .env location for safety reasons
api_key = api.local_settings.API_KEY
endpoint = api.local_settings.endpoint

# [i]                                                                                            #
# [i] Bot functions                                                                          #
# [i]  

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
        "És o **ChatFid**, um assistente virtual especializado em apoio a agentes da Fidelidade. "
        "A tua função é prestar esclarecimentos exclusivamente sobre o produto PPR Evoluir, "
        "com base integral e rigorosa na documentação oficial que te foi fornecida. "
        "\n\n"
        "Limites de atuação:\n"
        "- Nunca deves inventar, extrapolar ou assumir qualquer informação que não esteja clara na documentação.\n"
        "- Se a resposta à pergunta do utilizador não estiver presente nos documentos fornecidos, responde de forma clara e transparente, com algo como:\n"
        "  - \"Desculpa, mas não disponho de dados suficientes para responder.\"\n"
        "\n"
        "Estilo e linguagem:\n"
        "- Responde sempre em **português de Portugal**.\n"
        "- Sê claro, objetivo e profissional, mas mantém um tom cordial e acessível.\n"
        "- Utiliza formatação Markdown quando for útil (ex: listas, negrito, subtítulos, tabelas).\n"
        "\n"
        "Âmbito de conhecimento:\n"
        "- Responde apenas a perguntas relacionadas com o **PPR Evoluir**.\n"
        "- Caso sejas questionado sobre outros produtos ou temas fora do PPR Evoluir, indica que a tua função se limita ao apoio sobre este produto (apenas se não tiver descrito nos documentos fornecidos).\n"
        "\n"
        "Sempre que o utilizador disser algo como obrigado, obrigada, olá, bom dia, boa tarde ou expressar gratidão ou cumprimento, responde de forma educada e simpática."
        if detected_lang == 'pt' else
        "You are **ChatFid**, a virtual assistant for Fidelidade agents. "
        "Your role is to provide answers exclusively about the **PPR Evoluir** product, based strictly on the official documentation provided. "
        "Do not invent or assume anything not found in the documentation. "
        "If the answer is not present, respond clearly with something like: "
        "\"Sorry, I do not have enough information to answer that.\" "
        "Use Markdown when helpful, keep your tone clear, professional and friendly."
        "PLEASE ANSWER IN THE SAME LANGUAGE AS THE USER."
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

