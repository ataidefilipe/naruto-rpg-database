"""
Aplicação Principal FastAPI — Naruto 5e Database.
Executa servidor REST local sem autenticação e serve a interface SPA.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import jutsus, clans, classes, equipment, rules, meta, auth, reports
from src.db.database import ensure_tables

# Garante criação das tabelas de usuários e erros na inicialização
ensure_tables()

app = FastAPI(
    title="🍃 Naruto 5e Database API",
    description="API REST local e analítica com filtros massivos, autenticação simples e reporte de erros para o sistema Naruto 5e RPG.",
    version="1.1.0"
)

# CORS totalmente liberado para facilidade de uso pessoal e local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos Roteadores da API
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(meta.router)
app.include_router(jutsus.router)
app.include_router(clans.router)
app.include_router(classes.router)
app.include_router(equipment.router)
app.include_router(rules.router)

# Caminhos para o Frontend
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_frontend():
    """Serve a aplicação SPA Vue 3."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "🍃 Naruto 5e Database API ativa. Acesse /docs para explorar os endpoints."}


@app.get("/api")
def api_status():
    """Status da API e contadores rápidos."""
    return {
        "status": "online",
        "sistema": "Naruto 5e RPG",
        "docs_url": "/docs",
        "frontend_url": "/"
    }
