import streamlit as st
import re
import time
from history import load_user_history, save_user_history, start_new_conversation, add_message
import os
import json


# Assistant Instructions
instructions = ("És o **ChatFid**, um assistente virtual especializado em apoio a agentes de vendas da Fidelidade. "
        "A tua função é prestar esclarecimentos exclusivamente sobre os produtos da Fidelidade My Savings e PPR Evoluir, "
        "com base integral e rigorosa na documentação oficial que te foi fornecida. "
        "\n\n"
        "Limites de atuação:\n"
        "- Responde sempre com base na documentação, e não halucines.\n"
        "Estilo e linguagem:\n"
        "- Responde SEMPRE na mesma lingua que a mensagem dada pelo utilizador. \n"
        "Por exemplo:\n"
        "- Se o utilizador escrever em inglês, responde em inglês.\n"
        "- Se o utilizador escrever em português, responde em português de Portugal.\n"
        "- Nunca mistures línguas na mesma resposta."
        "- Sê claro, objetivo e profissional, mas mantém um tom cordial e acessível.\n"
        "- Utiliza formatação Markdown quando for útil (ex: listas, negrito, subtítulos, tabelas).\n"
        "\n"
        "Âmbito de conhecimento:\n"
        "- Caso sejas questionado sobre outros temas, indica que a tua função se limita ao apoio sobre a Fidelidade e os seus produtos financeiros.\n"
        "\n"
        "Sempre que o utilizador disser algo como obrigado, obrigada, olá, bom dia, boa tarde ou expressar gratidão ou cumprimento, responde de forma educada e simpática."
        )

def assistant_chat(client, assistant_id, user_id=None, selected_convo_idx=0):
    
    if st.session_state.get("selected_tab") != "ChatFid":
        return

    st.title("Fidelidade AI Assistant")

    # Load all user conversations if user_id
    conversations = []
    if user_id:
        conversations = load_user_history(user_id)
    # Load messages for selected conversation
    if user_id and conversations:
        selected_convo = conversations[selected_convo_idx]
        st.session_state.messages = [
            {"role": m["role"], "content": m["message"]}
            for m in selected_convo["messages"]
        ]
    elif "messages" not in st.session_state:
        st.session_state.messages = []

    # Load messages for selected conversation
    if user_id and conversations:
        selected_convo = conversations[selected_convo_idx]
        st.session_state.messages = [
            {"role": m["role"], "content": m["message"]}
            for m in selected_convo["messages"]
        ]
    elif "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    user_input = st.chat_input("Escreva")

    if user_input:
        # Add user message to session and history
        st.session_state.messages.append({"role": "user", "content": user_input})
        if user_id:
            # Start new conversation if none exists
            if not conversations:
                start_new_conversation(user_id, "Nova Conversa")
                conversations = load_user_history(user_id)
                selected_convo_idx = 0
            add_message(user_id, "user", user_input)

        with st.chat_message("user"):
            st.write(user_input)

        # Create thread
        thread = client.beta.threads.create()

        # Add system prompt if needed
        system_prompt = instructions  
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=system_prompt + user_input
        )

        # Send user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Wait for completion
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        # Get the assistant's response
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            for msg in messages.data[::-1]:
                if msg.role == "assistant":
                    raw_response = msg.content[0].text.value
                    clean_response = re.sub(r"【\d+:\d+†source】", "", raw_response).strip()
                    st.session_state.messages.append({"role": "assistant", "content": clean_response})
                    if user_id:
                        add_message(user_id, "assistant", clean_response)
                    with st.chat_message("assistant"):
                        st.write(clean_response)
                    break
