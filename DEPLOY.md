# 🚀 Déploiement en 15 minutes

Ce guide explique comment déployer **ClipForge AI** sur :
- **GitHub** (code)
- **Netlify** (frontend React statique — gratuit)
- **Render** (backend FastAPI + workers Celery — gratuit au début)
- **Neon** (PostgreSQL serverless — gratuit)
- **Upstash** (Redis serverless — gratuit)
- **Cloudflare R2** (stockage objet S3-compatible — gratuit jusqu'à 10 GB)

> Toutes ces offres ont un **free tier** qui suffit largement pour un MVP.

---

## Étape 0 — Créer le repo GitHub

```bash
# Sur github.com → New repository → "clipforge-ai" (privé de préférence)
# Puis en local :

cd clipforge-ai
git init
git add -A
git commit -m "Initial commit — ClipForge AI v0.1.0"
git branch -M main
git remote add origin git@github.com:<ton-user>/clipforge-ai.git
git push -u origin main
```

(Le `.gitignore` exclut déjà `.env`, `node_modules`, `data/`, etc.)

---

## Étape 1 — Provisionner les services gratuits

| Service | URL | Ce qu'on en tire |
|---|---|---|
| **Neon** | https://neon.tech | PostgreSQL serverless, free tier 0.5 GB |
| **Upstash** | https://upstash.com | Redis serverless, free tier 10 000 cmd/jour |
| **Cloudflare R2** | https://cloudflare.com | Stockage S3-compatible, 10 GB gratuits |
| **OpenAI** | https://platform.openai.com | Clé API pour l'AI Clip Finder (pay-as-you-go) |

Pour chaque service :
1. Crée un compte / connecte-toi
2. Crée une instance / bucket / clé
3. Note les valeurs suivantes (tu en auras besoin à l'étape 3) :
   - `DATABASE_URL` (postgresql://…)
   - `REDIS_URL` (rediss://… pour Upstash)
   - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`
   - `OPENAI_API_KEY` (commence par `gpt-4o-mini` à ~0.15 $/M tokens d'entrée)

---

## Étape 2 — Déployer le frontend sur Netlify

### Option A — Via l'UI Netlify (le plus simple)

1. Va sur https://app.netlify.com → **Add new site** → **Import an existing project**
2. Choisis **GitHub** → sélectionne `clipforge-ai`
3. Configure :
   - **Base directory** : `frontend`
   - **Build command** : `npm run build`
   - **Publish directory** : `frontend/dist`
4. **Environment variables** → ajoute :
   - `VITE_API_URL` = `https://clipforge-backend.onrender.com` (URL Render, voir étape 3)
5. **Deploy site** → tu obtiens `https://clipforge-ai-XXXX.netlify.app`

> Le fichier `netlify.toml` à la racine est détecté automatiquement et configure les redirects, les headers de sécurité, et le proxy `/api/*` vers le backend.

### Option B — Via Netlify CLI

```bash
npm i -g netlify-cli
netlify login
cd frontend && npm run build && cd ..
netlify deploy --prod --dir=frontend/dist
```

---

## Étape 3 — Déployer le backend sur Render

1. Va sur https://dashboard.render.com → **New** → **Blueprint**
2. Connecte le repo GitHub `clipforge-ai`
3. Render détecte `render.yaml` et propose deux services :
   - `clipforge-backend` (web)
   - `clipforge-worker` (worker)
4. **Environment variables** — pour chaque service, configure les secrets :
   - `DATABASE_URL` → la chaîne Neon
   - `REDIS_URL` → la chaîne Upstash
   - `CELERY_BROKER_URL` = `REDIS_URL`
   - `CELERY_RESULT_BACKEND` = `REDIS_URL`
   - `R2_*` → tes identifiants Cloudflare
   - `OPENAI_API_KEY` → ta clé OpenAI
   - `APP_URL` et `FRONTEND_URL` → ton URL Netlify (https://clipforge-ai-XXXX.netlify.app)
   - `CORS_ALLOW_ORIGINS` → ton URL Netlify
5. **Apply** → Render build et déploie. Quelques minutes plus tard :
   - Backend : `https://clipforge-backend.onrender.com`
6. **Teste** :
   ```bash
   curl https://clipforge-backend.onrender.com/api/v1/health
   # → {"status":"ok","version":"0.1.0"}
   ```

> Le 1er déploiement d'un service Render "free" peut prendre 5-10 min et se met en veille après 15 min d'inactivité. Le cold-start qui suit prend ~30 s. C'est normal.

---

## Étape 4 — Rebrancher le frontend sur le vrai backend

1. Retourne sur **Netlify → Site settings → Environment variables**
2. Mets à jour `VITE_API_URL` avec l'URL Render (`https://clipforge-backend.onrender.com`)
3. **Deploys** → **Trigger deploy** → **Clear cache and deploy**

---

## Étape 5 — Configurer Cloudflare R2 (stockage)

1. https://dash.cloudflare.com → **R2** → **Create bucket** → `clipforge`
2. **R2 → Manage R2 API Tokens** → **Create API token** :
   - Permissions : Object Read & Write
   - Bucket : `clipforge`
3. Note `Access Key ID` et `Secret Access Key`
4. Trouve ton `Account ID` sur le dashboard R2 (sidebar)
5. Mets ces valeurs dans Render (étape 3) :
   - `STORAGE_BACKEND=r2`
   - `R2_ACCOUNT_ID=…`
   - `R2_ACCESS_KEY=…`
   - `R2_SECRET_KEY=…`
   - `R2_BUCKET=clipforge`

> Rendre le bucket public (pour que les MP4 servis directement) :
> R2 → `clipforge` → Settings → Public access → **Connect domain** ou activer le sous-domaine R2.dev.

---

## Étape 6 — Créer le compte admin

Le bootstrap crée automatiquement un admin au démarrage. Vérifie les logs Render :
- `clipforge-backend` → **Logs**
- Cherche `Bootstrapped admin user …`
- Connecte-toi sur ton site Netlify avec l'email et le mot de passe configurés (`ADMIN_EMAIL` / `ADMIN_PASSWORD`)

---

## Étape 7 — Custom domain (optionnel)

### Sur Netlify
- **Domain settings** → **Add custom domain** → `clipforge.ai`
- Configure les DNS chez ton registrar (Netlify t'affiche les records à ajouter)

### Sur Render
- **Settings** → **Custom domain** → `api.clipforge.ai`
- Ajoute un CNAME `api → clipforge-backend.onrender.com`

### Mettre à jour
- Render : `APP_URL=https://clipforge.ai`, `API_URL=https://api.clipforge.ai`, `CORS_ALLOW_ORIGINS=https://clipforge.ai`
- Netlify : `VITE_API_URL=https://api.clipforge.ai`
- Redéploie les deux

---

## 💰 Coûts estimés (free tier)

| Service | Free tier | Au-delà |
|---|---|---|
| **Netlify** | 100 GB bande passante/mois | $19/mois pour 1 TB |
| **Render web** | Service "free" 750h/mois, dort après 15 min | $7/mois "Starter" (no sleep) |
| **Render worker** | 750h/mois | $7/mois |
| **Neon** | 0.5 GB Postgres, 191h compute/mois | $19/mois pour 10 GB |
| **Upstash** | 10 000 cmd Redis/jour | $0.2/100k cmd |
| **Cloudflare R2** | 10 GB stockage, 10M Class B ops/mois | $0.015/GB/mois |
| **OpenAI gpt-4o-mini** | — | ~$0.15 / 1M tokens d'entrée |

**MVP complet : $0/mois** tant que tu restes dans les free tiers (et que tu mets en veille Render quand tu n'utilises pas).

---

## 🔁 CI / CD

Le repo contient déjà `.github/workflows/ci.yml` :
- À chaque push sur `main`, GitHub Actions :
  - Lance les tests Python
  - Build le frontend
- **Netlify** détecte les pushes et redéploie automatiquement
- **Render** idem

Pour ajouter le déploiement auto, va dans :
- Netlify : **Site settings → Build & deploy → Continuous deployment** (activé par défaut)
- Render : **Settings → Auto-Deploy** (activé par défaut sur les Blueprints)

---

## 🆘 Dépannage

### Le frontend ne se connecte pas au backend
- Vérifie `VITE_API_URL` dans Netlify
- Vérifie `CORS_ALLOW_ORIGINS` dans Render (doit inclure l'URL Netlify)
- Ouvre les DevTools → Network pour voir les requêtes bloquées

### L'analyse ne trouve aucun clip
- Vérifie que `OPENAI_API_KEY` est valide
- Vérifie `DEMO_MODE=false` (sinon l'app reste en mode démo même avec une clé)

### Render "out of memory"
- Le plan "free" a 512 MB. Augmente à "Starter" ($7) pour 2 GB.

### Trop de cold-starts
- Le plan "free" de Render dort après 15 min. Upgrade à "Starter" pour le garder éveillé.

### Logs
- Render : `clipforge-backend` → **Logs** (live tail)
- Netlify : **Functions** → **Logs**

---

## ✅ Checklist de production (post-déploiement)

- [ ] Change `SECRET_KEY` et `JWT_SECRET` (Reder les a générés au hazard)
- [ ] Change `ADMIN_PASSWORD`
- [ ] Configure un vrai `AI_PROVIDER` et désactive `DEMO_MODE`
- [ ] Active HTTPS (Netlify le fait par défaut, Render aussi)
- [ ] Limite `CORS_ALLOW_ORIGINS` à ton vrai domaine
- [ ] Mets en place des backups Neon (PITR est inclus gratuit)
- [ ] Configure Sentry (optionnel) : `SENTRY_DSN=…` côté backend

Bon déploiement 🚀
