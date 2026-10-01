"""
Rotas para Consulta de Condições de Status, Regras de Combate e Calculadora de Clash.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import json
from src.db.database import get_connection, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/rules", tags=["Regras & Combate"])

ELEMENTAL_CYCLE = {
    "Fogo": "Vento",
    "Vento": "Relâmpago",
    "Relâmpago": "Terra",
    "Terra": "Água",
    "Água": "Fogo"
}

RANK_BONUS = {
    "Rank-E": 0,
    "Rank-D": 1,
    "Rank-C": 2,
    "Rank-B": 3,
    "Rank-A": 4,
    "Rank-S": 5
}


class ClashRequest(BaseModel):
    elemento_a: Optional[str] = Field(None, description="Elemento do combatente A (Fogo, Vento, Relâmpago, Terra, Água ou Outro)")
    rank_a: str = Field("Rank-C", description="Rank da técnica de A (Rank-E a Rank-S)")
    chakra_extra_a: int = Field(0, ge=0, description="Chakra adicional investido por A além do custo base")
    
    elemento_b: Optional[str] = Field(None, description="Elemento do combatente B")
    rank_b: str = Field("Rank-C", description="Rank da técnica de B")
    chakra_extra_b: int = Field(0, ge=0, description="Chakra adicional investido por B além do custo base")


@router.get("/conditions")
def list_conditions(
    categoria: Optional[str] = Query(None, description="Categoria: Elemental, Físico, Mental, Sensorial, Geral"),
    q: Optional[str] = Query(None, description="Busca textual"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta as 31 condições de status e suas regras de graus."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if categoria:
        conditions.append("categoria LIKE ?")
        params.append(f"%{categoria.strip()}%")
    if q:
        conditions.append("(nome LIKE ? OR descricao_mecanica LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM conditions WHERE {' AND '.join(conditions)} ORDER BY categoria, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


@router.get("/combat")
def list_combat_rules(
    chave: Optional[str] = Query(None, description="Identificador da regra (superioridade_elemental, confronto_clash, leia_inimigo)"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta regras centrais de combate de Naruto 5e."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if chave:
        conditions.append("chave LIKE ?")
        params.append(f"%{chave.strip()}%")

    query = f"SELECT * FROM combat_rules WHERE {' AND '.join(conditions)} ORDER BY id"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["dados_estruturados"] = json.loads(d["dados_estruturados"])
        results.append(d)

    conn.close()
    return results


@router.post("/clash-calculator")
def calculate_clash(req: ClashRequest):
    """
    Calculadora e Simulador de Regras de Conflito de Jutsu (Clash Mechanics, p. 170).
    Calcula bônus de rank, bônus de chakra extra e vantagem elemental.
    """
    bonus_a = RANK_BONUS.get(req.rank_a, 0) + req.chakra_extra_a
    bonus_b = RANK_BONUS.get(req.rank_b, 0) + req.chakra_extra_b

    vantagem_a = False
    vantagem_b = False
    motivo_vantagem = "Nenhum elemento superior no confronto."

    if req.elemento_a and req.elemento_b:
        if ELEMENTAL_CYCLE.get(req.elemento_a) == req.elemento_b:
            vantagem_a = True
            motivo_vantagem = f"{req.elemento_a} é SUPERIOR a {req.elemento_b}. Combatente A rola o teste contestado com VANTAGEM!"
        elif ELEMENTAL_CYCLE.get(req.elemento_b) == req.elemento_a:
            vantagem_b = True
            motivo_vantagem = f"{req.elemento_b} é SUPERIOR a {req.elemento_a}. Combatente B rola o teste contestado com VANTAGEM!"

    melhor_de_3 = req.rank_a in ["Rank-B", "Rank-A", "Rank-S"] or req.rank_b in ["Rank-B", "Rank-A", "Rank-S"]

    return {
        "combatente_a": {
            "rank": req.rank_a,
            "bonus_rank": RANK_BONUS.get(req.rank_a, 0),
            "chakra_extra": req.chakra_extra_a,
            "bonus_total_adicional": bonus_a,
            "tem_vantagem": vantagem_a
        },
        "combatente_b": {
            "rank": req.rank_b,
            "bonus_rank": RANK_BONUS.get(req.rank_b, 0),
            "chakra_extra": req.chakra_extra_b,
            "bonus_total_adicional": bonus_b,
            "tem_vantagem": vantagem_b
        },
        "analise_elemental": motivo_vantagem,
        "melhor_de_3_obrigatorio": melhor_de_3,
        "penalidade_perdedor": [
            "Técnica dissipada imediatamente sem causar efeitos",
            "Condição Incapacitado até o final do próximo turno",
            "Sofre 1 grau da condição Concussão"
        ]
    }
