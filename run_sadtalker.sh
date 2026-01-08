#!/bin/bash
# Script para ejecutar SadTalker fácilmente

# Activar entorno
source ~/anaconda3/etc/profile.d/conda.sh
conda activate sadtalker

# Parámetros por defecto
IMAGE_PATH="${1:-examples/source_image/full_body_1.jpg}"
AUDIO_PATH="${2:-examples/driven_audio/bus_chinese.wav}"
OUTPUT_DIR="${3:-results}"

echo "🎭 Ejecutando SadTalker..."
echo "📷 Imagen: $IMAGE_PATH"
echo "🎵 Audio: $AUDIO_PATH"
echo "📁 Salida: $OUTPUT_DIR"

python inference.py \
    --driven_audio "$AUDIO_PATH" \
    --source_image "$IMAGE_PATH" \
    --result_dir "$OUTPUT_DIR" \
    --expression_scale 1.0 \
    --still \
    --preprocess crop \
    --enhancer gfpgan

echo "✅ ¡Terminado! Revisa la carpeta $OUTPUT_DIR"
