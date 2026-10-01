import re
import pymupdf
from typing import List, Dict, Optional, Tuple, Any
from src.extractor.pdf_reader import iter_pdf_blocks
from src.models.clan import Clan, ClanFeature, LatentTrait

# Mapeamento do Sumário Oficial de Clãs em Clas.pdf (Nome, Página Inicial, Página Final Estimada)
CLAN_TOC = [
    ("Aburame", 4, 10), ("Akimichi", 10, 16), ("Bakuton", 16, 24), ("Chinoike", 24, 32),
    ("Fuma", 32, 36), ("Fūshin", 36, 41), ("Futton", 41, 47), ("Genwa", 47, 55),
    ("Hanami", 55, 60), ("Hatake", 60, 61), ("Hebi", 61, 67), ("Hoshi", 67, 75),
    ("Hoshigaki", 75, 79), ("Hozuki", 79, 84), ("Hyūga", 84, 92), ("Iburi", 92, 99),
    ("Inuzuka", 99, 106), ("Jiton", 106, 115), ("Jūgo", 115, 121), ("Kaguya", 121, 128),
    ("Kashu", 128, 135), ("Keton", 135, 140), ("Konjiki", 140, 146), ("Kurama", 146, 149),
    ("Kuru", 149, 156), ("Namikaze", 156, 162), ("Nara", 162, 168), ("Sem Clã", 168, 170),
    ("Ranton", 170, 177), ("Ryu", 177, 183), ("Sarutobi", 183, 186), ("Senju", 186, 194),
    ("Shakuton", 194, 200), ("Shí Hóu", 200, 204), ("Shikigami", 204, 210), ("Shoton", 210, 216),
    ("Humanos Sintéticos", 216, 222), ("Tsuchigumo", 222, 228), ("Uchiha", 228, 237),
    ("Uzumaki", 237, 243), ("Vesper", 243, 248), ("Yamada", 248, 253), ("Yamanaka", 253, 260),
    ("Yoton", 260, 267), ("Yuki", 267, 272)
]

ATTR_MAP = {
    "con": "Constituição", "constituicao": "Constituição", "constituição": "Constituição",
    "for": "Força", "forca": "Força", "força": "Força",
    "des": "Destreza", "destreza": "Destreza",
    "int": "Inteligência", "inteligencia": "Inteligência", "inteligência": "Inteligência",
    "sab": "Sabedoria", "sabedoria": "Sabedoria",
    "car": "Carisma", "cha": "Carisma", "carisma": "Carisma"
}


def parse_attr_bonuses(raw_text: str) -> Dict[str, int]:
    bonuses = {}
    if not raw_text:
        return bonuses

    raw_lower = raw_text.lower()
    if "qualquer" in raw_lower or "a sua escolha" in raw_lower or "à sua escolha" in raw_lower:
        return {"Qualquer Atributo (Escolha 1)": 2, "Qualquer Atributo (Escolha 2)": 1}

    matches = re.findall(r"(\+\d+)\s*(?:em\s*)?([A-Za-zÀ-ÿ]+(?:\s+ou\s+[A-Za-zÀ-ÿ]+)?)", raw_text, re.IGNORECASE)
    for val_str, attr_str in matches:
        val = int(val_str.replace("+", ""))
        parts = [p.strip().lower() for p in attr_str.split(" ou ")]
        norm_parts = [ATTR_MAP.get(p[:3], p.capitalize()) for p in parts if p[:3] in ATTR_MAP]
        if norm_parts:
            norm_key = "/".join(norm_parts)
            bonuses[norm_key] = val
    return bonuses


