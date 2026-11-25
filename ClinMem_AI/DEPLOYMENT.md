# Vercel deployment

Production: **https://clinmem-ai.vercel.app**

Project: `clinmem-ai`, deployed under the existing Vercel account. A free Neon PostgreSQL resource named `clinmem-ai-db` provides persistent storage in Singapore. Credentials are injected through Vercel environment variables and are excluded from source control and deployment uploads.

Vercel Authentication was disabled at the user's explicit request, so generated deployment URLs can also be opened without requesting Vercel team access. The dashboard now opens automatically without application sign-in. Each new visitor receives an isolated workspace preloaded with clearly labeled synthetic evidence. Existing accounts and their records remain private; optional account login is still available.

## Cloud application

The cloud version uses `server.py` (FastAPI) and the responsive HTML/CSS/JavaScript frontend in `web/`. It calls the same database models, memory store, six agents, retrieval, graph, evaluation and report code as the local Streamlit application. The cloud dashboard has all 16 navigation areas.

Vercel uses HTTP request handlers rather than running `streamlit run`. The local Streamlit app remains in `app.py`. Cloud storage uses PostgreSQL; the local app defaults to SQLite. Neither local accounts nor existing uploaded data were copied to the public deployment. Opening the deployed site creates a visitor session and shows the dashboard directly, including five synthetic demonstration evidence records and their review findings. A returning valid session reuses its own workspace.

Authentication uses bcrypt password hashing and opaque, database-backed sessions. Only token hashes are stored. Cookies are HttpOnly, Secure in production, SameSite Strict, and expire after 12 hours. Logout invalidates the stored session. Mutating requests reject a mismatched browser Origin. Account-scoped API access is tested. This remains an academic prototype, not a hardened medical production system.

Cloud document uploads accept PDF, DOCX, TXT and CSV, limited to 4 MB per file to fit the hosting request limit. No paid AI service or embedding model download is required.

## Rebuild and redeploy

From the `ClinMem_AI` directory:

```powershell
python scripts/prepare_vercel.py
cd .vercel-deploy
npx --yes vercel@latest link --yes --project clinmem-ai
npx --yes vercel@latest deploy --prod --yes
```

`prepare_vercel.py` copies only required backend, config, frontend assets and labeled sample documents into `.vercel-deploy`. It excludes local databases, user uploads, reports, tests and secrets. It installs the smaller cloud dependency list from `requirements-vercel.txt` and selects Python 3.12. The staging directory and all environment files are ignored by Git.

On this computer, the Node CLI needed the Windows certificate store:

```powershell
$env:NODE_USE_SYSTEM_CA = '1'
```

No TLS validation was disabled.

## Cloud testing

Install all development/runtime dependencies, then run:

```powershell
pip install -r requirements.txt
python -m pytest -v
node --check web/app.js
```

The full suite passed **19 tests** on 7 November 2026. Additional API tests cover authentication, session revocation, cross-account access, origin checks, synthetic ingestion, conflict detection, retrieval, graph relationships, versioning, supersession, evaluation and JSON/CSV/PDF exports.

A real production smoke test is available:

```powershell
node scripts/smoke_vercel.cjs https://clinmem-ai.vercel.app
```

It creates a synthetic-only verification account, checks persistent PostgreSQL health, assets, login, sample loading, source-linked retrieval, graph contradictions, the four-query benchmark, exports and logout. It does not log credentials or copy existing local records. Running it again creates another isolated test account.

## Verified production endpoints

- `/`: public sign-in page, HTTP 200.
- `/assets/app.js` and `/assets/styles.css`: HTTP 200.
- `/api/health`: HTTP 200, `storage: postgresql`.
- `/api/auth/me`: HTTP 401 when unauthenticated, as expected.

Database environment variables are managed by the Vercel Neon integration. The server refuses to use ephemeral SQLite when `VERCEL` is set, so missing cloud configuration fails explicitly instead of silently losing records. The free database can sleep when idle; the first request may take longer to respond.
