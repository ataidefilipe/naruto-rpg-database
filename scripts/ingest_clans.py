import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import init_db, insert_clans, insert_latent_bloodlines, DEFAULT_DB_PATH
from src.extractor.clan_parser import parse_all_clans, parse_all_latent_bloodlines


def main():
    print("=" * 60)
    print("🧬 INGESTÃO DE CLÃS & LINHAGENS LATENTES — NARUTO 5E")
    print("=" * 60)

    db_path = DEFAULT_DB_PATH
    init_db(db_path)

    start_time = time.time()
    pdf_clas = "PDFs/Clas.pdf"

    # 1. Ingestão dos Clãs
    print(f"\n[1/2] Extraindo os 45 Clãs de {pdf_clas}...")
    clans = parse_all_clans(pdf_clas)
    ins_clans = insert_clans(clans, db_path, clear_first=True)
    print(f" -> Sucesso: {ins_clans} clãs salvos no banco SQLite!")

    # 2. Ingestão das Linhagens Latentes
    print(f"\n[2/2] Extraindo Linhagens Sanguíneas Latentes (pág. 273 a 314)...")
    latent_traits = parse_all_latent_bloodlines(pdf_clas)
    ins_latent = insert_latent_bloodlines(latent_traits, db_path, clear_first=True)
    print(f" -> Sucesso: {ins_latent} habilidades latentes salvas no banco SQLite!")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"✅ Ingestão de Clãs concluída com sucesso em {elapsed:.1f} segundos!")
    print(f"📊 {ins_clans} Clãs e {ins_latent} Habilidades Latentes integrados ao banco!")
    print("=" * 60)


if __name__ == "__main__":
    main()
