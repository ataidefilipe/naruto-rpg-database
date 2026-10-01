"""
Rotas para Consulta de Clãs e Linhagens Sanguíneas Latentes.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import json
from src.db.database import get_connection, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/clans", tags=["Clãs & Linhagens"])


RANK_ORDER = ["Rank-E", "Rank-D", "Rank-C", "Rank-B", "Rank-A", "Rank-S"]


def parse_speed(raw: str):
    """Padroniza strings de deslocamento em formato legível e valor numérico em metros."""
    if not raw:
        return "9m (30 pés)", 9.0
    r = raw.lower().replace(",", ".")
    if "10.5" in r or "35" in r:
        return "10.5m (35 pés)", 10.5
    elif "5" in r and "10.5" not in r and "35" not in r:
        return "5m (15 pés)", 5.0
    else:
        return "9m (30 pés)", 9.0


@router.get("")
def list_clans(
    q: Optional[str] = Query(None, description="Busca textual por nome do clã"),
    atributo: Optional[str] = Query(None, description="Filtrar por atributo que recebe bônus"),
    pericia: Optional[str] = Query(None, description="Filtrar por perícia concedida"),
    db_path: str = DEFAULT_DB_PATH
):
    """Lista todos os clãs com filtros."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if q:
        conditions.append("nome LIKE ?")
        params.append(f"%{q.strip()}%")
    if atributo:
        conditions.append("aumento_atributos LIKE ?")
        params.append(f"%{atributo.strip()}%")
    if pericia:
        conditions.append("pericias LIKE ?")
        params.append(f"%{pericia.strip()}%")

    query = f"SELECT * FROM clans WHERE {' AND '.join(conditions)} ORDER BY nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["aumento_atributos"] = json.loads(d["aumento_atributos"])
        d["pericias"] = json.loads(d["pericias"])
        d["idiomas"] = json.loads(d["idiomas"])
        d["recursos"] = json.loads(d["recursos"])
        vel_str, vel_num = parse_speed(d.get("deslocamento", ""))
        d["deslocamento_formatado"] = vel_str
        d["deslocamento_metros"] = vel_num
        results.append(d)

    conn.close()
    return results


@router.get("/compare/summary")
def get_clans_comparison_summary(db_path: str = DEFAULT_DB_PATH):
    """Retorna a matriz resumida de todos os 45 clãs com métricas de jutsus, linhagens e recursos para comparação."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.id, c.nome, c.aumento_atributos, c.aumento_atributos_raw, c.deslocamento, c.pericias, c.recursos, c.pagina,
            (SELECT COUNT(1) FROM jutsus WHERE cla = c.nome) as total_jutsus,
            (SELECT GROUP_CONCAT(DISTINCT rank) FROM jutsus WHERE cla = c.nome) as ranks_jutsus_raw,
            (SELECT GROUP_CONCAT(DISTINCT natureza_estilo) FROM jutsus WHERE cla = c.nome) as estilos_jutsus_raw,
            (SELECT COUNT(1) FROM latent_bloodlines WHERE cla = c.nome) as total_latentes,
            (SELECT MIN(custo_pontos) FROM latent_bloodlines WHERE cla = c.nome) as min_pts,
            (SELECT MAX(custo_pontos) FROM latent_bloodlines WHERE cla = c.nome) as max_pts
        FROM clans c
        ORDER BY c.nome
    """)
    rows = cursor.fetchall()
    conn.close()

    summary = []
    for r in rows:
        d = dict(r)
        attrs = json.loads(d["aumento_atributos"]) if d["aumento_atributos"] else {}
        pericias = json.loads(d["pericias"]) if d["pericias"] else []
        recursos_raw = json.loads(d["recursos"]) if d["recursos"] else []

        recursos_resumo = []
        for rec in recursos_raw:
            desc = rec.get("descricao", "")
            recursos_resumo.append({
                "nome": rec.get("nome", ""),
                "nivel": rec.get("nivel", 1),
                "usos": rec.get("usos"),
                "descricao_curta": (desc[:140] + "...") if len(desc) > 140 else desc
            })

        ranks_raw = d["ranks_jutsus_raw"].split(",") if d["ranks_jutsus_raw"] else []
        ranks_sorted = [rk for rk in RANK_ORDER if rk in ranks_raw]

        estilos = [e.strip() for e in (d["estilos_jutsus_raw"].split(",") if d["estilos_jutsus_raw"] else []) if e.strip() and e.strip() != "-"]

        vel_str, vel_num = parse_speed(d["deslocamento"])

        summary.append({
            "id": d["id"],
            "nome": d["nome"],
            "aumento_atributos": attrs,
            "aumento_atributos_raw": d["aumento_atributos_raw"],
            "deslocamento": vel_str,
            "deslocamento_metros": vel_num,
            "pericias": pericias,
            "total_recursos": len(recursos_raw),
            "recursos_resumo": recursos_resumo,
            "total_jutsus": d["total_jutsus"],
            "ranks_jutsus": ranks_sorted,
            "estilos_jutsus": estilos,
            "total_latentes": d["total_latentes"],
            "latentes_min_pontos": d["min_pts"],
            "latentes_max_pontos": d["max_pts"],
            "pagina": d["pagina"]
        })

    return summary


