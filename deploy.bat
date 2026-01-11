@echo off
echo 🚀 PREPARING FILES FOR HUGGING FACE DEPLOYMENT
echo Target: https://huggingface.co/spaces/rishirajpathak/task-management
echo.

echo 📁 Files ready for upload:
echo.
dir /b app.py assignment_engine.py task_manager.py requirements.txt README.md users.csv tasks.csv results.csv task_progress.json .gitignore 2>nul

echo.
echo ✅ All files are ready!
echo.
echo 📋 NEXT STEPS:
echo 1. Go to: https://huggingface.co/new-space
echo 2. Space name: task-management
echo 3. Owner: rishirajpathak  
echo 4. SDK: Gradio
echo 5. Upload the files listed above
echo 6. Your app will be live at: https://huggingface.co/spaces/rishirajpathak/task-management
echo.
echo 🚫 DO NOT upload: .venv folder or any .pkl files
echo.
pause