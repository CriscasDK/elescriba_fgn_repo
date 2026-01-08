import os
import json
import re
from uuid import uuid4

INPUT_DIR = '/home/lab4/scripts/documentos_judiciales/json_files'
OUTPUT_DIR = '/home/lab4/scripts/documentos_judiciales/chunks_json'
CHUNK_SIZE = 1200  # caracteres (ajustable)
MIN_CHUNK_SIZE = 300  # para evitar chunks demasiado cortos

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text):
    """Limpia el texto extraído (OCR)"""
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_text(text, chunk_size=CHUNK_SIZE, min_chunk_size=MIN_CHUNK_SIZE):
    """
    Divide el texto en chunks jurídicos estrictos: cada chunk es un párrafo individual.
    No se unen párrafos cortos, y cada chunk lleva su número de párrafo.
    Si un párrafo es demasiado largo, se subdivide por longitud máxima.
    """
    paragraphs = re.split(r'\n{2,}|\r{2,}', text)
    chunks = []
    for idx, p in enumerate(paragraphs):
        p_clean = p.strip()
        if not p_clean:
            continue
        # Si el párrafo es muy largo, subdividir
        if len(p_clean) > chunk_size * 1.5:
            for i in range(0, len(p_clean), chunk_size):
                part = p_clean[i:i+chunk_size]
                chunks.append({
                    'texto_chunk': part.strip(),
                    'num_parrafo': idx+1,
                    'posicion': i,
                    'longitud': len(part.strip())
                })
        else:
            chunks.append({
                'texto_chunk': p_clean,
                'num_parrafo': idx+1,
                'posicion': 0,
                'longitud': len(p_clean)
            })
    return chunks

def process_document(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)
    texto = clean_text(doc.get('texto_extraido', ''))
    documento_id = doc.get('id', os.path.basename(json_path))
    archivo = doc.get('archivo', os.path.basename(json_path))
    chunks = split_text(texto)
    chunk_objs = []
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{documento_id}_chunk_{idx+1}_{uuid4().hex[:8]}"
        chunk_objs.append({
            'chunk_id': chunk_id,
            'texto_chunk': chunk['texto_chunk'],
            'documento_id': documento_id,
            'archivo': archivo,
            'num_parrafo': chunk['num_parrafo'],
            'posicion': chunk['posicion'],
            'longitud': chunk['longitud']
            # Puedes agregar más metadatos aquí
        })
    return {
        'documento_id': documento_id,
        'archivo': archivo,
        'chunks': chunk_objs
    }

def main():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    print(f"Procesando {len(files)} documentos...")
    for fname in files:
        in_path = os.path.join(INPUT_DIR, fname)
        out_path = os.path.join(OUTPUT_DIR, fname)
        try:
            doc_chunks = process_document(in_path)
            with open(out_path, 'w', encoding='utf-8') as out:
                json.dump(doc_chunks, out, ensure_ascii=False, indent=2)
            print(f"✅ {fname} → {len(doc_chunks['chunks'])} chunks")
        except Exception as e:
            print(f"❌ Error procesando {fname}: {e}")

if __name__ == '__main__':
    main()
