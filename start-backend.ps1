# Start ResumeRAG Backend
Set-Location -Path "C:\Users\herok\Documents\ResumeRAG\api"
& "C:/Users/herok/Documents/ResumeRAG/.venv/Scripts/uvicorn.exe" app.main:app --reload --host 0.0.0.0 --port 8000
