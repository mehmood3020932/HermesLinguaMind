#!/bin/bash
set -e
MODELS_DIR="./backend/models/avatar"
mkdir -p "$MODELS_DIR"
echo "📥 Downloading open-source SadTalker checkpoint..."
wget -c -P "$MODELS_DIR" \
  "https://huggingface.co/camenduru/SadTalker/resolve/main/checkpoints/sadtalker_v002_rc.pth" \
  || echo "⚠️ Auto-download failed. Manually download from HuggingFace and place in $MODELS_DIR"
echo "✅ Avatar models directory ready at: $MODELS_DIR"
