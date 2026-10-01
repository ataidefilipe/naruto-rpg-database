import re
from typing import List, Optional, Tuple, Dict, Any
from src.extractor.pdf_reader import iter_pdf_blocks
from src.models.jutsu import Jutsu


# Mapeamento de seções e naturezas elementais por página aproximada em Jutsus.pdf
JUTSUS_SECTION_PAGES = [
    (5, 48, "Não Elemental"),
    (49, 81, "Ninjutsu Médico"),
    (82, 108, "Estilo Terra"),
    (109, 133, "Estilo Vento"),
    (134, 158, "Estilo Fogo"),
    (159, 188, "Estilo Água"),
    (189, 217, "Estilo Relâmpago"),
    (218, 313, "Genjutsu"),
    (314, 368, "Taijutsu"),
    (369, 457, "Bukijutsu"),
    (458, 532, "Jutsu de Invocação"),
]

CONDICOES_CANONICAS = {
    "envenenado": "Envenenado", "envenenada": "Envenenado",
    "contido": "Contido", "contida": "Contido",
    "cego": "Cego", "cega": "Cego",
    "caído": "Caído", "caída": "Caído",
    "incapacitado": "Incapacitado", "incapacitada": "Incapacitado",
    "paralisado": "Paralisado", "paralisada": "Paralisado",
    "assustado": "Assustado", "assustada": "Assustado",
    "atordoado": "Atordoado", "atordoada": "Atordoado",
    "inconsciente": "Inconsciente",
    "surdo": "Surdo", "surda": "Surdo",
    "exaustão": "Exaustão"
}

ATRIBUTOS_SALVAGUARDA = [
    "Força", "Destreza", "Constituição", "Inteligência", "Sabedoria", "Carisma"
]


def get_nature_by_page(page_num: int) -> Optional[str]:
    for start, end, nature in JUTSUS_SECTION_PAGES:
        if start <= page_num <= end:
            return nature
    return None


def extract_field_values(header_text: str) -> Dict[str, str]:
    """Extrai os campos chave-valor de um bloco de definição de jutsu."""
    patterns = {
        "classificacao": r"Classifica[çc][ãa]o\s*:\s*(.*?)(?=\n(?:Rank|N[íi]vel|Tempo|Alcance|Dura|Componentes|Custo|Palavras|Descri)|$)",
        "rank": r"(?:Rank|N[íi]vel)\s*:\s*(.*?)(?=\n(?:Classifica|Tempo|Alcance|Dura|Componentes|Custo|Palavras|Descri)|$)",
        "tempo": r"(?:Tempo de [Cc]onjura[çc][ãa]o|Tempo de [Ll]an[çc]amento)\s*:\s*(.*?)(?=\n(?:Classifica|Rank|N[íi]vel|Alcance|Dura|Componentes|Custo|Palavras|Descri)|$)",
        "alcance": r"Alcance\s*:\s*(.*?)(?=\n(?:Classifica|Rank|N[íi]vel|Tempo|Dura|Componentes|Custo|Palavras|Descri)|$)",
        "duracao": r"Dura[çc][ãa]o\s*:\s*(.*?)(?=\n(?:Classifica|Rank|N[íi]vel|Tempo|Alcance|Componentes|Custo|Palavras|Descri)|$)",
        "componentes": r"Componentes\s*:\s*(.*?)(?=\n(?:Classifica|Rank|N[íi]vel|Tempo|Alcance|Dura|Custo|Palavras|Descri)|$)",
        "custo": r"Custo\s*:\s*(.*?)(?=\n(?:Classifica|Rank|N[íi]vel|Tempo|Alcance|Dura|Componentes|Palavras|Descri)|$)",
        "palavras": r"Palavras-[Cc]have\s*:\s*(.*?)(?=\n(?:Classifica|Rank|N[íi]vel|Tempo|Alcance|Dura|Componentes|Custo|Descri)|$)",
        "descricao": r"Descri[çc][ãa]o\s*:\s*(.*)",
    }

    res = {}
    for k, pat in patterns.items():
        flags = re.DOTALL if k == "descricao" else re.IGNORECASE | re.DOTALL
        m = re.search(pat, header_text, flags)
        res[k] = m.group(1).strip() if m else ""
    return res


