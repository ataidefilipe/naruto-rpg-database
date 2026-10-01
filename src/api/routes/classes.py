"""
Rotas para Consulta de Classes, Tabelas de Nível 1 a 20, Arquétipos e Talentos.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import json
from src.db.database import get_connection, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/classes", tags=["Classes & Arquétipos"])


@router.get("")
def list_classes(
    tipo_conjurador: Optional[str] = Query(None, description="Grau de conjuração (Alto, Médio, Baixo)"),
    dado_vida: Optional[str] = Query(None, description="Dado de vida (ex: 1d6, 1d8, 1d10, 1d12)"),
    dado_chakra: Optional[str] = Query(None, description="Dado de chakra (ex: 1d8, 1d10, 1d12)"),
    q: Optional[str] = Query(None, description="Busca textual por nome da classe"),
    db_path: str = DEFAULT_DB_PATH
):
    """Lista as 11 classes de Naruto 5e."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if tipo_conjurador:
        conditions.append("tipo_conjurador = ?")
        params.append(tipo_conjurador)
    if dado_vida:
        conditions.append("dado_vida = ?")
        params.append(dado_vida)
    if dado_chakra:
        conditions.append("dado_chakra = ?")
        params.append(dado_chakra)
    if q:
        conditions.append("(nome LIKE ? OR nome_en LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT id, nome, nome_en, tipo_conjurador, dado_vida, dado_chakra, hp_primeiro_nivel, chakra_primeiro_nivel, testes_resistencia, pagina_inicio FROM classes WHERE {' AND '.join(conditions)} ORDER BY nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["testes_resistencia"] = json.loads(d["testes_resistencia"])
        results.append(d)

    conn.close()
    return results


@router.get("/{nome}")
def get_class_detail(nome: str, db_path: str = DEFAULT_DB_PATH):
    """Retorna detalhes completos da classe: ficha, tabela 1 a 20, habilidades, arquétipos e talentos."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM classes WHERE nome LIKE ? OR nome_en LIKE ?", (f"%{nome.strip()}%", f"%{nome.strip()}%"))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Classe '{nome}' não encontrada.")

    cls_dict = dict(row)
    cls_dict["testes_resistencia"] = json.loads(cls_dict["testes_resistencia"])
    cls_dict["tabela_progressao"] = json.loads(cls_dict["tabela_progressao"])
    cls_dict["caracteristicas_classe"] = json.loads(cls_dict["caracteristicas_classe"])
    cls_dict["recursos_customizacao"] = json.loads(cls_dict["recursos_customizacao"])

    # Arquétipos da classe
    cursor.execute("SELECT * FROM archetypes WHERE classe_nome = ? ORDER BY nivel_obtencao, nome", (cls_dict["nome"],))
    a_rows = cursor.fetchall()
    archetypes = []
    for r in a_rows:
        d = dict(r)
        d["caracteristicas"] = json.loads(d["caracteristicas"])
        archetypes.append(d)

    # Talentos da classe
    cursor.execute("SELECT * FROM class_talents WHERE classe = ? OR classe = 'Geral' ORDER BY tipo, nome", (cls_dict["nome"],))
    t_rows = cursor.fetchall()
    talents = [dict(r) for r in t_rows]

    conn.close()

    return {
        "classe": cls_dict,
        "arquetipos": archetypes,
        "talentos": talents
    }


@router.get("/sub/archetypes")
def list_archetypes(
    classe: Optional[str] = Query(None, description="Filtrar por classe mãe"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de arquétipo"),
    q: Optional[str] = Query(None, description="Busca textual por nome"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta os 74 arquétipos cadastrados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if classe:
        conditions.append("classe_nome LIKE ?")
        params.append(f"%{classe.strip()}%")
    if tipo:
        conditions.append("tipo_arquetipo LIKE ?")
        params.append(f"%{tipo.strip()}%")
    if q:
        conditions.append("(nome LIKE ? OR descricao_mecanica LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM archetypes WHERE {' AND '.join(conditions)} ORDER BY classe_nome, nivel_obtencao, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["caracteristicas"] = json.loads(d["caracteristicas"])
        results.append(d)

    conn.close()
    return results


@router.get("/sub/talents")
def list_talents(
    classe: Optional[str] = Query(None, description="Filtrar por classe"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (Arquétipo, Conjuntor, Marcial, Geral)"),
    q: Optional[str] = Query(None, description="Busca textual"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta os 75 talentos de classe."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if classe:
        conditions.append("(classe LIKE ? OR classe = 'Geral')")
        params.append(f"%{classe.strip()}%")
    if tipo:
        conditions.append("tipo LIKE ?")
        params.append(f"%{tipo.strip()}%")
    if q:
        conditions.append("(nome LIKE ? OR descricao_mecanica LIKE ? OR prerequisitos LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM class_talents WHERE {' AND '.join(conditions)} ORDER BY tipo, classe, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results
