# [i]                                                                                            #
# [i] Libraries                                                                                   #
# [i]                                                                                            #

import streamlit as st
import time
from utils import *

# [i]                                                                                            #
# [i] CHATBOT                                                                                   #
# [i]   

st.title("ChatFid")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display intro message if no messages have been exchanged yet
if not st.session_state.chat_history:
    with st.chat_message("assistant"):
        st.markdown(
            "Olá! 👋 Eu sou o **Gemma3**, um assistente financeiro. Como posso ajudar você hoje? "
            "Pergunte-me sobre investimentos, orçamentos ou qualquer outra coisa que precise!"
        )

# Display chat messages

for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(chat["user"])
    with st.chat_message("assistant"):
        st.markdown(chat["bot"])

# User input
user_input = st.chat_input("Escreve algo...")

if user_input:
    st.chat_message("user").markdown(user_input)

    try:
        # Use the single clean function that retrieves context, builds prompt, and calls the model
        bot_reply = llama_completion(user_input, history=st.session_state.chat_history)
    except Exception as e:
        bot_reply = f"Erro: {e}"

    response_placeholder = st.chat_message("assistant").empty()

    streamed_output = ""
    for word in bot_reply.split():
        streamed_output += word + " "
        response_placeholder.markdown(streamed_output)
        time.sleep(0.05)

    st.session_state.chat_history.append({
        "user": user_input,
        "bot": bot_reply
    })