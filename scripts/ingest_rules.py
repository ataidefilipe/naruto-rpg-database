"""
Script de ingestão para Equipamentos (Armas, Armaduras), Selos de Fuinjutsu,
Condições e Regras de Combate de Naruto 5e.
Fonte: PDFs/Regras Gerais.pdf -> Banco: data/naruto5e.db
"""

import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import (
    init_db,
    insert_armors,
    insert_weapons,
    insert_fuinjutsu_seals,
    insert_conditions,
    insert_combat_rules,
    get_connection
)
from src.extractor.rules_parser import parse_all_rules


def main():
    t0 = time.time()
    print("==================================================")
    print("Iniciando Ingestão de Regras Gerais e Equipamentos")
    print("==================================================")

    init_db()

    pdf_path = "PDFs/Regras Gerais.pdf"
    if not os.path.exists(pdf_path):
        print(f"ERRO: Arquivo {pdf_path} não encontrado!")
        sys.exit(1)

    print(f"Extraindo dados mecânicos de {pdf_path}...")
    rules_data = parse_all_rules(pdf_path)

    armors = rules_data['armors']
    weapons = rules_data['weapons']
    seals = rules_data['seals']
    conditions = rules_data['conditions']
    combat_rules = rules_data['combat_rules']

    print(f"Inserindo {len(armors)} armaduras e escudos no SQLite...")
    n_arm = insert_armors(armors, clear_first=True)

    print(f"Inserindo {len(weapons)} armas no SQLite...")
    n_wep = insert_weapons(weapons, clear_first=True)

    print(f"Inserindo {len(seals)} selos de Fuinjutsu no SQLite...")
    n_seal = insert_fuinjutsu_seals(seals, clear_first=True)

    print(f"Inserindo {len(conditions)} condições no SQLite...")
    n_cond = insert_conditions(conditions, clear_first=True)

    print(f"Inserindo {len(combat_rules)} regras de combate no SQLite...")
    n_rules = insert_combat_rules(combat_rules, clear_first=True)

    # Verificação no Banco
    conn = get_connection()
    c_cur = conn.cursor()
    c_cur.execute("SELECT COUNT(*) FROM armors")
    total_armors = c_cur.fetchone()[0]
    c_cur.execute("SELECT COUNT(*) FROM weapons")
    total_weapons = c_cur.fetchone()[0]
    c_cur.execute("SELECT COUNT(*) FROM fuinjutsu_seals")
    total_seals = c_cur.fetchone()[0]
    c_cur.execute("SELECT COUNT(*) FROM conditions")
    total_conditions = c_cur.fetchone()[0]
    c_cur.execute("SELECT COUNT(*) FROM combat_rules")
    total_combat_rules = c_cur.fetchone()[0]
    conn.close()

    t1 = time.time()
    print("\n--------------------------------------------------")
    print(f"Ingestão concluída com sucesso em {t1 - t0:.2f}s!")
    print(f"Armaduras & Escudos no banco: {total_armors}")
    print(f"Armas no banco:               {total_weapons}")
    print(f"Selos de Fuinjutsu no banco:  {total_seals}")
    print(f"Condições de Status no banco: {total_conditions}")
    print(f"Regras de Combate no banco:   {total_combat_rules}")
    print("------------------------------------------------==")


if __name__ == "__main__":
    main()
