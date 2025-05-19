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

user_id = st.session_state.get("username")

# Page routing logic
if st.session_state.selected_tab == "ChatFid":
    selected_convo_idx = 0
    if user_id:
        conversations = h.load_user_history(user_id)
        options = [c["title"] for c in conversations] if conversations else ["Nova Conversa"]
        selected_convo_idx = st.selectbox(
            "Escolha uma conversa:",
            options=range(len(options)),
            format_func=lambda i: options[i],
            index=0
        )
    else:
        selected_convo_idx = 0

    bot.assistant_chat(client, ASSISTANT_ID, user_id=user_id, selected_convo_idx=selected_convo_idx)
elif st.session_state.selected_tab == "Login":
    l.login()
