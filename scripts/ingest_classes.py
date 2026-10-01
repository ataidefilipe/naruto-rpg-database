"""
Script de ingestão para Classes, Progressão 1-20, Arquétipos e Talentos de Classe.
Fonte: PDFs/Classes.pdf -> Banco: data/naruto5e.db
"""

import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import (
    init_db,
    insert_classes,
    insert_archetypes,
    insert_class_talents,
    get_connection
)
from src.extractor.class_parser import parse_all_classes


def main():
    t0 = time.time()
    print("==================================================")
    print("Iniciando Ingestão de Classes, Arquétipos e Talentos")
    print("==================================================")

    init_db()

    pdf_path = "PDFs/Classes.pdf"
    if not os.path.exists(pdf_path):
        print(f"ERRO: Arquivo {pdf_path} não encontrado!")
        sys.exit(1)

    print(f"Extraindo dados de {pdf_path}...")
    classes, archetypes, talents = parse_all_classes(pdf_path)

    print(f"Inserindo {len(classes)} classes no SQLite...")
    n_cls = insert_classes(classes, clear_first=True)

    print(f"Inserindo {len(archetypes)} arquétipos no SQLite...")
    n_arch = insert_archetypes(archetypes, clear_first=True)

    print(f"Inserindo {len(talents)} talentos de classe no SQLite...")
    n_tal = insert_class_talents(talents, clear_first=True)

    conn = get_connection()
    c_cur = conn.cursor()
    c_cur.execute("SELECT COUNT(*) FROM classes")
    total_classes = c_cur.fetchone()[0]
    c_cur.execute("SELECT COUNT(*) FROM archetypes")
    total_archetypes = c_cur.fetchone()[0]
    c_cur.execute("SELECT COUNT(*) FROM class_talents")
    total_talents = c_cur.fetchone()[0]
    conn.close()

    t1 = time.time()
    print("\n--------------------------------------------------")
    print(f"Ingestão concluída com sucesso em {t1 - t0:.2f}s!")
    print(f"Total de Classes no banco: {total_classes}")
    print(f"Total de Arquétipos no banco: {total_archetypes}")
    print(f"Total de Talentos de Classe no banco: {total_talents}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
