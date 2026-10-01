"""
Script de normalização e padronização de dados em data/naruto5e.db.
Padroniza valores de Ranks e campos essenciais para consultas exatas.
"""

import sqlite3
import re


def normalize_database(db_path: str = "data/naruto5e.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Padronização de Ranks
    cur.execute("UPDATE jutsus SET rank = 'Rank-E' WHERE rank LIKE '%Rank%E%' OR rank = 'E'")
    cur.execute("UPDATE jutsus SET rank = 'Rank-D' WHERE rank LIKE '%Rank%D%' OR rank LIKE '%Nível D%' OR rank = 'D'")
    cur.execute("UPDATE jutsus SET rank = 'Rank-C' WHERE rank LIKE '%Rank%C%' OR rank = 'C'")
    cur.execute("UPDATE jutsus SET rank = 'Rank-B' WHERE rank LIKE '%Rank%B%' OR rank LIKE '%Nível B%' OR rank = 'B' OR rank LIKE '%: Rank B%'")
    cur.execute("UPDATE jutsus SET rank = 'Rank-A' WHERE rank LIKE '%Rank%A%' OR rank = 'A'")
    cur.execute("UPDATE jutsus SET rank = 'Rank-S' WHERE rank LIKE '%Rank%S%' OR rank = 'S'")

    # Para os poucos registros sem rank explícito, inferir a partir do texto mecânico ou custo
    cur.execute("SELECT id, efeito_mecanico, custo_chakra FROM jutsus WHERE rank NOT IN ('Rank-E', 'Rank-D', 'Rank-C', 'Rank-B', 'Rank-A', 'Rank-S')")
    rem = cur.fetchall()
    for m_id, desc, cost in rem:
        if 'Rank E' in desc or 'Rank-E' in desc:
            rk = 'Rank-E'
        elif 'Rank D' in desc or 'Rank-D' in desc:
            rk = 'Rank-D'
        elif 'Rank C' in desc or 'Rank-C' in desc:
            rk = 'Rank-C'
        elif 'Rank B' in desc or 'Rank-B' in desc:
            rk = 'Rank-B'
        elif 'Rank A' in desc or 'Rank-A' in desc:
            rk = 'Rank-A'
        elif 'Rank S' in desc or 'Rank-S' in desc:
            rk = 'Rank-S'
        else:
            # Fallback por custo de chakra
            if cost <= 2:
                rk = 'Rank-D'
            elif cost <= 5:
                rk = 'Rank-C'
            elif cost <= 9:
                rk = 'Rank-B'
            elif cost <= 14:
                rk = 'Rank-A'
            else:
                rk = 'Rank-S'
        cur.execute("UPDATE jutsus SET rank = ? WHERE id = ?", (rk, m_id))

    # 2. Padronização de Vínculos de Clãs em jutsus e latent_bloodlines
    jutsu_corrections = [
        ("Hyuga", "Hyūga"),
        ("Yamanaka De", "Yamanaka"),
        ("Nara De", "Nara"),
        ("Fuma Prever", "Fuma"),
        ("Uzumaki Jutsu", "Uzumaki"),
        ("Dos Humanos", "Humanos Sintéticos"),
    ]
    for old_name, new_name in jutsu_corrections:
        cur.execute("UPDATE jutsus SET cla = ? WHERE cla = ?", (new_name, old_name))

    latent_corrections = [
        ("Hyuga", "Hyūga"),
        ("Jugo", "Jūgo"),
        ("Yonton", "Yoton"),
        ("Humano Sintético", "Humanos Sintéticos"),
    ]
    for old_name, new_name in latent_corrections:
        cur.execute("UPDATE latent_bloodlines SET cla = ? WHERE cla = ?", (new_name, old_name))

    conn.commit()

    cur.execute("SELECT rank, COUNT(*) FROM jutsus GROUP BY rank ORDER BY rank")
    counts = cur.fetchall()
    print("Contagem padronizada de Ranks de Jutsus:")
    for r, c in counts:
        print(f"  {r:8s}: {c} jutsus")

    conn.close()


if __name__ == "__main__":
    normalize_database()
