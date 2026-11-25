# Validation — 7 November 2026

- Environment: Windows, Python 3.14.6, pytest 9.2.0.
- `python -m compileall -q .`: passed.
- `python -m pytest -v --tb=short`: **14 passed in 20.56 seconds**, exit code 0.
- Streamlit AppTest: account login/logout, all 16 authenticated pages with synthetic records, and an assistant query passed without UI exceptions or error messages.
- Live server: started at `http://127.0.0.1:18765`; `GET /_stcore/health` returned **200 ok**.
- Dependency installation: required libraries were already available except `pypdf`; installed `pypdf 7.0.0`. Sentence Transformers is optional and was not installed or downloaded.
- The first sandbox test attempt could not create temporary databases. Tests now use the project-local `.pytest_tmp` directory. A clean rerun also set process-local TEMP and TMP to the project directory to avoid Streamlit temporary-directory cleanup restrictions.
- The normal environment has unrelated pre-existing `pymupdf4llm` / `pymupdf-layout` version conflicts reported by `pip check`. ClinMem AI uses pypdf and does not import those packages. Use a virtual environment for an isolated installation.
- Python 3.11/3.12 were not available for execution here. No claims of clinical validity or browser screenshot-based visual verification are made.

If the host sandbox restricts temporary-directory cleanup, run the tests in PowerShell with:

```powershell
$env:TEMP = (Get-Location).Path
$env:TMP = (Get-Location).Path
python -m pytest -v
```

The initial application database was empty; tests use separate temporary databases. Synthetic data is opt-in through Settings.

## Interactive synthetic demonstration

The local `clinmem_demo_1107` account was created for the requested walkthrough, and five labeled synthetic evidence records were loaded. The assistant retrieved both diabetes scenarios. A regression discovered during the walkthrough was fixed so standard safety disclaimers do not mask a difference in assertion polarity. The sample pair is now flagged as Conflicting, while the unrelated medication glossary stays Active. The graph now retains both Related to and Contradicts labels between the same records.

The four-question synthetic benchmark at top-k 3 returned mean precision 0.917 and mean recall 1.000. The diabetes query retrieved the two labeled records plus a glossary record; the other three queries returned their single relevant record. These are demonstration results, not clinical validation. A sample-data regression test was added, bringing the suite to 15 tests.

## Public dashboard deployment

At the user's request, the Vercel dashboard now opens without sign-in or a Vercel access request. A secure visitor cookie selects an isolated database workspace initialized with synthetic evidence. Initialization is batched in one database transaction to reduce first-visit latency. Returning sessions retain their own records; existing private accounts are not exposed. Optional account login remains available.

The full suite passed **21 tests** after the public-dashboard implementation. The six cloud tests were then rerun successfully with additional assertions for original evidence versions, conflict versions, graph labels, preserved logged-in accounts, and cross-visitor isolation. JavaScript syntax and Python compilation passed. `scripts/smoke_public_dashboard.cjs` verifies the deployed application without registration or credentials.
