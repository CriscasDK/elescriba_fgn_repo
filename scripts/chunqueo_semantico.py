import os
import json
import spacy
from uuid import uuid4

INPUT_DIR = '/home/lab4/scripts/documentos_judiciales/json_files'
OUTPUT_DIR = '/home/lab4/scripts/documentos_judiciales/chunks_semanticos_json'
NLP_MODEL = 'es_core_news_md'
MAX_CHUNK_SENTENCES = 5  # Máximo de oraciones por chunk (ajustable)

os.makedirs(OUTPUT_DIR, exist_ok=True)
nlp = spacy.load(NLP_MODEL)

def clean_text(text):
    if not text:
        return ''
    return ' '.join(text.split())

def semantic_chunk(text, max_sentences=MAX_CHUNK_SENTENCES):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    chunks = []
    current = []
    for idx, sent in enumerate(sentences):
        current.append(sent)
        if len(current) >= max_sentences:
            chunks.append(' '.join(current))
            current = []
    if current:
        chunks.append(' '.join(current))
    return chunks

def process_document(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)
    texto = clean_text(doc.get('texto_extraido', ''))
    documento_id = doc.get('id', os.path.basename(json_path))
    archivo = doc.get('archivo', os.path.basename(json_path))
    chunks = semantic_chunk(texto)
    chunk_objs = []
    for idx, chunk_text in enumerate(chunks):
        chunk_id = f"{documento_id}_semchunk_{idx+1}_{uuid4().hex[:8]}"
        chunk_objs.append({
            'chunk_id': chunk_id,
            'texto_chunk': chunk_text,
            'documento_id': documento_id,
            'archivo': archivo,
            'posicion': idx+1,
            'num_oraciones': len(chunk_text.split('.')),
            'longitud': len(chunk_text)
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
            print(f"✅ {fname} → {len(doc_chunks['chunks'])} chunks semánticos")
        except Exception as e:
            print(f"❌ Error procesando {fname}: {e}")

if __name__ == '__main__':
    main()
