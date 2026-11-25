# ClinMem AI

**An Adaptive Agent Memory Framework for Long-Term Clinical Knowledge Retrieval and Evidence Updating**

ClinMem AI is an offline academic prototype for persistent, source-linked evidence retrieval. It addresses loss of previous context and difficulty inspecting changing evidence. It does not diagnose, prescribe, establish causation, or validate medical guidance.

**Vercel web application:** https://clinmem-ai.vercel.app — see [DEPLOYMENT.md](DEPLOYMENT.md) for the cloud architecture, persistent database, testing and redeployment commands. The local Streamlit interface below remains available.

## Objectives and methodology

Ingest documents, normalize and chunk their text, attach provenance, retrieve relevant records, expose possible conflicts, preserve every revision, and evaluate retrieval against explicit labels. All records and operational logs belong to an authenticated account. Dashboard metrics query actual stored records; demonstration data is loaded only on request.

## Installation and execution

Python 3.11 or 3.12 is recommended. This workspace was also tested on the available Python 3.14.6 interpreter. From PowerShell:

```powershell
cd "C:\Users\LENOVO\OneDrive\Documents\ChatGPT\Clinmem AI\ClinMem_AI"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m compileall -q .
pytest -v
streamlit run app.py
```

Open the local URL printed by Streamlit, normally http://localhost:8501. Create an account and then sign in. Any non-empty username and password are accepted, including long Unicode passwords. Passwords are SHA-256 prehashed before bcrypt to preserve bcrypt compatibility with arbitrary input length. There are no default credentials.

For an existing interpreter, skip virtual environment creation. The SQLite database is created automatically in `data/clinmem.db`. Optional configuration: copy `.env.example` to `.env`. `CLINMEM_DB` is a SQLAlchemy SQLite URL. Protect the database and use filesystem permissions appropriate to the host.

## Architecture and workflow

```text
Streamlit authenticated UI
  └─ user-scoped Store + central Orchestrator
       ├─ document extraction → Encoding → Evidence Updating → Consolidation
       ├─ Retrieval → Working context → Reasoning → Evaluation → Analysis history
       └─ SQLite: users, documents, memories, relationships, versions,
                  evidence records, agent logs, analysis history
```

Six agent modules have a common result dictionary containing records processed, findings and a summary, plus workflow-specific outputs. The orchestrator records running/completed/failed execution, duration and summarized input/output. Database operational errors receive one retry. Other failures are returned as structured errors. Failed retrieval can still produce an explicit insufficient-evidence response. Working context is cleared in `finally`.

| Agent | Inputs | Outputs and responsibility |
|---|---|---|
| Memory Encoding | filename, bytes, quality, source date | validated extraction, chunks, concept terms, record IDs; duplicate document detection |
| Memory Retrieval | question, top-k, category/status filters | hybrid ranked evidence and recent context |
| Memory Consolidation | account memories | shared-concept links; original records are retained |
| Evidence Updating | new IDs or full account scan | possible polarity conflicts and age review flags; no automatic content overwrite |
| Clinical Reasoning | question and retrieved evidence | deterministic source-linked extractive explanation and limitations |
| Memory Evaluation | labeled queries, top-k | actual precision/recall, duplicate/outdated/conflicting counts |

## Adaptive memory

| Memory | Implementation |
|---|---|
| Short-Term | Persistent recent queries and retrieved IDs, session tagged; archived after 24 hours on the next query |
| Long-Term | Persistent ingested evidence chunks |
| Semantic | Structured concept vocabulary and categorized facts; entities also extracted from long-term chunks |
| Episodic | Document ingestion and evidence-screening events |
| Working | Evidence staged during the active task and removed when the task ends |

Each logical memory module uses the shared, user-scoped store. Category detection uses a transparent small clinical term dictionary, not a clinical NER model. The status lifecycle supports Active, Recently Updated, Outdated, Conflicting, Archived and Pending Review. Creation and every content/status edit produce a version. Original evidence excerpts remain separately stored. Explicit supersession requires a human-selected replacement and rationale; chronological age alone only creates a review flag.

## Retrieval and explanations

The default encoder is local character TF-IDF (3–5 character n-grams). Cosine similarity is combined with keyword overlap, uploader-assigned evidence quality and a small recency component. Formula: `0.70 similarity + 0.20 keyword overlap + 0.06 quality + 0.04 recency`. A minimum text relevance gate prevents quality or recency alone from selecting unrelated evidence. Archived records are excluded. Conflicting evidence remains retrievable and visibly labeled. The index is rebuilt from current account records per query, so edits take effect immediately and no stale on-disk index must be synchronized.

This is lexical similarity, not a validated medical semantic model. Optional Sentence Transformers support uses only an already cached `all-MiniLM-L6-v2` model when `CLINMEM_EMBEDDINGS=sentence-transformers`; install `sentence-transformers` separately. No model is downloaded automatically. If unavailable, TF-IDF is used. Large corpora will require a persisted vector index and stronger entity extraction.

Answers quote retrieved content with actual memory IDs, source names, page numbers where extracted, quality and status. They provide no additional medical facts. Relevance scores are ranking indicators, not calibrated clinical confidence. Recent user questions are context and never promoted to evidence. No paid API or generative language model is required.

