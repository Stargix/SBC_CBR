# Chef Digital CBR API

FastAPI backend para el sistema CBR con datos de embeddings UMAP.

## Instalación y Ejecución

Desde la raíz del proyecto `CBR/`:

```bash
# Instalar dependencias (incluye FastAPI, uvicorn, etc.)
pip install -r ../../requirements.txt

# Ejecutar servidor
cd interface/api
python server.py
# O alternativamente:
uvicorn api.app:app --reload --port 8000
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
- Synthetic endpoint uses `simulation/llm_simulator.py` and needs `GROQ_API_KEY` plus `groq` package.
- Load environment variables from `.env` in project root.
