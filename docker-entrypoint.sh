#!/bin/bash
set -e

# Create codex config directory
mkdir -p /root/.codex

# Generate config.toml from environment variables
cat > /root/.codex/config.toml << EOF
model_provider = "${CODEX_MODEL_PROVIDER:-openai}"
model = "${CODEX_MODEL:-gpt-4}"
model_reasoning_effort = "${CODEX_MODEL_REASONING_EFFORT:-high}"

[model_providers.${CODEX_MODEL_PROVIDER:-openai}]
name = "${CODEX_MODEL_PROVIDER:-openai}"
base_url = "${CODEX_API_BASE_URL:-https://api.openai.com/v1}"
wire_api = "responses"
EOF

# Generate auth.json from environment variables
cat > /root/.codex/auth.json << EOF
{
  "OPENAI_API_KEY": "${CODEX_API_KEY:-${OPENAI_API_KEY}}"
}
EOF

echo "Codex configuration generated:"
echo "  Model Provider: ${CODEX_MODEL_PROVIDER:-openai}"
echo "  Model: ${CODEX_MODEL:-gpt-4}"
echo "  Base URL: ${CODEX_API_BASE_URL:-https://api.openai.com/v1}"

# Execute the main command
exec "$@"
