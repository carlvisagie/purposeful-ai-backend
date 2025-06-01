# launch_backend.ps1

cd "C:\Projects\PurposefulLive\backend"
code .
& "C:\Projects\PurposefulLive\venv\Scripts\Activate.ps1"
$env:FLASK_APP = "main:app"
$env:FLASK_ENV = "development"
flask run --reload --host=0.0.0.0 --port=5000