## UI and features

The dark navy and teal Streamlit UI provides all 16 requested pages: overview, assistant, upload, explorer, five memory views, evidence updating, version history, knowledge graph, agent monitor, evaluation, reports and settings. Plotly visualizes memory composition, lifecycle and the NetworkX graph. A node selector shows graph provenance and neighboring relationships. Shared-term links are explicitly marked inferred, and potential contradictions are review findings.

PDF/TXT/DOCX/CSV extraction includes DOCX table text. PDF pages retain real page numbers; DOCX/TXT/CSV page references are absent. Files are limited to 20 MB. Scanned PDFs require external OCR. Original upload bytes are not retained: extracted content, source metadata and document hashes are persisted. Exact duplicate uploads are skipped per account. Identical content from different sources is retained to preserve provenance.

Reports download PDF, CSV and JSON. PDF reports include a selected analysis, retrieved IDs, memory evidence, provenance, status, version history, conflicts, agent activity and limitations. PDF generation escapes markup. Standard PDF fonts have limited non-Latin coverage; source records and CSV/JSON retain Unicode.

## Example use

1. Create an account and sign in.
2. In Settings, choose **Load clearly labeled synthetic demonstration**. Repeated loads skip identical source records.
3. Ask “diabetes glucose intervention alpha” in the assistant. Both fictional, opposing sources are available and marked for review.
4. Inspect their original evidence and versions in Memory Explorer.
5. Upload `data/sample_clinical_knowledge.txt` and then `data/sample_updated_evidence.txt`.
6. In Evidence Updating Center, review versions and explicitly record supersession if justified. No automatic overwrite occurs.
7. Inspect graph edges, run the synthetic labeled benchmark, and download a report.

## Evaluation and tests

```powershell
python -m compileall -q .
pytest -v
```

Tests exercise registration and bcrypt authentication, logout, arbitrary long passwords, account isolation, TXT/CSV/DOCX/PDF extraction, malformed files, exact duplicate handling, categorization, retrieval ranking and abstention, graph links, consolidation, age flags, conflict preservation, versions, orchestration cleanup, failure isolation, labeled metrics, PDF generation and authenticated page rendering. Pytest uses `.pytest_tmp` within the project for sandbox compatibility. Tests use temporary databases and do not change the application database.

`data/evaluation_queries.json` contains synthetic questions with source labels. The evaluation page resolves labels to actual account memory IDs and calculates precision over returned results and recall over labeled relevant records. Queries with no available labeled source are omitted and no scores are fabricated. These small synthetic results are demonstrations, not validated clinical performance.

## Folder structure

```text
ClinMem_AI/
├── app.py, requirements.txt, README.md, pytest.ini, .env.example, .gitignore
├── .streamlit/config.toml
├── config/settings.py
├── backend/
│   ├── authentication/auth.py
│   ├── database/{db_connection,models,db_operations}.py
│   ├── ingestion/{document_loader,text_processor,chunking}.py
│   ├── memory/{short_term_memory,long_term_memory,semantic_memory,
│   │           episodic_memory,working_memory,memory_manager,
│   │           memory_consolidation,memory_versioning}.py
│   ├── agents/{memory_encoding_agent,memory_retrieval_agent,
│   │           memory_consolidation_agent,evidence_updating_agent,
│   │           clinical_reasoning_agent,memory_evaluation_agent}.py
│   ├── retrieval/{embeddings,vector_store,hybrid_retriever}.py
│   ├── knowledge_graph/graph_manager.py
│   ├── orchestration/orchestrator.py
│   ├── evaluation/metrics.py
│   ├── generative_ai/response_generator.py
│   └── reports/pdf_generator.py
├── frontend/{dashboard,components,styles}.py
├── data/{sample_clinical_knowledge.txt,sample_updated_evidence.txt,
│         sample_evidence.json,evaluation_queries.json}
├── uploads/, vector_store/, reports/
└── tests/{conftest,test_auth,test_memory,test_ingestion,test_retrieval,
           test_agents,test_updating,test_evaluation,test_reports,test_dashboard}.py
```

The three output directories are available for future storage; current exports are generated in memory. SQLite is the authoritative memory store. Dependencies include Streamlit, SQLAlchemy, Pandas, NumPy, scikit-learn, NetworkX, Pydantic, Plotly, bcrypt, ReportLab, pytest, dotenv, python-docx and pypdf.

## Limitations and future work

Conflict detection is a shared-entity and negation heuristic: it can flag unrelated contexts and miss numerical, temporal and nuanced contradictions. Source dates are supplied by users, source quality is unverified, no live guideline feeds are queried, and clinical causality is never inferred. Memory categories use a small vocabulary. Reasoning is extractive, not model-based synthesis. Consolidation links records instead of merging potentially meaningful differences. Evaluation requires broader human-labeled corpora before any scientific performance claim.

This local prototype has no password recovery, rate limiting, encrypted database, deployment hardening or regulated medical validation. Future work includes clinician-reviewed terminology, evidence retrieval benchmarks, context-aware contradiction models, persistent semantic indexes, encrypted storage, migrations, source-document retention, OCR and reviewed guideline updates. Do not deploy it as a medical decision engine.
