"""
Script de Saneamento e Normalização de Vínculos de Clãs.
Corrige divergências de digitação e formatação de cabeçalhos nos campos 'cla' de jutsus e linhagens latentes.
"""

import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "data/naruto5e.db"


def run_cleanup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("Iniciando normalização de vínculos de Clãs...")
    print("=" * 60)

    # 1. Correções na tabela jutsus
    jutsu_corrections = [
        ("Hyuga", "Hyūga"),
        ("Yamanaka De", "Yamanaka"),
        ("Nara De", "Nara"),
        ("Fuma Prever", "Fuma"),
        ("Uzumaki Jutsu", "Uzumaki"),
        ("Dos Humanos", "Humanos Sintéticos"),
    ]

    total_jutsus_fixed = 0
    for old_name, new_name in jutsu_corrections:
        cursor.execute("UPDATE jutsus SET cla = ? WHERE cla = ?", (new_name, old_name))
        count = cursor.rowcount
        total_jutsus_fixed += count
        if count > 0:
            print(f"  [jutsus] '{old_name}' -> '{new_name}': {count} registros corrigidos.")

    # 2. Correções na tabela latent_bloodlines
    latent_corrections = [
        ("Hyuga", "Hyūga"),
        ("Jugo", "Jūgo"),
        ("Yonton", "Yoton"),
        ("Humano Sintético", "Humanos Sintéticos"),
    ]

    total_latent_fixed = 0
    for old_name, new_name in latent_corrections:
        cursor.execute("UPDATE latent_bloodlines SET cla = ? WHERE cla = ?", (new_name, old_name))
        count = cursor.rowcount
        total_latent_fixed += count
        if count > 0:
            print(f"  [latent_bloodlines] '{old_name}' -> '{new_name}': {count} registros corrigidos.")

    conn.commit()

    # 3. Verificação de integridade referencial
    cursor.execute("""
        SELECT DISTINCT j.cla 
        FROM jutsus j 
        WHERE j.cla IS NOT NULL AND j.cla != '' 
          AND j.cla NOT IN (SELECT nome FROM clans)
    """)
    orphan_jutsus = cursor.fetchall()

    cursor.execute("""
        SELECT DISTINCT l.cla 
        FROM latent_bloodlines l 
        WHERE l.cla IS NOT NULL AND l.cla != '' 
          AND l.cla NOT IN (SELECT nome FROM clans)
    """)
    orphan_latent = cursor.fetchall()

    conn.close()

    print("-" * 60)
    print(f"Total de jutsus atualizados: {total_jutsus_fixed}")
    print(f"Total de linhagens latentes atualizadas: {total_latent_fixed}")
    print(f"Jutsus sem clã correspondente na tabela clans: {[r[0] for r in orphan_jutsus]}")
    print(f"Latentes sem clã correspondente na tabela clans: {[r[0] for r in orphan_latent]}")
    print("=" * 60)
    print("Saneamento concluído com sucesso!")


if __name__ == "__main__":
    run_cleanup()
