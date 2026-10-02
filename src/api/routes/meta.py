"""
Rota de Metadados e Valores Distintos para Alimentar Filtros Dinâmicos.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import json
from src.db.database import get_connection, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/meta", tags=["Metadados"])


@router.get("/filters", response_model=Dict[str, Any])
def get_all_filter_options(db_path: str = DEFAULT_DB_PATH):
    """Retorna todas as opções e listas de valores únicos para alimentar os filtros do frontend."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Ranks de Jutsus
    ranks = ["Rank-E", "Rank-D", "Rank-C", "Rank-B", "Rank-A", "Rank-S"]

    # 2. Naturezas / Estilos
    cursor.execute("""
        SELECT DISTINCT natureza_estilo FROM jutsus 
        WHERE natureza_estilo IS NOT NULL AND natureza_estilo != '' 
        ORDER BY natureza_estilo
    """)
    naturezas = [r[0] for r in cursor.fetchall()]

    # 3. Classificações
    cursor.execute("SELECT DISTINCT classificacao FROM jutsus WHERE classificacao IS NOT NULL ORDER BY classificacao")
    classificacoes = [r[0] for r in cursor.fetchall()]

    # 4. Clãs
    cursor.execute("SELECT DISTINCT nome FROM clans ORDER BY nome")
    clans = [r[0] for r in cursor.fetchall()]

    # 5. Salvaguardas
    salvaguardas = ["Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"]

    # 6. Tipos de Dano
    cursor.execute("""
        SELECT DISTINCT dano_tipo FROM jutsus 
        WHERE dano_tipo IS NOT NULL AND dano_tipo != '' AND dano_tipo != '-'
        ORDER BY dano_tipo
    """)
    dano_tipos = [r[0] for r in cursor.fetchall()]

    # 7. Condições
    cursor.execute("SELECT nome, categoria FROM conditions ORDER BY categoria, nome")
    condicoes = [dict(r) for r in cursor.fetchall()]

    # 8. Categorias e Grupos de Armas
    cursor.execute("SELECT DISTINCT categoria FROM weapons ORDER BY categoria")
    armas_categorias = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT grupo_arma FROM weapons WHERE grupo_arma != '' ORDER BY grupo_arma")
    armas_grupos = [r[0] for r in cursor.fetchall()]

    # 9. Tipos de Armaduras
    cursor.execute("SELECT DISTINCT tipo FROM armors ORDER BY tipo")
    armaduras_tipos = [r[0] for r in cursor.fetchall()]

    # 10. Selos de Fuinjutsu Ranks e Graus
    cursor.execute("SELECT DISTINCT rank FROM fuinjutsu_seals ORDER BY rank")
    selos_ranks = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT grau_selo FROM fuinjutsu_seals WHERE grau_selo IS NOT NULL ORDER BY grau_selo")
    selos_graus = [r[0] for r in cursor.fetchall()]

    # 11. Classes
    cursor.execute("SELECT id, nome, nome_en, tipo_conjurador, dado_vida, dado_chakra FROM classes ORDER BY nome")
    classes_lista = [dict(r) for r in cursor.fetchall()]

    # 12. Contadores Globais
    contadores = {}
    for tbl in ["jutsus", "clans", "latent_bloodlines", "classes", "archetypes", "class_talents", "weapons", "armors", "fuinjutsu_seals", "conditions", "combat_rules", "error_reports"]:
        cursor.execute(f"SELECT COUNT(1) FROM {tbl}")
        contadores[tbl] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(1) FROM error_reports WHERE status = 'pendente'")
    contadores["pending_reports"] = cursor.fetchone()[0]

    conn.close()

    return {
        "jutsus": {
            "ranks": ranks,
            "naturezas": naturezas,
            "classificacoes": classificacoes,
            "clans": clans,
            "salvaguardas": salvaguardas,
            "dano_tipos": dano_tipos,
            "tempos_conjuracao": ["1 Ação", "1 Ação Bônus", "1 Reação", "Especial"]
        },
        "condicoes": condicoes,
        "equipamentos": {
            "armas_categorias": armas_categorias,
            "armas_grupos": armas_grupos,
            "armaduras_tipos": armaduras_tipos,
            "selos_ranks": selos_ranks,
            "selos_graus": selos_graus,
            "selos_tipos_item": ["Arma", "Armadura"]
        },
        "classes": classes_lista,
        "contadores": contadores
    }


@router.get("/counts", response_model=Dict[str, int])
def get_table_counts(db_path: str = DEFAULT_DB_PATH):
    """Retorna a contagem exata e atualizada de registros de todas as tabelas."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    contadores = {}
    for tbl in ["jutsus", "clans", "latent_bloodlines", "classes", "archetypes", "class_talents", "weapons", "armors", "fuinjutsu_seals", "conditions", "combat_rules", "error_reports"]:
        cursor.execute(f"SELECT COUNT(1) FROM {tbl}")
        contadores[tbl] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(1) FROM error_reports WHERE status = 'pendente'")
    contadores["pending_reports"] = cursor.fetchone()[0]
    conn.close()
    return contadores

