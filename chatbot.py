# [i]                                                                                            #
# [i] Libraries                                                                                   #
# [i]                                                                                            #

import streamlit as st
import time
from utils import *



## CHATBOT
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

    # Add current user input to a temporary history
    temp_history = st.session_state.chat_history + [{"user": user_input, "bot": ""}]
    
    # Pass user_input to build_prompt function
    full_prompt = build_prompt(temp_history[:-1], user_input) + f"User: {user_input}\nAssistant:"

    response_placeholder = st.chat_message("assistant").empty()


    # Call model with the full prompt
    try:
        response = llama_completion(full_prompt)
        bot_reply = response["choices"][0]["text"]
    except Exception as e:
        bot_reply = f"Erro: {e}"

    streamed_output = ""
    for word in bot_reply.split():
        streamed_output += word + " "
        response_placeholder.markdown(streamed_output)
        time.sleep(0.05)  # adjust for speed


    # Save the new message pair
    st.session_state.chat_history.append({
        "user": user_input,
        "bot": bot_reply
    })
