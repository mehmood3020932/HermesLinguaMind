#!/bin/sh
# Runs inside the tts_voices_init container (curlimages/curl, Alpine — /bin/sh
# only, no bash) to download real, free, open-source Piper voice models into
# the same volume hermes_backend mounts at /app/voices.
#
# This is a plain file (not inlined into docker-compose.yml's `command:`)
# specifically so none of its $variables get caught by docker-compose's own
# interpolation pass before the shell ever sees them — an inline version of
# this failed with "invalid interpolation format" because compose tries to
# expand ${pair%%:*}-style shell parameter expansion itself and doesn't
# understand that syntax.
set -e

BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main"

# POSIX sh has no associative arrays, so: one "hf_path:voice_name" pair per
# line instead of a bash `declare -A`.
VOICES="
en/en_US/amy/medium/en_US-amy-medium:en_US-amy-medium
es/es_ES/davefx/medium/es_ES-davefx-medium:es_ES-davefx-medium
fr/fr_FR/siwis/medium/fr_FR-siwis-medium:fr_FR-siwis-medium
de/de_DE/thorsten/medium/de_DE-thorsten-medium:de_DE-thorsten-medium
"

for pair in $VOICES; do
  src=$(echo "$pair" | cut -d: -f1)
  name=$(echo "$pair" | cut -d: -f2)
  echo "Downloading voice: $name"
  curl -fL "$BASE/$src.onnx" -o "/app/voices/$name.onnx"
  curl -fL "$BASE/$src.onnx.json" -o "/app/voices/$name.onnx.json"
done

echo "Voices ready."
