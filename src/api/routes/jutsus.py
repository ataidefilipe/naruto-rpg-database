"""
Rotas para Consulta e Filtragem Massiva do Compêndio Unificado de Jutsus.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import json
from src.db.database import get_connection, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/jutsus", tags=["Jutsus"])

RANK_ORDER_MAP = {
    "Rank-E": 1,
    "Rank-D": 2,
    "Rank-C": 3,
    "Rank-B": 4,
    "Rank-A": 5,
    "Rank-S": 6
}


@router.get("")
def list_jutsus(
    q: Optional[str] = Query(None, description="Busca textual livre em nome ou descrição mecânica"),
    rank: Optional[str] = Query(None, description="Ranks separados por vírgula (ex: Rank-D,Rank-C)"),
    natureza: Optional[str] = Query(None, description="Naturezas/Estilos separados por vírgula (ex: Fogo,Vento)"),
    classificacao: Optional[str] = Query(None, description="Classificações separadas por vírgula (Ninjutsu, Taijutsu, Genjutsu, Bukijutsu)"),
    cla: Optional[str] = Query(None, description="Nome do clã"),
    apenas_cla: Optional[bool] = Query(None, description="Filtrar apenas jutsus exclusivos de clã"),
    apenas_gerais: Optional[bool] = Query(None, description="Filtrar apenas jutsus gerais (sem clã)"),
    min_chakra: Optional[int] = Query(None, description="Custo mínimo de chakra"),
    max_chakra: Optional[int] = Query(None, description="Custo máximo de chakra"),
    tempo_conjuracao: Optional[str] = Query(None, description="Tempo de ação (ex: 1 Ação, 1 Ação Bônus, 1 Reação)"),
    alcance: Optional[str] = Query(None, description="Filtro por alcance"),
    duracao: Optional[str] = Query(None, description="Filtro por duração"),
    componentes: Optional[str] = Query(None, description="Componente requerido (SM, FN, MC)"),
    dano_tipo: Optional[str] = Query(None, description="Tipos de dano separados por vírgula"),
    salvaguarda: Optional[str] = Query(None, description="Atributos de salvaguarda separados por vírgula"),
    condicao: Optional[str] = Query(None, description="Condição de status aplicada (ex: Queimado, Cego)"),
    palavra_chave: Optional[str] = Query(None, description="Palavra-chave (ex: Conflito, Fuinjutsu, Hijutsu)"),
    possui_vantagem: Optional[bool] = Query(None, description="Apenas jutsus que concedem vantagem/desvantagem"),
    possui_upcast: Optional[bool] = Query(None, description="Apenas jutsus com escalonamento (upcasting)"),
    sort_by: str = Query("rank_asc", description="Ordenação: nome_asc, nome_desc, chakra_asc, chakra_desc, rank_asc, rank_desc"),
    limit: int = Query(50, ge=0, le=2000, description="Limite de registros (0 = todos)"),
    offset: int = Query(0, ge=0, description="Offset de paginação"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta jutsus com filtros combinados massivos."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions_sql = ["1=1"]
    params = []

    if q:
        q_clean = f"%{q.strip()}%"
        conditions_sql.append("(nome LIKE ? OR efeito_mecanico LIKE ? OR palavras_chave LIKE ?)")
        params.extend([q_clean, q_clean, q_clean])

    if rank:
        ranks_list = [r.strip() for r in rank.split(",") if r.strip()]
        if ranks_list:
            placeholders = ",".join("?" for _ in ranks_list)
            conditions_sql.append(f"rank IN ({placeholders})")
            params.extend(ranks_list)

    if natureza:
        nats_list = [n.strip() for n in natureza.split(",") if n.strip()]
        if nats_list:
            sub = " OR ".join("natureza_estilo LIKE ?" for _ in nats_list)
            conditions_sql.append(f"({sub})")
            params.extend([f"%{n}%" for n in nats_list])

    if classificacao:
        classes_list = [c.strip() for c in classificacao.split(",") if c.strip()]
        if classes_list:
            placeholders = ",".join("?" for _ in classes_list)
            conditions_sql.append(f"classificacao IN ({placeholders})")
            params.extend(classes_list)

    if cla:
        conditions_sql.append("cla LIKE ?")
        params.append(f"%{cla.strip()}%")

    if apenas_cla is True:
        conditions_sql.append("exclusivo_cla = 1")
    elif apenas_gerais is True:
        conditions_sql.append("(cla IS NULL OR cla = '')")

    if min_chakra is not None:
        conditions_sql.append("custo_chakra >= ?")
        params.append(min_chakra)

    if max_chakra is not None:
        conditions_sql.append("custo_chakra <= ?")
        params.append(max_chakra)

    if tempo_conjuracao:
        conditions_sql.append("tempo_conjuracao LIKE ?")
        params.append(f"%{tempo_conjuracao.strip()}%")

    if alcance:
        conditions_sql.append("alcance LIKE ?")
        params.append(f"%{alcance.strip()}%")

    if duracao:
        conditions_sql.append("duracao LIKE ?")
        params.append(f"%{duracao.strip()}%")

    if componentes:
        conditions_sql.append("componentes LIKE ?")
        params.append(f"%{componentes.strip()}%")

    if dano_tipo:
        dmg_list = [d.strip() for d in dano_tipo.split(",") if d.strip()]
        if dmg_list:
            sub = " OR ".join("dano_tipo LIKE ?" for _ in dmg_list)
            conditions_sql.append(f"({sub})")
            params.extend([f"%{d}%" for d in dmg_list])

    if salvaguarda:
        saves_list = [s.strip() for s in salvaguarda.split(",") if s.strip()]
        if saves_list:
            sub = " OR ".join("salvaguarda LIKE ?" for _ in saves_list)
            conditions_sql.append(f"({sub})")
            params.extend([f"%{s}%" for s in saves_list])

    if condicao:
        conditions_sql.append("condicoes LIKE ?")
        params.append(f"%{condicao.strip()}%")

    if palavra_chave:
        conditions_sql.append("palavras_chave LIKE ?")
        params.append(f"%{palavra_chave.strip()}%")

    if possui_vantagem is True:
        conditions_sql.append("(vantagem_desvantagem IS NOT NULL AND vantagem_desvantagem != '')")

    if possui_upcast is True:
        conditions_sql.append("(em_niveis_mais_altos IS NOT NULL AND em_niveis_mais_altos != '')")

    where_clause = " AND ".join(conditions_sql)

    # 1. Total Count
    cursor.execute(f"SELECT COUNT(1) FROM jutsus WHERE {where_clause}", params)
    total_count = cursor.fetchone()[0]

    # 2. Ordenação
    order_clause = "CASE rank WHEN 'Rank-E' THEN 1 WHEN 'Rank-D' THEN 2 WHEN 'Rank-C' THEN 3 WHEN 'Rank-B' THEN 4 WHEN 'Rank-A' THEN 5 WHEN 'Rank-S' THEN 6 ELSE 7 END, custo_chakra, nome"
    if sort_by == "nome_asc":
        order_clause = "nome ASC"
    elif sort_by == "nome_desc":
        order_clause = "nome DESC"
    elif sort_by == "chakra_asc":
        order_clause = "custo_chakra ASC, nome ASC"
    elif sort_by == "chakra_desc":
        order_clause = "custo_chakra DESC, nome ASC"
    elif sort_by == "rank_desc":
        order_clause = "CASE rank WHEN 'Rank-S' THEN 1 WHEN 'Rank-A' THEN 2 WHEN 'Rank-B' THEN 3 WHEN 'Rank-C' THEN 4 WHEN 'Rank-D' THEN 5 WHEN 'Rank-E' THEN 6 ELSE 7 END, custo_chakra DESC, nome ASC"

    # 3. Query com Paginação
    query_sql = f"SELECT * FROM jutsus WHERE {where_clause} ORDER BY {order_clause}"
    if limit > 0:
        query_sql += f" LIMIT {limit} OFFSET {offset}"

    cursor.execute(query_sql, params)
    rows = cursor.fetchall()

    items = []
    for r in rows:
        d = dict(r)
        d["componentes"] = json.loads(d["componentes"])
        d["palavras_chave"] = json.loads(d["palavras_chave"])
        d["condicoes"] = json.loads(d["condicoes"])
        d["exclusivo_cla"] = bool(d["exclusivo_cla"])
        items.append(d)

    conn.close()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@router.get("/{jutsu_id}")
def get_jutsu(jutsu_id: int, db_path: str = DEFAULT_DB_PATH):
    """Obtém detalhes completos de um jutsu por ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jutsus WHERE id = ?", (jutsu_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Jutsu {jutsu_id} não encontrado.")

    d = dict(row)
    d["componentes"] = json.loads(d["componentes"])
    d["palavras_chave"] = json.loads(d["palavras_chave"])
    d["condicoes"] = json.loads(d["condicoes"])
    d["exclusivo_cla"] = bool(d["exclusivo_cla"])
    return d
