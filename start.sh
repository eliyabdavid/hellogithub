#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "✅ Starting Airbnb Guest Assistant..."
echo "👉 Open your browser and go to: http://localhost:5000"
echo "   Press Ctrl+C to stop."
echo ""
python app.py
