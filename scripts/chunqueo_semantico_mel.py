import os
import json
from uuid import uuid4
from transformers import AutoTokenizer, AutoModel
import torch
import spacy

INPUT_DIR = '/home/lab4/scripts/documentos_judiciales/json_files'
OUTPUT_DIR = '/home/lab4/scripts/documentos_judiciales/chunks_semanticos_mel_json'
MODEL_NAME = 'IIC/MEL'
MAX_CHUNK_SENTENCES = 5  # Máximo de oraciones por chunk

os.makedirs(OUTPUT_DIR, exist_ok=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
nlp = spacy.load('es_core_news_md')

def clean_text(text):
    if not text:
        return ''
    return ' '.join(text.split())

def get_sentence_embeddings(sentences):
    inputs = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        # Usar el embedding [CLS] de cada oración
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
    return embeddings

def semantic_chunk_mel(text, max_sentences=MAX_CHUNK_SENTENCES):
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    chunks = []
    current = []
    for sent in sentences:
        current.append(sent)
        if len(current) >= max_sentences:
            chunks.append(list(current))
            current = []
    if current:
        chunks.append(list(current))
    return chunks

def process_document(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        doc = json.load(f)
    texto = clean_text(doc.get('texto_extraido', ''))
    documento_id = doc.get('id', os.path.basename(json_path))
    archivo = doc.get('archivo', os.path.basename(json_path))
    chunks = semantic_chunk_mel(texto)
    chunk_objs = []
    for idx, chunk_sentences in enumerate(chunks):
        chunk_text = ' '.join(chunk_sentences)
        chunk_id = f"{documento_id}_melchunk_{idx+1}_{uuid4().hex[:8]}"
        # Obtener embedding del chunk usando MEL
        embedding = get_sentence_embeddings([chunk_text])[0].tolist()
        chunk_objs.append({
            'chunk_id': chunk_id,
            'texto_chunk': chunk_text,
            'documento_id': documento_id,
            'archivo': archivo,
            'posicion': idx+1,
            'num_oraciones': len(chunk_sentences),
            'longitud': len(chunk_text),
            'mel_embedding': embedding
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
            print(f"✅ {fname} → {len(doc_chunks['chunks'])} chunks MEL semánticos")
        except Exception as e:
            print(f"❌ Error procesando {fname}: {e}")

if __name__ == '__main__':
    main()
