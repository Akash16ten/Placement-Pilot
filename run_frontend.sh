#!/usr/bin/env bash
cd "$(dirname "$0")"
exec streamlit run frontend/streamlit_app.py --server.port 8501
