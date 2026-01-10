# Chef Digital CBR - Web Interface

Sistema web completo para el CBR de Chef Digital con backend FastAPI y frontend React/Vite.

## 📁 Estructura

```
interface/
├── api/              # Backend FastAPI
│   ├── app.py        # Aplicación principal
│   ├── server.py     # Punto de entrada
│   ├── requirements.txt (deprecated - usar root)
│   └── README.md
│
└── web/              # Frontend React + Vite
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   ├── components/
    │   └── pages/
    ├── package.json
    └── vite.config.js
```

## 🚀 Inicio Rápido

### Backend (desde raíz del proyecto)
```bash
cd interface/api
python server.py
```

Servidor en `http://localhost:8000`

### Frontend (desde raíz del proyecto)
```bash
cd interface/web
npm install
npm run dev
```

Frontend en `http://localhost:5173`

## 📋 Requisitos

- Python 3.8+ (backend)
- Node.js 16+ (frontend)
- Dependencias en root `requirements.txt`

## 🔗 Integración

El frontend se conecta al backend en `http://localhost:8000/api` para:
- Recuperación de casos
- Ejecución del ciclo CBR
- Simulaciones con LLM
- Embeddings UMAP

## 📚 Documentación

- [Backend API](./api/README.md)
- [Frontend Architecture](./web/README.md) (si disponible)
