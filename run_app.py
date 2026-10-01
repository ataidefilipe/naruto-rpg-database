"""
Script de Inicialização do Painel Naruto 5e (Backend FastAPI + Frontend SPA).
Executa o servidor local e abre o navegador automaticamente.
"""

import sys
import os
import webbrowser
import threading
import time
import uvicorn

sys.stdout.reconfigure(encoding='utf-8')


def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://localhost:8000")


def main():
    print("=" * 65)
    print("🍃 INICIANDO NARUTO 5E DATABASE — PAINEL TÁTICO RPG")
    print("=" * 65)
    print("📍 Frontend SPA:         http://localhost:8000")
    print("📘 Swagger API Docs:     http://localhost:8000/docs")
    print("⚙️  Banco de Dados:       data/naruto5e.db (1.677 Jutsus, 45 Clãs)")
    print("=" * 65)
    print("Pressione CTRL+C para encerrar o servidor.")
    print("-" * 65)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
