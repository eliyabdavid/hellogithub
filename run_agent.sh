#!/bin/bash
# Start the Airbnb Guest Assistant agent

set -a
source .env
set +a

echo ""
echo "🏠 Airbnb Guest Assistant is starting..."
echo "   Press Ctrl+C to stop."
echo ""

python3 gmail_agent.py
