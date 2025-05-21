import fitz 
from langchain.text_splitter import RecursiveCharacterTextSplitter


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_text(extracted_text)

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks)

import faiss
import numpy as np

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(np.array(embeddings))

query = "What is the main point of the document?"
query_embedding = model.encode([query])

D, I = index.search(np.array(query_embedding), k=5)
retrieved_chunks = [chunks[i] for i in I[0]]
