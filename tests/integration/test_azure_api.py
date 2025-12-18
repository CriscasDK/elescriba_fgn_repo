#!/usr/bin/env python3
"""Test simple de Azure OpenAI API"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env.gpt41'
load_dotenv(env_path)

print("="*60)
print("TEST AZURE OPENAI API")
print("="*60)

# Configurar cliente
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")

print(f"\n✅ Cliente configurado:")
print(f"   Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"   Deployment: {deployment}")

# Test simple
print(f"\n📝 Enviando mensaje de prueba...")

try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Eres un asistente. Responde en formato JSON."},
            {"role": "user", "content": 'Responde con este JSON: {"test": "ok", "numero": 123}'}
        ],
        temperature=0.1,
        max_tokens=100
    )

    result_text = response.choices[0].message.content
    print(f"\n✅ Respuesta recibida ({len(result_text)} caracteres):")
    print(f"   {result_text}")

    print(f"\n✅ Tokens usados: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
