# hlphuis

Korte starter voor het `hlphuis` project — een eenvoudige webapp voor het bijhouden van lessen (datum, klantnaam, bedrag) met login op een Raspberry Pi. Doel: ontwikkelen op de Pi en later frontend deployen naar Netlify.

Quickstart (Raspberry Pi):

```bash
# update Pi
sudo apt update && sudo apt upgrade -y

# Python en virtuele omgeving
sudo apt install -y python3 python3-venv python3-pip git

# Maak venv, installeer dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Initialiseert database + (optioneel) maakt admin gebruiker aan
python3 backend/init_db.py --create-admin

# Run de app
export FLASK_APP=backend/app.py
export FLASK_ENV=development
flask run --host=0.0.0.0
```

Git (lokale repo):

```bash
git init
git add .
git commit -m "Initial scaffold: Flask backend + minimal frontend"
# Voeg remote toe en push (maak remote repo eerst op GitHub/GitLab)
git remote add origin <git-url>
git push -u origin main
```

Structuur:

- `backend/` - Flask backend, models en API
- `frontend/` - simpele static frontend (login + formulier)

Volgende stappen:
- Test lokaal op de Pi
- Kies hosting voor backend (Pi/Render/Heroku) en zet frontend op Netlify
