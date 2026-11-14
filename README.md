# Kairos

Application anti-doomscrolling : 2 à 3 alternatives concrètes pour décrocher des écrans.

## Lancer

**Backend (FastAPI + SQLite)**
```powershell
cd backend
.venv\Scripts\activate          # (ou: python -m venv .venv ; pip install -r requirements.txt)
uvicorn app.main:app --reload --port 8000
```
La base `kairos.db` est créée et remplie automatiquement (20 activités) au premier démarrage.
Pour la réinitialiser, supprimez `kairos.db`.

**Frontend (React + Vite + Tailwind)**
```powershell
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

**IA : Google Gemini (par défaut si une clé est présente)**
1. Crée une clé sur https://aistudio.google.com/apikey
2. Copie `backend/.env.example` en `backend/.env` et colle la clé dans `GEMINI_API_KEY`
3. Relance uvicorn. `GET /api/health` indique le fournisseur utilisé.

**LLM local (alternative, `LLM_PROVIDER=local`)** — LM Studio ou Ollama, API compatible OpenAI :
```powershell
# LM Studio (par défaut) : charger qwen3-8b et démarrer le serveur sur le port 1234
$env:LLM_BASE_URL="http://localhost:1234/v1"; $env:LLM_MODEL="qwen3-8b"
# Ollama :
$env:LLM_BASE_URL="http://localhost:11434/v1"; $env:LLM_MODEL="qwen3:8b"
```

## Fonctionnement
1. Le backend pré-filtre la base SQLite par score (humeur, contexte social, mots-clés) → 4 candidats par catégorie.
2. Le LLM choisit 1 activité par catégorie **parmi les id fournis** et rédige une justification personnalisée (JSON strict).
3. Si le LLM est absent ou renvoie un JSON invalide → repli automatique sur le meilleur score (`"source": "fallback"`).
4. Si le backend est éteint, le frontend affiche des données factices.

Endpoint : `POST /api/kairos/recommend` (contrat conforme au cahier des charges, + champs `instructions` et `source`).
