import streamlit as st
from streamlit_option_menu import option_menu
import os
import time
from openai import AzureOpenAI
import re

import login as l
import bot
import history as h


# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint="https://ai-bcds.openai.azure.com/",
    api_key="8J6pTdfaGgA5r193UVLsBshUspqwNpal42Jse1aHaok1cWNTLpRkJQQJ99BDACYeBjFXJ3w3AAABACOGLa23",
    api_version="2024-05-01-preview"
)

# Assistant ID
ASSISTANT_ID = "asst_yo99aUtzwlgezxRgDNgRon7b"

# Set page configuration
st.set_page_config(page_title="Fidelidade AI Assistant", layout="wide")

# Initialize session state
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "ChatFid"

# Show option menu and capture user selection
selected = option_menu(
    menu_title=None,
    options=["ChatFid", "Login"],
    icons=["robot", "person"],
    orientation="horizontal",
    default_index=["ChatFid", "Login"].index(st.session_state.selected_tab)
)



# If the selection changed, update session state and rerun the app
if selected != st.session_state.selected_tab:
    st.session_state.selected_tab = selected
    st.rerun()

# Define the user ID
user_id = st.session_state.get("username")

# Page routing logic
if st.session_state.selected_tab == "ChatFid":
    if "selected_convo_idx" not in st.session_state:
        st.session_state.selected_convo_idx = 0

    # Load the selected conversation index from session state
    selected_convo_idx = st.session_state.selected_convo_idx

    # Only shows the conversation selection if the user is logged in
    if user_id:
        conversations = h.load_user_history(user_id)
        options = [c["title"] for c in conversations] if conversations else []
        options = ["Nova Conversa"] + options


        # Add a new conversation option
        selected_option = st.selectbox(
            "Escolha uma conversa:",
            options=range(len(options)),
            format_func=lambda i: options[i],
            index=st.session_state.selected_convo_idx
        )

        if selected_option == 0:
            # Only create a new conversation if not just created
            if st.session_state.selected_convo_idx == 0 and conversations and conversations[-1]["messages"] == []:
                pass
            else:
                h.start_new_conversation(user_id, f"Conversa {len(conversations)+1}")
                conversations = h.load_user_history(user_id)
                st.session_state.selected_convo_idx = len(conversations)
                st.rerun()
        else:
            st.session_state.selected_convo_idx = selected_option
            selected_convo_idx = selected_option

            # Conversation Rename Logic
            current_title = conversations[selected_convo_idx - 1]["title"]
            new_title = st.text_input(
                "Renomear conversa:",
                value=current_title,
                key=f"rename_convo_{selected_convo_idx}"
            )
            if new_title != current_title and new_title.strip():
                conversations[selected_convo_idx - 1]["title"] = new_title.strip()
                h.save_user_history(user_id, conversations)
                st.rerun()

            # Conversation Delete Logic
            if st.button("Apagar esta conversa", key=f"delete_convo_{selected_convo_idx}"):
                del conversations[selected_convo_idx - 1]
                h.save_user_history(user_id, conversations)
                st.session_state.selected_convo_idx = 0
                st.rerun()
    else:
        selected_convo_idx = 0

    # Display the chat interface
    bot.assistant_chat(client, ASSISTANT_ID, user_id=user_id, selected_convo_idx=selected_convo_idx-1 if selected_convo_idx > 0 else 0)

# Login page    
elif st.session_state.selected_tab == "Login":
    l.login()