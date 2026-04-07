import secrets
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")

# 1) Il file .env esiste? Se no lo creo vuoto
if not os.path.exists(env_path):
    open(env_path, "w").close()
    print(".env non trovato, creato.")

# 2) SECRET_KEY è nel file? Se no la aggiungo
with open(env_path, "r") as f:
    content = f.read()

if "SECRET_KEY" not in content:
    key = secrets.token_hex(32)
    with open(env_path, "a") as f:
        f.write(f"\nSECRET_KEY={key}\n")
    print("SECRET_KEY generata e aggiunta al .env.")
else:
    print("SECRET_KEY già presente, nessuna modifica.")