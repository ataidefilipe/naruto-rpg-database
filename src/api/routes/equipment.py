"""
Rotas para Consulta de Equipamentos: Armas, Armaduras e Selos de Fuinjutsu.
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from src.db.database import get_connection, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/equipment", tags=["Equipamentos & Fuinjutsu"])


@router.get("/weapons")
def list_weapons(
    categoria: Optional[str] = Query(None, description="Categoria (Simples, Marcial, Exótica)"),
    grupo: Optional[str] = Query(None, description="Grupo de arma (Lâmina, Mangal, Arma de Haste, etc.)"),
    propriedade: Optional[str] = Query(None, description="Propriedade mecânica (Leve, Sutil, Pesada, etc.)"),
    q: Optional[str] = Query(None, description="Busca textual por nome da arma"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta armas de Naruto 5e."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if categoria:
        conditions.append("categoria LIKE ?")
        params.append(f"%{categoria.strip()}%")
    if grupo:
        conditions.append("grupo_arma LIKE ?")
        params.append(f"%{grupo.strip()}%")
    if propriedade:
        conditions.append("propriedades LIKE ?")
        params.append(f"%{propriedade.strip()}%")
    if q:
        conditions.append("(nome LIKE ? OR propriedades LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM weapons WHERE {' AND '.join(conditions)} ORDER BY categoria, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


@router.get("/armors")
def list_armors(
    tipo: Optional[str] = Query(None, description="Tipo (Armadura Leve, Armadura Média, Armadura Pesada)"),
    min_ca: Optional[str] = Query(None, description="Bônus mínimo de CA"),
    q: Optional[str] = Query(None, description="Busca textual por nome da armadura"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta armaduras e escudos."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if tipo:
        conditions.append("tipo LIKE ?")
        params.append(f"%{tipo.strip()}%")
    if min_ca:
        conditions.append("bonus_ca >= ?")
        params.append(min_ca)
    if q:
        conditions.append("(nome LIKE ? OR efeito_especial LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM armors WHERE {' AND '.join(conditions)} ORDER BY tipo, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


@router.get("/fuinjutsu")
def list_fuinjutsu_seals(
    tipo_item: Optional[str] = Query(None, description="Item aplicável: Arma ou Armadura"),
    rank: Optional[str] = Query(None, description="Rank do selo (Rank-D a Rank-S)"),
    grau: Optional[str] = Query(None, description="Grau do selo (Menor, Padrão, Maior, Mestre, Supremo)"),
    max_ryo: Optional[int] = Query(None, description="Custo máximo em Ryo"),
    q: Optional[str] = Query(None, description="Busca textual por nome ou efeito mecânico"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta os 139 selos de Fuinjutsu de aprimoramento."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if tipo_item:
        conditions.append("tipo_item = ?")
        params.append(tipo_item)
    if rank:
        conditions.append("rank LIKE ?")
        params.append(f"%{rank.strip()}%")
    if grau:
        conditions.append("grau_selo LIKE ?")
        params.append(f"%{grau.strip()}%")
    if max_ryo is not None:
        conditions.append("custo_ryo <= ?")
        params.append(max_ryo)
    if q:
        conditions.append("(nome LIKE ? OR efeito_mecanico LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM fuinjutsu_seals WHERE {' AND '.join(conditions)} ORDER BY rank, custo_ryo, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results
