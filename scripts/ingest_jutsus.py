import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import init_db, insert_jutsus, DEFAULT_DB_PATH
from src.extractor.jutsu_parser import parse_jutsus_from_pdf


def main():
    print("=" * 60)
    print("🍃 INGESTÃO COMPLETA DE JUTSUS — NARUTO 5E DATABASE")
    print("=" * 60)

    db_path = DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    init_db(db_path)

    start_time = time.time()

    # 1. Ingestão de Jutsus Gerais (Jutsus.pdf)
    pdf_jutsus = "PDFs/Jutsus.pdf"
    print(f"\n[1/2] Lendo e extraindo {pdf_jutsus} (Compêndio Geral)...")
    jutsus_gerais = parse_jutsus_from_pdf(pdf_jutsus, is_clan_pdf=False)
    print(f" -> Sucesso: {len(jutsus_gerais)} jutsus gerais extraídos!")

    # 2. Ingestão de Jutsus de Clã (Clas.pdf)
    pdf_clas = "PDFs/Clas.pdf"
    print(f"\n[2/2] Lendo e extraindo {pdf_clas} (Técnicas Exclusivas de Clã)...")
    jutsus_clas = parse_jutsus_from_pdf(pdf_clas, is_clan_pdf=True)
    print(f" -> Sucesso: {len(jutsus_clas)} jutsus de clãs extraídos!")

    # 3. Inserção consolidada no SQLite
    total_jutsus = jutsus_gerais + jutsus_clas
    print(f"\nSalvando {len(total_jutsus)} jutsus unificados no banco SQLite ({db_path})...")
    inserted = insert_jutsus(total_jutsus, db_path, clear_first=True)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✅ Ingestão concluída com sucesso em {elapsed:.1f} segundos!")
    print(f"📊 Total consolidado de jutsus no banco: {inserted}")
    print("=" * 60)


if __name__ == "__main__":
    main()
