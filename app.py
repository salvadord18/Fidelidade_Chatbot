import streamlit as st
from streamlit_option_menu import option_menu
import os
import time
from openai import AzureOpenAI
import re

import login as l
import bot as bot


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

# Initialize menu selection in session state
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "ChatFid"

selected = option_menu(
    menu_title=None,
    options=["ChatFid", "Login"],
    icons=["robot", "person"],
    orientation="horizontal",
    default_index=0
)

st.session_state.selected_tab = selected

# Page routing logic
if st.session_state.selected_tab == "ChatFid":
    #st.title("Fidelidade AI Assistant")
    bot.assistant_chat(client, ASSISTANT_ID)
elif st.session_state.selected_tab == "Login":
    l.login()