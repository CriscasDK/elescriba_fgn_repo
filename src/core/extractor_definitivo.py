#!/usr/bin/env python3
"""
EXTRACTOR DEFINITIVO - Procesamiento masivo automático
"""

import json
import ollama
import psycopg2
import os
import re
import glob
import time

# Configuración de BD
DB_CONFIG = {
    'host': 'localhost',
    'database': 'documentos_juridicos',
    'user': 'docs_user',
    'password': 'docs_password_2025',
    'port': 5432
}

def fix_encoding(text):
    """Corregir encoding de caracteres especiales"""
    if not text:
        return text
    
    fixed_text = str(text)
    fixed_text = fixed_text.replace('Ã¡', 'á')
    fixed_text = fixed_text.replace('Ã©', 'é')
    fixed_text = fixed_text.replace('Ã­', 'í')
    fixed_text = fixed_text.replace('Ã³', 'ó')
    fixed_text = fixed_text.replace('Ãº', 'ú')
    fixed_text = fixed_text.replace('Ã±', 'ñ')
    fixed_text = fixed_text.replace('Ã�a', 'ía')
    fixed_text = fixed_text.replace('Ã�', 'í')
    
    return fixed_text.strip()

def insert_documento_completo(json_data):
    """Insertar documento con todos los metadatos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute("SELECT id FROM documentos WHERE archivo = %s", (json_data.get('archivo'),))
        if cursor.fetchone():
            conn.close()
            return -1  # Ya existe
        
        # Insertar documento principal
        cursor.execute("""
            INSERT INTO documentos (
                archivo, estado, paginas, tamaño_mb, texto_extraido, analisis
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            json_data.get('archivo'),
            json_data.get('estado'),
            json_data.get('paginas'),
            json_data.get('tamaño_mb'),
            json_data.get('texto_extraido'),
            json_data.get('analisis')
        ))
        
        doc_id = cursor.fetchone()[0]
        
        # Insertar metadatos
        metadatos = json_data.get('metadatos', {})
        if metadatos:
            cursor.execute("""
                INSERT INTO metadatos (
                    documento_id, nuc, cuaderno, codigo, despacho, detalle,
                    entidad_productora, serie, subserie, folio_inicial, folio_final,
                    hash_sha256, producer, equipo_id_auth
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                doc_id,
                fix_encoding(metadatos.get('NUC')),
                fix_encoding(metadatos.get('Cuaderno')),
                fix_encoding(metadatos.get('Código')),
                fix_encoding(metadatos.get('Despacho')),
                fix_encoding(metadatos.get('Detalle')),
                fix_encoding(metadatos.get('Entidad productora')),
                fix_encoding(metadatos.get('Serie')),
                fix_encoding(metadatos.get('Subserie')),
                metadatos.get('Folio Inicial'),
                metadatos.get('Folio Final'),
                metadatos.get('Hash_SHA256'),
                metadatos.get('Producer'),
                metadatos.get('Equipo_ID')
            ))
        
        # Insertar estadísticas
        estadisticas = json_data.get('estadisticas', {})
        if estadisticas:
            cursor.execute("""
                INSERT INTO estadisticas (
                    documento_id, normal, ilegible, posiblemente,
                    total_palabras, porcentaje_inferencias
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                doc_id,
                estadisticas.get('normal'),
                estadisticas.get('ilegible'),
                estadisticas.get('posiblemente'),
                estadisticas.get('total_palabras'),
                estadisticas.get('porcentaje_inferencias')
            ))
        
        conn.commit()
        conn.close()
        return doc_id
        
    except Exception as e:
        print(f"❌ Error insertando: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return None

def extract_personas_llm(text, modelo):
    """Extraer personas usando LLM"""
    try:
        prompt = f"""
Extrae nombres de personas del texto judicial:

{{
    "victimarios": [{{"nombre": "Juan Prada", "cedula": "123", "alias": "Juancho"}}],
    "funcionarios": [{{"nombre": "Fiscal", "cedula": "", "alias": ""}}],
    "victimas": [{{"nombre": "Víctima", "cedula": "", "alias": ""}}],
    "otros": [{{"nombre": "Otro", "cedula": "", "alias": ""}}]
}}

Texto: {text[:1500]}
"""
        
        response = ollama.chat(model=modelo, messages=[{'role': 'user', 'content': prompt}])
        
        json_match = re.search(r'\{.*\}', response['message']['content'], re.DOTALL)
        if json_match:
            json_str = json_match.group()
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            return json.loads(json_str)
        
    except Exception as e:
        print(f"⚠️ Error personas: {e}")
    return None

def extract_organizaciones_llm(text, modelo):
    """Extraer organizaciones usando LLM"""
    try:
        prompt = f"""
Extrae organizaciones del texto:

{{
    "legal": ["Fiscalía General"],
    "ilegal": ["AUSAC"],
    "otra": ["Otra"]
}}

Texto: {text[:1500]}
"""
        
        response = ollama.chat(model=modelo, messages=[{'role': 'user', 'content': prompt}])
        
        json_match = re.search(r'\{.*\}', response['message']['content'], re.DOTALL)
        if json_match:
            json_str = json_match.group()
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            return json.loads(json_str)
        
    except Exception as e:
        print(f"⚠️ Error orgs: {e}")
    return None

def parse_markdown_section(text, section_pattern):
    """Buscar sección específica"""
    lines = text.split('\n')
    content = ""
    in_section = False
    
    for line in lines:
        if re.search(section_pattern, line, re.IGNORECASE):
            in_section = True
            continue
        elif in_section and (line.startswith("### ") or line.startswith("## ")):
            break
        elif in_section:
            content += line + "\n"
    
    return content.strip() if content else None

def insert_extracted_data(doc_id, personas_data, org_data):
    """Insertar datos extraídos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        total_personas = 0
        total_orgs = 0
        
        if personas_data:
            for tipo, personas in personas_data.items():
                for persona in personas:
                    if isinstance(persona, dict) and persona.get('nombre'):
                        cursor.execute("""
                            INSERT INTO personas (documento_id, nombre, tipo_persona, cedula, alias)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            doc_id, persona['nombre'].strip(), tipo,
                            persona.get('cedula', '').strip() or None,
                            persona.get('alias', '').strip() or None
                        ))
                        total_personas += 1
        
        if org_data:
            for tipo, orgs in org_data.items():
                for org in orgs:
                    if org and len(str(org).strip()) > 2:
                        cursor.execute("""
                            INSERT INTO organizaciones (documento_id, nombre, tipo)
                            VALUES (%s, %s, %s)
                        """, (doc_id, str(org).strip(), tipo))
                        total_orgs += 1
        
        conn.commit()
        conn.close()
        return total_personas, total_orgs
        
    except Exception as e:
        print(f"❌ Error insertando extraídos: {e}")
        return 0, 0