def extract_mechanical_data(full_desc: str) -> Tuple[Optional[str], Optional[str], Optional[str], List[str], Optional[str], Optional[str]]:
    """Extrai estritamente dados mecânicos explícitos (sem inferência):
    Retorna: (dano_formula, dano_tipo, salvaguarda, condicoes, vantagem_desvantagem, em_niveis_mais_altos)
    """
    em_niveis = None
    upcast_match = re.search(r"(?:Em Níveis (?:Superiores|Mais Altos)|Em níveis mais altos)\s*:\s*(.*)", full_desc, re.IGNORECASE | re.DOTALL)
    if upcast_match:
        em_niveis = upcast_match.group(1).strip()
        desc_core = full_desc[:upcast_match.start()].strip()
    else:
        desc_core = full_desc

    dano_formula = None
    dano_tipo = None
    dano_match = re.search(r"(\d+d\d+(?:\s*[+-]\s*\d+)?)\s*(?:pontos\s*)?(?:de\s*)?dano\s*(?:de\s*)?([A-Za-zÀ-ÿ]+)?", desc_core, re.IGNORECASE)
    if dano_match:
        dano_formula = dano_match.group(1).strip()
        if dano_match.group(2):
            dano_tipo = dano_match.group(2).strip().capitalize()

    salvaguarda = None
    for attr in ATRIBUTOS_SALVAGUARDA:
        if re.search(rf"(?:salvaguarda|teste de resistência)\s*(?:de|em)\s*{attr}", desc_core, re.IGNORECASE):
            salvaguarda = attr
            break

    condicoes = []
    desc_lower = desc_core.lower()
    for cond_key, canon_name in CONDICOES_CANONICAS.items():
        if cond_key in desc_lower and canon_name not in condicoes:
            condicoes.append(canon_name)

    vant_desv = None
    if "vantagem" in desc_lower and "desvantagem" in desc_lower:
        vant_desv = "Concede Vantagem e Desvantagem sob condições específicas"
    elif "vantagem" in desc_lower:
        vant_desv = "Concede Vantagem sob condições específicas"
    elif "desvantagem" in desc_lower:
        vant_desv = "Impõe Desvantagem sob condições específicas"

    return dano_formula, dano_tipo, salvaguarda, condicoes, vant_desv, em_niveis


