#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "🎮 Kingshot Gift Code Automation wird gestartet..."
echo "================================================"
python3 main.py
echo "================================================"
echo "✅ Fertig. Du kannst dieses Fenster schließen."
read -p "Drücke Enter zum Schließen..."