def process_single_json(json_file_path, modelo):
    """Procesar un archivo JSON"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        archivo = json_data.get('archivo', 'N/A')
        
        # Insertar documento
        doc_id = insert_documento_completo(json_data)
        if doc_id == -1:
            return "existe"
        elif doc_id is None:
            return "error"
        
        # Extraer con LLM
        analisis_text = json_data.get('analisis', '')
        if analisis_text:
            personas_section = parse_markdown_section(analisis_text, "A. PERSONAS")
            personas_data = extract_personas_llm(personas_section, modelo) if personas_section else None
            
            org_section = parse_markdown_section(analisis_text, "B. ORGANIZACIONES")
            org_data = extract_organizaciones_llm(org_section, modelo) if org_section else None
            
            if personas_data or org_data:
                insert_extracted_data(doc_id, personas_data, org_data)
        
        return "exitoso"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return "error"

def main():
    """Procesamiento masivo automático"""
    
    print("🚀 PROCESAMIENTO MASIVO AUTOMÁTICO")
    print("="*60)
    
    try:
        # Configurar
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("✅ PostgreSQL OK")
        
        models_response = ollama.list()
        modelo = [model.model for model in models_response.models if 'deepseek' in model.model.lower()][0]
        print(f"✅ Modelo: {modelo}")
        
        json_files = glob.glob('./json_files/*.json')
        print(f"📂 Archivos: {len(json_files)}")
        
        # Procesar TODOS automáticamente
        exitosos = 0
        fallidos = 0
        existentes = 0
        inicio = time.time()
        
        for i, json_file in enumerate(json_files, 1):
            resultado = process_single_json(json_file, modelo)
            
            if resultado == "exitoso":
                exitosos += 1
                status = "✅"
            elif resultado == "existe":
                existentes += 1
                status = "⚠️"
            else:
                fallidos += 1
                status = "❌"
            
            if i % 10 == 0:  # Progreso cada 10 archivos
                transcurrido = time.time() - inicio
                velocidad = i / transcurrido * 60
                restante = (len(json_files) - i) / velocidad if velocidad > 0 else 0
                
                print(f"[{i:5d}/{len(json_files)}] {status} | ✅{exitosos} ⚠️{existentes} ❌{fallidos} | {velocidad:.1f}/min | {restante:.0f}min restantes")
        
        # Estadísticas finales
        tiempo_total = time.time() - inicio
        print(f"\n🏁 COMPLETADO en {tiempo_total/60:.1f} min")
        print(f"✅ Exitosos: {exitosos}")
        print(f"⚠️ Ya existían: {existentes}")
        print(f"❌ Fallidos: {fallidos}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
