# -*- coding: utf-8 -*-
"""chatbotRag.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1dPL5mJlNy5eu-3ZGOjfZ8x5qRsEVfCgH
"""

# Etapa 1: Instalação de dependências necessárias

def install_if_not_exist():
    import subprocess
    import sys

    required_packages = ["openai", "faiss-cpu", "sentence-transformers", "PyPDF2", "google-colab"]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Pacote {package} instalado.")

install_if_not_exist()

# Etapa 2: Importação de bibliotecas essenciais
import openai
import faiss
import numpy as np
import PyPDF2
from sentence_transformers import SentenceTransformer
from typing import List
from google.colab import files
import ipywidgets as widgets

# Etapa 3: Configuração da API do ChatGPT
from openai import OpenAI
openai.api_key = "API_KEY"
client = OpenAI(api_key=openai.api_key)

# Etapa 4: Carregamento do modelo de embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Etapa 5: Definição dos documentos de exemplo
print("Faça o upload do seu currículo em PDF:")
uploaded_file = files.upload()
pdf_filename = next(iter(uploaded_file.keys()))

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

curriculum_text = extract_text_from_pdf(pdf_filename)

documents = [curriculum_text]

# Etapa 6: Criação dos embeddings dos documentos
document_embeddings = np.array(embedding_model.encode(documents), dtype=np.float32)
document_embeddings = np.ascontiguousarray(document_embeddings)

# Etapa 7: Construção do índice FAISS
d = document_embeddings.shape[1]
index = faiss.IndexFlatL2(d)
index.add(document_embeddings)

# Etapa 8: Função para recuperação de documentos relevantes
def retrieve_documents(query: str, top_k: int = 2) -> List[str]:
    query_embedding = np.array(embedding_model.encode([query]), dtype=np.float32)
    query_embedding = np.ascontiguousarray(query_embedding)
    distances, indices = index.search(query_embedding, top_k)
    return [documents[i] for i in indices[0]]

# Etapa 9: Função para geração de resposta com ChatGPT
def generate_response(query: str):
    retrieved_docs = retrieve_documents(query)
    context = "\n".join(retrieved_docs)

    # Limitar o contexto para evitar estouro de tokens
    max_context_length = 4000
    if len(context) > max_context_length:
        context = context[:max_context_length] + "..."

    prompt = f"""
    Contexto:
    {context}

    Pergunta: {query}
    Responda baseado no contexto acima.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        print(f"Erro na API da OpenAI: {e}")
        return "Erro ao processar a solicitação."

# Etapa 10: Teste do chatbot
input_box = widgets.Text(
    placeholder='Digite sua pergunta...',
    description='Pergunta:',
    layout=widgets.Layout(width='100%')
)

send_button = widgets.Button(description="Enviar")
output_box = widgets.Output()

# Função para processar a entrada do usuário
def on_submit(change):
    with output_box:
        output_box.clear_output()
        response = generate_response(input_box.value)
        print("Resposta do Chatbot:", response)

send_button.on_click(lambda _: on_submit(None))
input_box.on_submit(on_submit)

display(input_box, send_button, output_box)