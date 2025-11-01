#!/bin/bash
# Manual trigger script for reMarkable ingest
cd "$(dirname "$0")"
source .venv/bin/activate
python main.py
