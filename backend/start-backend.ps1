# Start the backend in a PowerShell terminal
# Run this from the backend folder.

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force
$pythonPath = "C:\Users\nithy_2vne\AppData\Local\Programs\Python\Python312\python.exe"
if (-Not (Test-Path $pythonPath)) {
    Write-Error "Python not found at $pythonPath. Install Python 3.12 or update this script."
    exit 1
}

& $pythonPath -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
