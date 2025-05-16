import os
import time
import json
import requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

# Initialize Azure OpenAI client with entra-id authentication
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(),
    "https://cognitiveservices.azure.com/.default"
)
client = AzureOpenAI(
    azure_ad_token_provider=token_provider,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-05-01-preview"
)

assistant = client.beta.assistants.create(
    model="gpt-4o-mini",  # replace with model deployment name
    name="Assistant46",
    instructions="Tu és um perito que trabalha na Fidelidade em investimentos a prazo. Toda a informação que dás é com base nos ficheiros disponibilizados.",
    tools=[{"type":"file_search"}]
    ,tool_resources={"file_search":{"vector_store_ids":["vs_ftCso8RzHlBSbUwcqVWP3RiG"]},"code_interpreter":{"file_ids":["assistant-WuJZaGApRBgPZGvfPJwTBF","assistant-WQbe2oYNiunshZFamDkAMe","assistant-WA9mo2ooGuCakdtLYe7S5Y","assistant-VmGKDJtKWW8mLr7RsNDHJ4","assistant-VcoN7vmxYPZCBfSTaFsEQ3","assistant-TaHujXgSvATXXH1V5gBTDN","assistant-NMXvUzELtRbwtQMoTXeApo","assistant-LvBZjKCKvtwUvCCTgpfWim","assistant-GWrPgzCPp8si1AH2yKKJBB","assistant-F5nrFbNEjGxEqeSCmkdLAg","assistant-EwB2EpAtrmQVUrtxvg79HB","assistant-BFYazbjKgte4W5u9Jgrs6b","assistant-96mBrzvMJbaTjLYcCEG3S2","assistant-8phYrqvFLjksiThSKqSgkq","assistant-7GHqFyWe29skpMH8Ug4QoZ","assistant-6zJbn35vHos3RRzqJUiVMQ","assistant-5dMu4U3q2VUkjhP4LvhAGb","assistant-4hduKqwh6y7AWcUohbxMC3","assistant-426n1B453C2wqH2AnDc2mh","assistant-3UFjejDd1iMmYhBuj2bgi8"]}},
    temperature=0.44,
    top_p=1
)

print(f"Assistant created: {json.dumps(assistant)}")