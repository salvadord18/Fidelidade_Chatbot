import streamlit as st
import re
import time


# Assistant Instructions
instructions = ("És o **ChatFid**, um assistente virtual especializado em apoio a agentes de vendas da Fidelidade. "
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

def assistant_chat(client, assistant_id):

    if st.session_state.get("selected_tab") != "ChatFid":
        return

    st.title("Fidelidade AI Assistant")
    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    user_input = st.chat_input("Escreva")

    if user_input:
        # Add user message locally first for instant UI update
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Create thread
        thread = client.beta.threads.create()

        # Send system message to set assistant behavior
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

        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            for msg in messages.data[::-1]:
                if msg.role == "assistant":
                    raw_response = msg.content[0].text.value
                    clean_response = re.sub(r"【\d+:\d+†source】", "", raw_response).strip()
                    st.session_state.messages.append({"role": "assistant", "content": clean_response})
                    with st.chat_message("assistant"):
                        st.write(clean_response)
                    break
