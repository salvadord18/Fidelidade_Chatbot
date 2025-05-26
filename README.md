# Fidelidade Chatbot

A Streamlit-based assistant for supporting Fidelidade sales agents, with login and conversation history features.

---

## Features

- **FIDCHAT**: Virtual assistant specialized in Fidelidade products (My Savings, PPR Evoluir) and financial literacy.
- **User Authentication**: Login and account creation with credential storage.
- **Conversation History**: Stores and manages multiple conversations per user, with options to rename or delete.
- **Evaluation Tools**: Scripts and utilities to evaluate chatbot answers using both string similarity and a dedicated evaluation assistant.

---

## Main Files

- `app.py`  
  Main Streamlit app. Handles authentication, chat UI, conversation management, and routing.

- `bot.py`  
  Implements the assistant chat logic, including message handling and history integration.

- `login.py`  
  User login and account creation logic.

- `history.py`  
  Utilities for saving, loading, and managing user conversation histories.

- `eval_utils.py`  
  Tools for evaluating chatbot answers, including:

- `users.json`  
  Stores user credentials.

- `conversations/`  
  Stores per-user conversation histories as JSON files.

---

This Project was developed by
- Ana Farinha 20211514
- António Oliveira 20211595
- Mariana Neto 20211527
- Salvador Domingues 20240597