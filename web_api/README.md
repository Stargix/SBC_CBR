# Chef Digital CBR API

FastAPI backend for the CBR system and UMAP manifold data.

## Run

From `SBC_CBR`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r web_api/requirements.txt
uvicorn web_api.app:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `GET /cases` -> embeddings + case metadata
- `POST /request` -> run CBR with trace
- `POST /synthetic` -> run synthetic user (requires Groq dependencies)
- `POST /embeddings/transform` -> embed new cases using existing UMAP model

## Notes

- UMAP artifacts are stored in `develop/config/` (`umap_embeddings.json`, `umap_model.pkl`, `umap_feature_spec.pkl`).
- If artifacts are missing, the API will fit them from `initial_cases.json` on first call to `/cases`.
- Synthetic endpoint uses `simulation/groq_simulator.py` and needs `GROQ_API_KEY` plus `groq` package.
