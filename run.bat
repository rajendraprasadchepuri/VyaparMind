@echo off
echo Starting Retail Manager...
pip install -r requirements.txt > nul 2>&1
streamlit run app.py
pause
