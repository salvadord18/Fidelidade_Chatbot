import streamlit as st
from streamlit_option_menu import option_menu
import os
import time
from openai import AzureOpenAI
import re

import assistant_func as af


# Initialize Azure OpenAI client
client = AzureOpenAI(
  azure_endpoint = "https://ai-bcds.openai.azure.com/",
  api_key= "8J6pTdfaGgA5r193UVLsBshUspqwNpal42Jse1aHaok1cWNTLpRkJQQJ99BDACYeBjFXJ3w3AAABACOGLa23",
  api_version="2024-05-01-preview"
)

# Assistant ID
ASSISTANT_ID = "asst_yo99aUtzwlgezxRgDNgRon7b"


# Set page configuration
st.set_page_config(page_title="Fidelidade AI Assistant", layout="wide")

################################################################################################

def assistant_chat():

    st.title("Fidelidade AI Assistant")
    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    user_input = st.chat_input("Faça uma pergunta sobre os produtos Fidelidade")

    if user_input:
        # Add user message locally first for instant UI update
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Create thread
        thread = client.beta.threads.create()

        # Send system message to set assistant behavior
        system_prompt = af.system_prompt
        
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
            assistant_id=ASSISTANT_ID
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



# Initialize session state for the menu option if not present
if "menu_option" not in st.session_state:
    st.session_state.menu_option = "ChatFid"

choice = option_menu(
    menu_title=None,
    options=["ChatFid", "Login"],
    icons=["robot", "person"],
    orientation="horizontal",
    default_index=["ChatFid", "Login"].index(st.session_state.menu_option),
    key="menu_option"
)

# Use the synced session state variable directly
choice = st.session_state.menu_option

if choice == "ChatFid":
    assistant_chat()
elif choice == "Login":
    af.login()

