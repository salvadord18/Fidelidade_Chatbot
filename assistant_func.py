import streamlit as st
import json
import os


USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def login():
    st.subheader("Login or Create Account")

    users = load_users()

    mode = st.radio("Escolha uma opção:", ["Login", "Criar Conta"])

    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_btn = st.form_submit_button("Confirmar")

        if submit_btn:
            if mode == "Login":
                if username in users and users[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success(f"Login realizado com sucesso! Bem-vindo(a), {username}.")
                else:
                    st.error("Credenciais inválidas")
            elif mode == "Criar Conta":
                if username in users:
                    st.error("Utilizador já existe. Escolha outro username.")
                elif not username or not password:
                    st.error("Username e Password não podem estar vazios.")
                else:
                    users[username] = password
                    save_users(users)
                    st.success(f"Conta criada com sucesso para {username}. Agora pode fazer login.")





# Assistant Instructions
system_prompt = ("És o **ChatFid**, um assistente virtual especializado em apoio a agentes de vendas da Fidelidade. "
        "A tua função é prestar esclarecimentos exclusivamente sobre os produtos da Fidelidade My Savings e PPR Evoluir, "
        "com base integral e rigorosa na documentação oficial que te foi fornecida. "
        "\n\n"
        "Limites de atuação:\n"
        "- Responde sempre com base na documentação, e não halucines.\n"
        "Estilo e linguagem:\n"
        "- Responde SEMPRE na mesma lingua que o utilizador. Caso o utilizador escreva em português, responde em português de Portugal.\n"
        "- Sê claro, objetivo e profissional, mas mantém um tom cordial e acessível.\n"
        "- Utiliza formatação Markdown quando for útil (ex: listas, negrito, subtítulos, tabelas).\n"
        "\n"
        "Âmbito de conhecimento:\n"
        "- Caso sejas questionado sobre outros temas, indica que a tua função se limita ao apoio sobre a Fidelidade e os seus produtos financeiros.\n"
        "\n"
        "Sempre que o utilizador disser algo como obrigado, obrigada, olá, bom dia, boa tarde ou expressar gratidão ou cumprimento, responde de forma educada e simpática."
        )