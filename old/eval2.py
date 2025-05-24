import os
from openai import AzureOpenAI
import bot  # Import your main bot logic

# Set up the evaluation assistant (replace with your eval assistant's info)
client = AzureOpenAI(
  azure_endpoint = "https://ai-bcds.openai.azure.com/",
  api_key= "8J6pTdfaGgA5r193UVLsBshUspqwNpal42Jse1aHaok1cWNTLpRkJQQJ99BDACYeBjFXJ3w3AAABACOGLa23",
  api_version="2024-05-01-preview"
)

eval_client = client.beta.assistants.create(
  model="gpt-4o-mini-BCwDS", 
  instructions="",
  tools=[{"type":"file_search"}],
  tool_resources={"file_search":{"vector_store_ids":["vs_ezpssNVZDpwb0RjgcxSwbNZz"]}},
  temperature=1,
  top_p=1
)

def evaluate_bot_response(user_input, bot_response):
    """
    Sends the user input and bot response to the evaluation assistant and gets a score or feedback.
    """
    # Compose the evaluation prompt
    eval_prompt = (
        "Avalie a seguinte resposta do assistente a uma pergunta de utilizador.\n\n"
        f"Pergunta do utilizador: {user_input}\n"
        f"Resposta do assistente: {bot_response}\n\n"
        "Dê uma avaliação objetiva da resposta, incluindo pontos fortes, pontos fracos e uma nota de 1 a 10."
    )

    # Create a thread and send the evaluation prompt
    thread = eval_client.beta.threads.create()
    eval_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=eval_prompt
    )

    # Run the evaluation assistant
    run = eval_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=eval_client.assistant_id  
    )

    # Wait for completion
    import time
    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = eval_client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Get the evaluation response
    if run.status == "completed":
        messages = eval_client.beta.threads.messages.list(thread_id=thread.id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                return msg.content[0].text.value.strip()
    return "[ERROR] No evaluation response"

# Example usage
if __name__ == "__main__":
    user_input = "Quais são as vantagens do produto My Savings?"
    bot_response = bot.get_assistant_response(
        client=bot.client,  # Or your main client
        assistant_id=bot.assistant_id,  # Or your main assistant id
        user_input=user_input
    )
    eval_feedback = evaluate_bot_response(user_input, bot_response)
    print("Bot response:", bot_response)
    print("Evaluation feedback:", eval_feedback)