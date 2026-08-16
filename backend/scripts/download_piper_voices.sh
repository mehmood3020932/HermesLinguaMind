#!/usr/bin/env bash
# Downloads real Piper ONNX voice models used by the self-hosted TTS engine.
# Run this once after `docker compose up -d` (or before, for a faster first
# request) so phase3/services/tts/main.py's PiperEngine has voices to load.
#
# Usage: ./scripts/download_piper_voices.sh
#
# Voices come from the official rhasspy/piper-voices Hugging Face repo.
# Override VOICES or ONNX_BASE_URL to point at a mirror if huggingface.co
# is not reachable from your network.

set -euo pipefail

VOICES_DIR="${PIPER_VOICES_DIR:-./piper_voices}"
ONNX_BASE_URL="${ONNX_BASE_URL:-https://huggingface.co/rhasspy/piper-voices/resolve/main}"

# lang_code -> "hf_path_dir/voice_name"
declare -A VOICES=(
  [en]="en/en_US/amy/medium/en_US-amy-medium"
  [es]="es/es_ES/davefx/medium/es_ES-davefx-medium"
  [fr]="fr/fr_FR/siwis/medium/fr_FR-siwis-medium"
  [de]="de/de_DE/thorsten/medium/de_DE-thorsten-medium"
)

mkdir -p "$VOICES_DIR"

for lang in "${!VOICES[@]}"; do
  path="${VOICES[$lang]}"
  name="$(basename "$path")"
  echo "→ Downloading Piper voice for '$lang': $name"
  curl -fL "${ONNX_BASE_URL}/${path}.onnx" -o "${VOICES_DIR}/${name}.onnx"
  curl -fL "${ONNX_BASE_URL}/${path}.onnx.json" -o "${VOICES_DIR}/${name}.onnx.json"
done

echo ""
echo "Done. Copy these into the tts container's /app/voices volume, e.g.:"
echo "  docker cp ${VOICES_DIR}/. hermes_tts:/app/voices/"
echo "or mount ${VOICES_DIR} directly as the piper_voices volume source."
