#!/usr/bin/env python3
"""
Test específico para la extracción de nombres en consultas complejas
"""

import re

def test_name_extraction():
    texto = "oswaldo olivo y su relación con rosa edith sierra"

    print("🧪 TEST EXTRACCIÓN DE NOMBRES")
    print("=" * 50)
    print(f"Texto: '{texto}'")

    # Test diferentes patrones de regex
    patrones = [
        r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+\b',  # Actual
        r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b',  # Alternativo 1
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Sin acentos
        r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*'  # Más flexible
    ]

    for i, patron in enumerate(patrones, 1):
        print(f"\n{i}️⃣ Patrón: {patron}")
        matches = re.findall(patron, texto)
        print(f"   Resultado: {matches}")

    # Test con texto en mayúsculas
    texto_caps = "Oswaldo Olivo y su relación con Rosa Edith Sierra"
    print(f"\n📝 Con mayúsculas: '{texto_caps}'")

    for i, patron in enumerate(patrones, 1):
        print(f"\n{i}️⃣ Patrón: {patron}")
        matches = re.findall(patron, texto_caps)
        print(f"   Resultado: {matches}")

if __name__ == "__main__":
    test_name_extraction()