@router.get("/compare")
def compare_clans(
    names: str = Query(..., description="Nomes dos clãs a comparar separados por vírgula (ex: Uchiha,Hyūga,Senju)"),
    db_path: str = DEFAULT_DB_PATH
):
    """Retorna a ficha mecânica detalhada simultânea dos clãs solicitados para comparação lado a lado."""
    clan_names = [n.strip() for n in names.split(",") if n.strip()]
    if not clan_names:
        raise HTTPException(status_code=400, detail="Pelo menos um nome de clã deve ser fornecido.")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    results = []
    for name in clan_names:
        cursor.execute("SELECT * FROM clans WHERE nome LIKE ?", (f"%{name.strip()}%",))
        row = cursor.fetchone()
        if not row:
            continue

        clan = dict(row)
        clan["aumento_atributos"] = json.loads(clan["aumento_atributos"]) if clan["aumento_atributos"] else {}
        clan["pericias"] = json.loads(clan["pericias"]) if clan["pericias"] else []
        clan["idiomas"] = json.loads(clan["idiomas"]) if clan["idiomas"] else []
        clan["recursos"] = json.loads(clan["recursos"]) if clan["recursos"] else []
        vel_str, vel_num = parse_speed(clan.get("deslocamento", ""))
        clan["deslocamento_formatado"] = vel_str
        clan["deslocamento_metros"] = vel_num

        # Jutsus exclusivos
        cursor.execute("SELECT * FROM jutsus WHERE cla = ? ORDER BY rank, custo_chakra, nome", (clan["nome"],))
        j_rows = cursor.fetchall()
        jutsus = []
        ranks_count = {}
        total_chakra = 0
        naturezas_set = set()

        for jr in j_rows:
            jd = dict(jr)
            jd["componentes"] = json.loads(jd["componentes"])
            jd["palavras_chave"] = json.loads(jd["palavras_chave"])
            jd["condicoes"] = json.loads(jd["condicoes"])
            jd["exclusivo_cla"] = bool(jd["exclusivo_cla"])
            jutsus.append(jd)

            rk = jd["rank"]
            ranks_count[rk] = ranks_count.get(rk, 0) + 1
            total_chakra += jd["custo_chakra"]
            if jd["natureza_estilo"]:
                naturezas_set.add(jd["natureza_estilo"])

        # Linhagens latentes
        cursor.execute("SELECT * FROM latent_bloodlines WHERE cla = ? ORDER BY custo_pontos, nome_habilidade", (clan["nome"],))
        l_rows = cursor.fetchall()
        latentes = [dict(lr) for lr in l_rows]
        latentes_por_custo = {}
        for lr in latentes:
            pts = lr["custo_pontos"]
            latentes_por_custo[pts] = latentes_por_custo.get(pts, 0) + 1

        stats = {
            "total_jutsus": len(jutsus),
            "jutsus_por_rank": ranks_count,
            "naturezas": sorted(list(naturezas_set)),
            "custo_chakra_medio": round(total_chakra / len(jutsus), 1) if jutsus else 0.0,
            "total_latentes": len(latentes),
            "latentes_por_custo": latentes_por_custo,
            "total_recursos": len(clan["recursos"])
        }

        results.append({
            "cla": clan,
            "stats": stats,
            "jutsus_exclusivos": jutsus,
            "linhagens_latentes": latentes
        })

    conn.close()

    if not results:
        raise HTTPException(status_code=404, detail="Nenhum dos clãs solicitados foi encontrado.")

    return results


@router.get("/{nome}")
def get_clan_detail(nome: str, db_path: str = DEFAULT_DB_PATH):
    """Retorna a ficha mecânica completa de um clã, seus jutsus exclusivos e linhagens latentes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clans WHERE nome LIKE ?", (f"%{nome.strip()}%",))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Clã '{nome}' não encontrado.")

    clan = dict(row)
    clan["aumento_atributos"] = json.loads(clan["aumento_atributos"])
    clan["pericias"] = json.loads(clan["pericias"])
    clan["idiomas"] = json.loads(clan["idiomas"])
    clan["recursos"] = json.loads(clan["recursos"])

    # Jutsus exclusivos do clã
    cursor.execute("SELECT * FROM jutsus WHERE cla = ? ORDER BY rank, custo_chakra, nome", (clan["nome"],))
    j_rows = cursor.fetchall()
    jutsus = []
    for r in j_rows:
        d = dict(r)
        d["componentes"] = json.loads(d["componentes"])
        d["palavras_chave"] = json.loads(d["palavras_chave"])
        d["condicoes"] = json.loads(d["condicoes"])
        d["exclusivo_cla"] = bool(d["exclusivo_cla"])
        jutsus.append(d)

    # Linhagens latentes do clã
    cursor.execute("SELECT * FROM latent_bloodlines WHERE cla = ? ORDER BY custo_pontos, nome_habilidade", (clan["nome"],))
    l_rows = cursor.fetchall()
    latent = [dict(r) for r in l_rows]

    conn.close()

    return {
        "cla": clan,
        "jutsus_exclusivos": jutsus,
        "linhagens_latentes": latent
    }


@router.get("/latent/all")
def list_latent_bloodlines(
    cla: Optional[str] = Query(None, description="Filtrar por clã"),
    max_pontos: Optional[int] = Query(None, description="Custo máximo em pontos"),
    q: Optional[str] = Query(None, description="Busca textual"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta habilidades de linhagens latentes de todos os clãs."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    conditions = ["1=1"]
    params = []

    if cla:
        conditions.append("cla LIKE ?")
        params.append(f"%{cla.strip()}%")
    if max_pontos is not None:
        conditions.append("custo_pontos <= ?")
        params.append(max_pontos)
    if q:
        conditions.append("(nome_habilidade LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

    query = f"SELECT * FROM latent_bloodlines WHERE {' AND '.join(conditions)} ORDER BY cla, custo_pontos, nome_habilidade"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results