def parse_all_clans(pdf_path: str = "PDFs/Clas.pdf") -> List[Clan]:
    """Extrai os 45 clãs com seus atributos, deslocamento, perícias e características mecânicas."""
    doc = pymupdf.open(pdf_path)
    clans: List[Clan] = []

    for name, p_start, p_end in CLAN_TOC:
        # Páginas do clã (0-indexed)
        pages_to_check = range(p_start - 1, min(p_start + 2, len(doc)))
        full_text = "\n".join([doc[p].get_text() for p in pages_to_check])

        # 1. Bônus de Atributos
        m_attr = re.search(
            r"(?:Aumento (?:da|no|de|nas)?\s*(?:pontuação|pontuações|valor|valores|habilidade|pontos|recomendado)[^:]*):\s*(.*?)(?=\n\s*(?:Velocidade|Proficiências|Perícias|[A-Z][a-z]+:|\n\n)|$)",
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        bonus_raw = m_attr.group(1).strip().replace("\n", " ") if m_attr else "Não especificado"
        bonus_dict = parse_attr_bonuses(bonus_raw)

        # 2. Deslocamento / Velocidade
        m_spd = re.search(
            r"Velocidade:\s*(.*?)(?=\n[A-Z]|\n\n|$)",
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        speed = m_spd.group(1).strip().replace("\n", " ") if m_spd else "9 Metros (padrão)"
        # Limpar texto extra de velocidade
        if "caminhada" in speed.lower() or "base" in speed.lower():
            m_num = re.search(r"(\d+\s*(?:Metros|metros|pés|pes))", speed)
            if m_num:
                speed = m_num.group(1)

        # 3. Proficiências / Perícias
        m_per = re.search(
            r"(?:Proficiências em Habilidades|Proficiências de habilidades|Perícias):\s*(.*?)(?=\n[A-Z]|\n\n|$)",
            full_text,
            re.IGNORECASE | re.DOTALL
        )
        pericias_list = []
        if m_per:
            per_raw = m_per.group(1).strip().replace("\n", " ")
            pericias_list = [p.strip().rstrip(".") for p in per_raw.split(",") if p.strip()]

        # 4. Recursos / Características Mecânicas
        features: List[ClanFeature] = []
        blocks = list(iter_pdf_blocks(pdf_path, start_page=p_start - 1, end_page=p_end - 1))

        for b in blocks:
            text = b[2].strip()
            # Interromper quando os jutsus começarem
            if "Classificação:" in text or "Classificacao:" in text:
                break

            lines = text.split("\n")
            for lidx, line in enumerate(lines):
                m_feat = re.match(r"^([A-ZÀ-ÿ][A-Za-zÀ-ÿ\s\-–]{3,40}):\s*(.*)", line)
                if m_feat:
                    fname = m_feat.group(1).strip()
                    # Ignorar cabeçalhos comuns não-mecânicos
                    if any(k in fname.lower() for k in [
                        "aumento", "velocidade", "proficiênc", "perícia", "idioma",
                        "conversão", "creditos", "ilustrador", "idade", "tendência", "tamanho"
                    ]):
                        continue

                    rest = m_feat.group(2).strip()
                    desc_lines = [rest] + lines[lidx + 1:]
                    fdesc = " ".join([d.strip() for d in desc_lines if d.strip()])

                    # Detectar nível exigido
                    m_lvl = re.search(r"(?:A partir do|No|no)\s+(\d+)º\s+[Nn]ível", fdesc)
                    req_lvl = int(m_lvl.group(1)) if m_lvl else 1

                    # Detectar usos
                    m_usos = re.search(r"((?:uma|duas|três|\d+)?\s*(?:vez(?:es)?)?\s*por descanso (?:curto|longo))", fdesc, re.IGNORECASE)
                    usos_str = m_usos.group(1) if m_usos else None

                    features.append(ClanFeature(
                        nome=fname,
                        descricao=fdesc,
                        nivel=req_lvl,
                        usos=usos_str
                    ))

        clan_obj = Clan(
            id=len(clans) + 1,
            nome=name,
            aumento_atributos_raw=bonus_raw,
            aumento_atributos=bonus_dict,
            deslocamento=speed,
            pericias=pericias_list,
            idiomas=[],
            recursos=features,
            tracos_latentes=[],
            pagina=p_start
        )
        clans.append(clan_obj)

    return clans


def parse_all_latent_bloodlines(pdf_path: str = "PDFs/Clas.pdf") -> List[Dict[str, Any]]:
    """Extrai todas as habilidades de linhagem sanguínea latente das páginas 273 a 314."""
    doc = pymupdf.open(pdf_path)
    latent_traits: List[Dict[str, Any]] = []

    # Mapeamento de página para clã latente
    for pno in range(273, min(315, len(doc))):
        text = doc[pno].get_text()
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        clan_name = "Desconhecido"
        for l in lines:
            if "LATENTE" in l.upper() and len(l) >= 6:
                clean_clan = l.replace("Habilidade de Linhagem", "").replace("LATENTE", "").strip().title()
                if clean_clan:
                    clan_name = clean_clan
                break

        # Localizar tabela
        idx = text.find("Descrição da Habilidade")
        if idx == -1:
            idx = text.find("Descrio da Habilidade")
        if idx == -1:
            continue

        body = text[idx + len("Descrição da Habilidade"):].strip()
        blines = [l.strip() for l in body.split("\n") if l.strip()]

        # Cada traço é delimitado por uma linha com custo numérico (dígito único 1-9)
        cost_indices = [i for i, l in enumerate(blines) if l.isdigit() and len(l) == 1]

        for k, cidx in enumerate(cost_indices):
            cost = int(blines[cidx])

            # O nome está nas linhas imediatamente anteriores ao custo
            # Procurar onde o nome começa
            name_lines = []
            lookback = cidx - 1
            while lookback >= 0 and lookback > (cost_indices[k - 1] if k > 0 else -1):
                cand = blines[lookback]
                name_lines.insert(0, cand)
                # Nomes de linhagem geralmente têm "Latente", "Hijutsu", "Talentos" ou até 3 palavras
                if any(w in cand for w in ["Latente", "Hijutsu", "Talento", "Pílula", "Isolamento", "Calorias", "Hospedeiro", "Estilo", "Modo"]):
                    break
                if len(name_lines) >= 3:
                    break
                lookback -= 1

            trait_name = " ".join(name_lines).strip()
            if not trait_name:
                trait_name = blines[cidx - 1] if cidx > 0 else "Habilidade Latente"

            # A descrição está após o custo até o início do próximo nome
            next_cidx = cost_indices[k + 1] if k + 1 < len(cost_indices) else len(blines)
            # O próximo nome ocupa as 1-2 linhas antes de next_cidx
            desc_end = max(cidx + 1, next_cidx - 2 if k + 1 < len(cost_indices) else len(blines))
            desc_lines = blines[cidx + 1:desc_end]
            trait_desc = " ".join(desc_lines).strip()

            # Pré-requisito explícito
            m_pre = re.search(r"(\((?:Você deve ter|Você precisa ter|É necessário ter|é necessário ter)[^)]+\))", trait_desc, re.IGNORECASE)
            pre_req = m_pre.group(1) if m_pre else None

            latent_traits.append({
                "cla": clan_name,
                "nome_habilidade": trait_name,
                "custo_pontos": cost,
                "pre_requisito": pre_req,
                "descricao": trait_desc,
                "pagina": pno + 1
            })

    return latent_traits