def parse_jutsus_from_pdf(pdf_path: str, is_clan_pdf: bool = False, start_page: int = 0, end_page: Optional[int] = None) -> List[Jutsu]:
    """Processa o PDF extraindo todos os jutsus como modelos Jutsu validados pelo Pydantic."""
    blocks = list(iter_pdf_blocks(pdf_path, start_page=start_page, end_page=end_page))
    jutsus: List[Jutsu] = []

    # Mapear o clã ativo para cada bloco do documento
    block_clan = [None] * len(blocks)
    if is_clan_pdf:
        tracked_clan = None
        clan_heading_pattern = re.compile(r"^(?:CLÃ|CLA)\s+([A-ZÀ-ÿ]+(?:\s+[A-ZÀ-ÿ]+)?)", re.IGNORECASE)
        for i, (pno, bidx, text, bbox) in enumerate(blocks):
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if lines:
                m_clan = clan_heading_pattern.match(lines[0])
                if m_clan:
                    cand = m_clan.group(1).strip()
                    if len(cand) >= 3 and "LATENTE" not in cand.upper():
                        tracked_clan = cand.title()
            block_clan[i] = tracked_clan

    # Função auxiliar para extrair título e saber se veio de dentro ou fora do bloco
    def get_jutsu_title_info(idx: int) -> Tuple[str, bool]:
        text = blocks[idx][2]
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for lidx, line in enumerate(lines):
            if line.lower().startswith("classificação:") or line.lower().startswith("classificacao:"):
                if lidx > 0:
                    raw_title = " ".join(lines[:lidx])
                    clean_title = re.sub(r"^(?:Rank\s+[E-S]:|NINJUTSUS|GENJUTSU|TAIJUTSU)\s*", "", raw_title, flags=re.IGNORECASE).strip()
                    return clean_title, True
                break

        # Está no bloco imediatamente anterior
        if idx > 0:
            prev_lines = [l.strip() for l in blocks[idx - 1][2].split("\n") if l.strip()]
            title_candidates = []
            for line in reversed(prev_lines):
                if line.isupper() or len(prev_lines) <= 2:
                    title_candidates.insert(0, line)
                    if len(title_candidates) >= 2:
                        break
                else:
                    break
            raw_title = " ".join(title_candidates) if title_candidates else (prev_lines[-1] if prev_lines else "DESCONHECIDO")
            clean_title = re.sub(r"^(?:Rank\s+[E-S]:|NINJUTSUS|GENJUTSU|TAIJUTSU)\s*", "", raw_title, flags=re.IGNORECASE).strip()
            return clean_title, False

    # Identificar índices onde um jutsu começa
    jutsu_indices = [i for i, b in enumerate(blocks) if "Classificação:" in b[2] or "Classificacao:" in b[2]]

    for k, idx in enumerate(jutsu_indices):
        pno, bidx, text, bbox = blocks[idx]
        current_clan = block_clan[idx] if is_clan_pdf else None

        title, is_internal = get_jutsu_title_info(idx)

        # Extrair campos chave-valor do bloco de cabeçalho
        fields = extract_field_values(text)

        # Determinar limite superior dos blocos de descrição
        next_idx = jutsu_indices[k + 1] if k + 1 < len(jutsu_indices) else len(blocks)
        desc_end_idx = next_idx

        # Se o próximo jutsu tem título no bloco externo anterior, não engolir o título dele na descrição atual
        if k + 1 < len(jutsu_indices):
            _, next_is_internal = get_jutsu_title_info(next_idx)
            if not next_is_internal and next_idx - 1 > idx:
                desc_end_idx = next_idx - 1

        desc_parts = [fields.get("descricao", "")]
        for cont_i in range(idx + 1, desc_end_idx):
            cont_text = blocks[cont_i][2].strip()
            if is_clan_pdf and clan_heading_pattern.match(cont_text):
                break
            if re.match(r"^Rank\s+[A-S]:?$", cont_text, re.IGNORECASE):
                continue
            desc_parts.append(cont_text)

        full_desc = " ".join([p.replace("\n", " ").strip() for p in desc_parts if p.strip()])

        # Normalização do Custo em Chakra
        custo_raw = fields.get("custo", "")
        custo_match = re.search(r"(\d+)", custo_raw)
        custo_chakra = int(custo_match.group(1)) if custo_match else 0

        # Componentes
        comp_raw = fields.get("componentes", "")
        componentes = [c.strip() for c in comp_raw.split(",") if c.strip()] if comp_raw else []

        # Palavras-chave
        palavras_raw = fields.get("palavras", "")
        palavras_chave = [p.strip() for p in palavras_raw.split(",") if p.strip()] if palavras_raw else []

        # Extração de dados mecânicos estritos
        dano_formula, dano_tipo, salvaguarda, condicoes, vant_desv, em_niveis = extract_mechanical_data(full_desc)

        if is_clan_pdf:
            natureza_estilo = f"Hijutsu ({current_clan})" if current_clan else "Hijutsu"
        else:
            natureza_estilo = get_nature_by_page(pno)

        origem_livro = "Estudos da Tsunade (Clas.pdf)" if is_clan_pdf else "Anotações do Jiraiya (Jutsus.pdf)"

        jutsu_obj = Jutsu(
            id=len(jutsus) + 1,
            nome=title,
            classificacao=fields.get("classificacao", "Ninjutsu").replace("\n", " ").strip(),
            natureza_estilo=natureza_estilo,
            rank=fields.get("rank", "Rank-D").replace("\n", " ").strip(),
            tempo_conjuracao=fields.get("tempo", "1 Ação").replace("\n", " ").strip(),
            alcance=fields.get("alcance", "Toque").replace("\n", " ").strip(),
            duracao=fields.get("duracao", "Instantâneo").replace("\n", " ").strip(),
            componentes=componentes,
            custo_chakra=custo_chakra,
            palavras_chave=palavras_chave,
            cla=current_clan if is_clan_pdf else None,
            exclusivo_cla=is_clan_pdf,
            efeito_mecanico=full_desc,
            dano_formula=dano_formula,
            dano_tipo=dano_tipo,
            salvaguarda=salvaguarda,
            condicoes=condicoes,
            vantagem_desvantagem=vant_desv,
            em_niveis_mais_altos=em_niveis,
            origem_livro=origem_livro,
            pagina=pno
        )
        jutsus.append(jutsu_obj)

    return jutsus
