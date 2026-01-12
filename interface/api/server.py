#!/usr/bin/env python3
"""
Servidor FastAPI para Chef Digital CBR API.
"""

import uvicorn

if __name__ == "__main__":
    # Ejecutar servidor en puerto 8000
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
