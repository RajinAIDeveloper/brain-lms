# Brain Gym

Brain Gym is a Django MVP for mental-math practice and progress tracking. Read [docs/README.md](docs/README.md) and [docs/MVP_IMPLEMENTATION_PLAN.md](docs/MVP_IMPLEMENTATION_PLAN.md) before implementing new product work.

## Run locally (Windows)

The workspace currently uses the existing Python 3.10 installation:

```powershell
$python = 'C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe'
& $python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py seed_demo
& .\.venv\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/login/`. Demo emails and password are listed in [docs/DEMO_ACCOUNTS.md](docs/DEMO_ACCOUNTS.md).

Run validation with:

```powershell
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py test
```
