import streamlit as st
import requests
import api
import time
import langdetect

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
    
    # Ensure we are always returning a valid string
    prompt = system_prompt + "\n"
    for msg in history:
        prompt += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"

    return prompt if prompt else ""
    

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
