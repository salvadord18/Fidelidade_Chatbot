import streamlit as st
import requests
import api
import time

# Replace with your actual values
api_key = api.api_key1
endpoint = api.endpoint

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

def build_prompt(history):
    """Convert history list to a full prompt."""
    prompt = ""
    for msg in history:
        prompt += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"
    return prompt


# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat messages
st.title("💬 Fala com Gemma3")
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
    full_prompt = build_prompt(temp_history[:-1]) + f"User: {user_input}\nAssistant:"

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
