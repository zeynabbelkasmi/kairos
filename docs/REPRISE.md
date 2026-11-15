# Kairos : dossier de reprise

Ce document résume tout ce qui a été fait sur Kairos jusqu'au **15 novembre 2026**, pourquoi,
et comment reprendre le travail. Il complète le [README](../README.md), qui reste la référence
pour installer et lancer le projet.

---

## 1. Où en est le projet

Kairos est une application anti-doomscrolling : l'utilisateur décrit son humeur ou son envie,
et Kairos propose **trois alternatives concrètes** loin des écrans, dont de vrais lieux à
proximité.

| Élément | État |
|---------|------|
| Backend FastAPI + SQLite | Fonctionnel |
| Génération d'activités par LLM (Ollama Cloud, Gemini ou local) | Fonctionnel, avec des idées de secours sans LLM |
| Recherche de lieux **sans clé** via Google Maps | Fonctionnelle, commitée et poussée (`df4e94f`) |
| Choix du rayon (500 m à 10 km) | Fonctionnel, commité et poussé (`df4e94f`) |
| README réécrit (encodage corrigé) | Commité et poussé (`df4e94f`) |
| **Refonte de l'interface** | Terminée et vérifiée, **pas encore commitée** |
| API Anything (outil de rétro-ingénierie d'API) | Installé sur la machine et connecté à Claude Code |

> **Première chose à faire en reprenant :** commiter la refonte de l'interface
> (voir [section 9](#9-checklist-de-reprise)).

---

## 2. Lancer le projet

Deux terminaux :

```powershell
# Terminal 1 : backend (http://localhost:8000)
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 : frontend (http://localhost:5173)
cd frontend
npm run dev
```

Le frontend redirige les appels `/api` vers le backend (proxy dans `frontend/vite.config.ts`).
Vérifier que le backend répond : http://localhost:8000/api/health.

Première installation : voir le [README](../README.md#lancer-le-projet) (`python -m venv`,
`pip install -r requirements.txt`, `npm install`).

---

## 3. Architecture

```
Navigateur (React)
  │  1. position GPS + humeur + texte + rayon
  ▼
POST /api/kairos/recommend   (backend/app/main.py)
  │
  ▼
recommender.py ─────────────┬──────────────────────────────┐
  │                         │                              │
  ▼                         ▼                              ▼
LLM : idées d'activités    Lieux proches                  SQLite : historique
(Ollama / Gemini / local)  ├─ google_places.py (clé API)   (activités déjà faites,
                           └─ maps_search.py   (sans clé)   évitées ensuite)
  │
  ▼
3 recommandations : lieux réels d'abord, complétés par des idées
```

### Fichiers clés

| Fichier | Rôle |
|---------|------|
| `backend/app/main.py` | Routes FastAPI (`/api/health`, `/api/kairos/recommend`, `/api/kairos/history`) |
| `backend/app/recommender.py` | Cœur de la logique : comprend la demande, appelle le LLM et la recherche de lieux, assemble les 3 options |
| `backend/app/google_places.py` | Recherche via l'**API Google Places officielle** (clé requise, payante) |
| `backend/app/maps_search.py` | Recherche via la **page web de Google Maps** (sans clé, non officielle) |
| `backend/app/schemas.py` | Modèles de données échangés avec le frontend |
| `backend/app/database.py` | SQLite (historique des activités faites) |
| `frontend/src/App.tsx` | Écran principal (formulaire → chargement → résultats) |
| `frontend/src/api.ts` | Appels au backend et géolocalisation |
| `frontend/src/components/` | `KairosForm`, `KairosCard`, `InstructionModal`, `BreathingLoader` |
| `frontend/tailwind.config.js` | Couleurs et polices de l'interface |

---

## 4. Chronologie de ce qui a été fait

### 4.1 Installation d'API Anything

[API Anything](https://github.com/goodnight000/api-anything) apprend la requête qu'un site
envoie lui-même depuis sa page web, puis la rejoue en HTTP simple, sans navigateur. C'est ce
qui a permis de trouver la recherche Google Maps utilisée par Kairos.

- Installé avec `npx -y api-anything setup --agents claude-code --yes`.
- **Partage activé** : les opérations apprises sur des pages publiques sont partagées avec le
  catalogue commun, jamais les cookies ni les données personnelles. Pour désactiver :
  `npx api-anything setup --no-share --share-only`.
- Données locales : `C:\Users\zeyna\.api-anything\`.
- Commandes utiles :
  ```powershell
  npx -y api-anything call google-maps searchPlaces "query=café Rabat"   # tester une opération
  npx -y api-anything search tripadvisor                                 # chercher un site dans le catalogue
  npx -y api-anything learn "<url-avec-{param}>" --args ... --args2 ... --args3 ...  # apprendre un site
  ```
- Le dossier `Documents\api-anything` (copie du dépôt) a seulement servi à lire la doc ; il
  n'est pas nécessaire et peut être supprimé.

**Sites étudiés pour Kairos :**

| Site | Verdict |
|------|---------|
| Google Maps | ✅ Utilisé : lieux, notes, photos, horaires, sans clé |
| Eventbrite, Meetup, Ticketmaster | ❌ Peu ou pas de contenu au Maroc |
| Trip.com | ❌ Hôtels uniquement |
| Wikivoyage | ➖ Utile seulement pour du contexte culturel |
| Tripadvisor, AllEvents, Guichet.ma | ❓ Pas encore dans le catalogue, à apprendre (voir [section 8](#8-prochaines-étapes-possibles)) |

### 4.2 Recherche de lieux sans clé (`maps_search.py`)

**Problème :** sans clé Google Places (payante), Kairos n'affichait aucun lieu.

**Solution :** rejouer la requête que la page Google Maps envoie quand on fait une recherche.
API Anything connaissait déjà cette requête (opération `google-maps searchPlaces`), mais elle
ne renvoyait ni photo ni résultats centrés sur une position. Après analyse de la réponse brute
de Google, trois ajouts ont été faits :

1. **Centrage sur l'utilisateur** : un paramètre « viewport »
   (`!4m8!1m3!1d<largeur en m>!2d<lon>!3d<lat>…`) est inséré dans le paramètre `pb`, ce qui
   ramène des résultats autour de la position GPS.
2. **Photo** : extraite de la réponse, puis redimensionnée en changeant la fin de l'URL
   (`=w1000-h600-k-no`). Elle s'ouvre sans compte Google.
3. **Lien vers la fiche Maps** : construit au format officiel
   `https://www.google.com/maps/search/?api=1&query=<nom>&query_place_id=<id>`.

**Où se trouvent les données dans la réponse de Google** (chaque résultat est
`data[64][i][1]`) :

| Donnée | Position |
|--------|----------|
| Nom | `[11]` |
| Adresse | `[18]` (ou `[39]`) |
| Place ID | `[78]` |
| Catégories | `[13]` |
| Note / nombre d'avis | `[4][7]` / `[4][8]` |
| Latitude / longitude | `[9][2]` / `[9][3]` |
| Photo | `[37][0][0][6][0]` (ou `[72][0][0][6][0]`) |
| Horaires (« Ouvert · Ferme à 22:00 ») | `[203][1][4][0]` |

**Filtres appliqués :** note ≥ 4,2, au moins 10 avis, une photo, pas « fermé
définitivement / temporairement », et distance ≤ rayon choisi.

**Choix de la source** (`PLACES_PROVIDER` dans `backend/.env`) :

| Valeur | Comportement |
|--------|--------------|
| `auto` (défaut) | API officielle si `GOOGLE_PLACES_API_KEY` est rempli, sinon Google Maps |
| `google_places` | API officielle uniquement |
| `maps` | Google Maps uniquement |

> ⚠️ **Risque important :** c'est une API **non documentée**. Google peut la modifier ou
> bloquer les requêtes à tout moment, et l'utiliser en production enfreint ses conditions
> d'utilisation. Elle convient pour prototyper ou faire une démo. Pour un vrai déploiement,
> utiliser la clé Places officielle : le code bascule automatiquement dès qu'elle est présente.

### 4.3 Choix du rayon

- Le backend acceptait déjà un `radius` (300 à 10 000 m), mais le frontend envoyait toujours
  2 000 m.
- Ajout d'un choix « Jusqu'où marcher » dans le formulaire : 500 m, 1 km, 2 km, 5 km, 10 km.
- Le backend exclut tout lieu au-delà du rayon (calcul de distance `haversine_m`).
- Si rien ne correspond, un message invite à élargir la distance.

**Vérifié à Rabat :** 500 m → 2 cafés (à 100 m et 500 m) ; 10 km → lieux jusqu'à 6,4 km.

### 4.4 README réécrit

Le README s'affichait mal sur GitHub : accents cassés (« Ã© » au lieu de « é ») et une ligne
en UTF-16 ajoutée par GitHub (`# k a i r o s - p r o j e c t`). Il a été réécrit en UTF-8 propre,
avec une structure claire. L'info périmée sur le fournisseur d'IA a aussi été corrigée : c'est
Ollama Cloud par défaut, puis Gemini, puis local.

**Commit :** `df4e94f` « Add keyless place search via Google Maps and a distance selector »
(regroupe 4.2, 4.3 et 4.4), poussé sur `origin/main`.

### 4.5 Refonte de l'interface (pas encore commitée)

**Pourquoi :** l'ancien design ressemblait à une interface générée par IA (fond crème
`#F4F1EA`, cartes pastel identiques, étiquettes EN MAJUSCULES, infos collées avec « · »).
Pour une app anti-doomscroll, l'objectif était l'inverse d'un feed : calme, posé, peu stimulant.

**Système visuel** (défini dans `frontend/tailwind.config.js`) :

| Nom | Couleur | Usage |
|-----|---------|-------|
| `paper` | `#E6DECE` | Fond de page (calcaire chaud) |
| `surface` | `#F1EBDD` | Cartes, formulaire |
| `ink` | `#283028` | Texte principal, boutons |
| `muted` | `#575C4F` | Texte secondaire |
| `line` | `#D5CAB4` | Bordures fines |
| `moss` | `#5F7D5A` | Catégorie « sortie » |
| `amber` | `#A86A28` | Catégorie « création » |
| `iris` | `#6E6388` | Catégorie « découverte » |

- **Polices :** Fraunces (serif douce) pour le titre, les noms de lieux et les phrases clés ;
  Inter pour le reste.
- Les anciens noms de couleurs (`canvas`, `card`, `charcoal`, `accent-*`) sont gardés comme
  alias, pour ne rien casser.
- Le backend envoie toujours `tag_color` = `sauge` / `peche` / `lilas` ; le frontend les
  traduit en mousse / ambre / iris (`CATEGORY` dans `KairosCard.tsx`).

**Changements par composant :**

- **`KairosCard`** : bande verticale colorée selon la catégorie. Pour un lieu : photo, note,
  avis, distance et horaires (« Ouvert » en couleur) ; l'adresse ne répète plus le nom.
  Les infos sont construites à partir des champs (`rating`, `distance_m`, `opening_hours`),
  pas de la description texte du backend.
- **`KairosForm`** : intitulés en phrases simples, bouton « Me proposer trois idées », aide qui
  explique pourquoi le bouton est grisé.
- **`App`** : grand titre « Kairos » avec *καιρός, le moment opportun*, historique sous forme
  de liste avec dates, cartes à hauteur naturelle.
- **`InstructionModal`, `BreathingLoader`** : nouvelles couleurs et typographie.
- **Accessibilité :** contour visible au clavier, `aria-pressed` sur les choix, fenêtre
  annoncée comme dialogue, animations coupées si l'appareil demande moins de mouvement.

**Vérifié :** `tsc` sans erreur, build Vite OK, captures desktop et mobile avec une vraie
recherche à Rabat (cafés, et mélange lieu + idées).

---

## 5. Configuration (`backend/.env`)

Copier `backend/.env.example` en `backend/.env`. Variables utilisées :

| Variable | Rôle | Défaut |
|----------|------|--------|
| `OLLAMA_API_KEY` | Clé Ollama Cloud (fournisseur IA prioritaire) | — |
| `GEMINI_API_KEY` | Clé Gemini (utilisée si pas de clé Ollama) | — |
| `LLM_PROVIDER` | Forcer `ollama_cloud`, `gemini` ou `local` | auto |
| `LLM_MODEL`, `LLM_BASE_URL` | Modèle et adresse du LLM | selon fournisseur |
| `LLM_TIMEOUT` | Délai max d'appel au LLM (s) | `120` |
| `PLACES_PROVIDER` | `auto`, `google_places` ou `maps` | `auto` |
| `GOOGLE_PLACES_API_KEY` | Clé Places officielle | vide |
| `GOOGLE_PLACES_MIN_RATING` | Note minimale d'un lieu | `4.2` |
| `GOOGLE_PLACES_MIN_REVIEWS` | Nombre d'avis minimal | `10` |

> `.env` est ignoré par git : ne jamais commiter de clé.

---

## 6. Si la recherche Google Maps casse

Symptôme : le message « Google Maps n'a pas répondu » s'affiche, ou plus aucun lieu
n'apparaît alors que la position est autorisée.

1. **Tester l'opération partagée :**
   `npx -y api-anything call google-maps searchPlaces "query=café Rabat"`.
   Si elle échoue aussi, Google a changé quelque chose. Un autre utilisateur d'API Anything
   l'aura peut-être déjà réparée : relancer plus tard, ou lancer
   `npx api-anything heal google-maps searchPlaces`.
2. **Récupérer le nouveau gabarit :** le paramètre `pb` à jour se trouve dans la spec
   d'API Anything (`sites/google-maps.json`, emplacement `query:pb`). Le recopier dans
   `PB_TEMPLATE` de `maps_search.py`, en gardant `{viewport}` juste après `!1s{query}`.
3. **Vérifier les positions des données** (tableau de la section 4.2) : si un champ est vide,
   sa position a changé. Chercher la nouvelle position dans la réponse brute ; l'opération
   d'API Anything (`response.pick`) donne les positions à jour du nom, de l'adresse, de la note
   et des coordonnées.
4. **En dernier recours :** `PLACES_PROVIDER=google_places` avec une clé officielle.

Test rapide du module seul :

```powershell
cd backend
.venv\Scripts\python.exe -c "import asyncio; from app.maps_search import search_maps; print(asyncio.run(search_maps(34.0209, -6.8416, 1000, {'cafe'}))[:2])"
```

---

## 7. Limites connues

- **Google Maps non officiel :** fragile, et interdit en production (voir 4.2).
- Au plus **20 résultats par type** de lieu et par recherche : dans une grande ville avec un
  rayon de 10 km, ce sont surtout les lieux populaires qui ressortent.
- La requête Maps est fixée en **français / Maroc** (`hl=fr`, `gl=ma`) ; à adapter pour un
  autre pays.
- Les adresses peuvent être des **codes Plus** (« 25F6+WQR OKFE, Rabat ») quand Google n'a pas
  d'adresse postale.
- Pas de tests automatisés : la vérification a été faite à la main (scripts et captures).
- Sans géolocalisation autorisée, Kairos ne propose que des idées d'activités, pas de lieux.

---

## 8. Prochaines étapes possibles

Par ordre de priorité suggéré :

1. **Commiter la refonte de l'interface** (voir section 9).
2. **Ajouter des événements** (concerts, expos, ateliers) : apprendre **AllEvents** ou
   **Guichet.ma** avec API Anything (`npx api-anything learn …`), puis créer un module comme
   `maps_search.py`. Google Places n'a pas d'événements, c'est un vrai complément.
3. **Tests automatisés** : au minimum un test du filtrage par rayon et de l'extraction des
   champs de `maps_search.py`, à partir d'une réponse Google enregistrée.
4. **Mode sombre** pour le soir (le moment où l'on pose le téléphone) : il suffit de redéfinir
   les couleurs de `tailwind.config.js`.
5. **Préparer la production** : clé Places officielle, `PLACES_PROVIDER=google_places`.

---

## 9. Checklist de reprise

- [ ] Lancer backend et frontend (section 2) et vérifier http://localhost:8000/api/health.
- [ ] Faire une recherche avec la position autorisée : des lieux avec photo doivent apparaître.
- [ ] Vérifier avec `git status` que la refonte de l'interface est bien commitée ; sinon :
  ```powershell
  git add frontend README.md docs
  git commit -m "Redesign UI with a calmer visual identity and refresh README"
  git push
  ```
- [ ] Relire la section 7 (limites) avant toute mise en ligne.
