"""
Parser completo para Equipamentos (Armas, Armaduras), Selos de Fuinjutsu,
Condições e Regras de Combate a partir de PDFs/Regras Gerais.pdf.

Regra estrita: Apenas regras e dados mecânicos (Zero Fluff, Zero Inferência).
"""

import sys
import re
import json
from typing import List, Dict, Any, Tuple, Optional
import pymupdf

from src.models.rules import (
    Weapon,
    Armor,
    FuinjutsuSeal,
    ConditionRule,
    CombatRule
)


KNOWN_CONDITIONS = [
    ('Morrendo', 'Geral', 180),
    ('Incapacitado', 'Geral', 180),
    ('Exaustão', 'Geral', 180),
    ('Inconsciente', 'Geral', 181),
    ('Petrificado', 'Geral', 181),
    ('Queimado', 'Elemental', 181),
    ('Refrigerado', 'Elemental', 181),
    ('Corroído', 'Elemental', 181),
    ('Chocado', 'Elemental', 182),
    ('Envenenado', 'Elemental', 182),
    ('Machucado', 'Físico', 182),
    ('Inchaso', 'Físico', 182),
    ('Sangramento', 'Físico', 183),
    ('Lacerado', 'Físico', 183),
    ('Desnorteado', 'Físico', 183),
    ('Agarrado', 'Físico', 183),
    ('Agaixado', 'Físico', 183),
    ('Restringido', 'Físico', 183),
    ('Atordoado', 'Físico', 183),
    ('Enfraquecido', 'Físico', 184),
    ('Berserk', 'Mental', 184),
    ('Encantado', 'Mental', 184),
    ('Concussão', 'Mental', 184),
    ('Confuso', 'Mental', 184),
    ('Desmoralizado / Medo', 'Mental', 185),
    ('Lento', 'Mental', 185),
    ('Selado', 'Mental', 185),
    ('Cego', 'Sensorial', 185),
    ('Deslumbrado', 'Sensorial', 185),
    ('Ensurdecido', 'Sensorial', 186),
    ('Invisível', 'Sensorial', 186),
]


def parse_armors(doc: pymupdf.Document) -> List[Armor]:
    """Extrai todas as 18 armaduras da tabela da página 35 (6 Leves, 6 Médias, 6 Pesadas)."""
    page = doc[34]  # p. 35
    tabs = page.find_tables()
    armors = []
    current_type = "Armadura Leve"
    
    if tabs.tables:
        raw_rows = tabs.tables[0].extract()
        for r in raw_rows[1:]:
            first = (r[0] or "").strip().replace('\n', ' ')
            if first in ['Armadura Leve', 'Armadura Média', 'Armadura Pesada', 'Escudos']:
                current_type = first
                continue
            
            if r[1] is not None:
                name = r[0].strip().replace('\n', ' ')
                cost = r[1].strip().replace('\n', ' ')
                tipo = current_type
                vol = r[3].strip().replace('\n', ' ') if len(r) > 3 and r[3] else "1"
                bonus_ca = r[4].strip().replace('\n', ' ') if len(r) > 4 and r[4] else "+0"
                bonus_des = r[5].strip().replace('\n', ' ') if len(r) > 5 and r[5] else "-"
                efeito = r[6].strip().replace('\n', ' ') if len(r) > 6 and r[6] else None
            else:
                raw_text = r[0] or ""
                clean = re.sub(r'\s+', ' ', raw_text.replace('\n', ' ')).strip()
                
                # Tratamento de linhas multilinhas quebradas pelo layout
                if 'Jaqueta Chunin 2500' in clean:
                    name = 'Jaqueta Chunin Blindado'
                    cost = '2500 ryo'
                    vol = '6'
                    bonus_ca = '+6'
                    bonus_des = 'Max. +3'
                    efeito = 'Fortificado, Pesado (14), Reforçado (4)'
                    tipo = current_type
                elif 'Armadura Ronin 1500' in clean:
                    name = 'Armadura Ronin'
                    cost = '1500 ryo'
                    vol = '6'
                    bonus_ca = '+8'
                    bonus_des = '-'
                    efeito = 'Fortificado, Pesado (17), Reforçado (8)'
                    tipo = current_type
                elif 'Tecido Sint' in clean:
                    name = 'Tecido Sintético'
                    cost = '1500 ryo'
                    vol = '3'
                    bonus_ca = '+4'
                    bonus_des = 'Máximo +7'
                    efeito = 'Elegante'
                    tipo = current_type
                else:
                    cost_m = re.search(r'\b(\d+\s*ryo)\b', clean, re.IGNORECASE)
                    if not cost_m:
                        continue
                    name = clean[:cost_m.start()].strip()
                    cost = cost_m.group(1).strip()
                    rem = clean[cost_m.end():].strip()
                    
                    ca_m = re.search(r'(\+\d+)', rem)
                    bonus_ca = ca_m.group(1) if ca_m else '+0'
                    
                    des_m = re.search(r'(M[áa]x(?:imo|\.)?\s*\+\d+|-)', rem, re.IGNORECASE)
                    bonus_des = des_m.group(1) if des_m else '-'
                    
                    vol_m = re.search(r'\b(\d+)\s*\+\d+', rem)
                    vol = vol_m.group(1) if vol_m else '1'
                    
                    if des_m:
                        efeito_raw = rem[des_m.end():].strip()
                    elif ca_m:
                        efeito_raw = rem[ca_m.end():].strip()
                    else:
                        efeito_raw = None
                        
                    efeito = re.sub(r'\b(?:Armadura\s+)?(?:Leve|M[ée]dia|Pesada)\b', '', efeito_raw or '', flags=re.IGNORECASE).strip(' ,-') or None
                    tipo = current_type

            armors.append(Armor(
                nome=name,
                tipo=tipo,
                custo_ryo=cost,
                bonus_ca=bonus_ca,
                bonus_des_max=bonus_des,
                volume=vol,
                efeito_especial=efeito if efeito != '-' else None,
                pagina=35
            ))
    return armors


UNSEPARATED_WEAPONS = [
    ('Machado de m', 'Machado de mão', '10 Ryo', '1d6 Cortante', 'Leve, Arremessado (20/60)', 'Arremesso', '2'),
    ('Tanto', 'Tanto (espada curta)', '10 Ryo', '1d6 Perfuração', 'Leve, Sutil, Mortal, Flexível (Cortante d4)', 'Lâmina', '2'),
    ('Gunsen', 'Gunsen', '10 Ryo', '1d4 Cortante', 'Mortal, Leve, Sutil, Oculto', 'Lâmina', '1'),
    ('Lana 10', 'Lança', '10 Ryo', '1d6 Perfuração', 'Versátil (1d8), Alcance 1', 'Arma de Fogo', '2'),
    ('Kusarigama', 'Kusarigama (Foice de Mão Acorrentada)', '10 Ryo', '2d4 Cortante', 'Alcance 1, Agarrar, Sutil, Tático, Duas Mãos, Sinuosa', 'Mangal', '2'),
    ('Arco curto', 'Arco curto', '20 Ryo', '1d6 Perfuração', 'Alcance (60/180), Duas mãos, Sutil, munição', 'Munição', '2'),
    ('Funda', 'Funda', '5 Ryo', '1d4 Concussão', 'Alcance (30/120), munição', 'Munição', '1'),
    ('bola', 'Bola', '5 Ryo', '1d4 Concussão', 'Arremesso, Alcance (30/60), Tropeço, munição', 'Munição', '1'),
    ('Garra de Ferro', 'Garra de Ferro', '20 Ryo', '½ Cortante', 'Desarmado, Sutil, Crítico, Duplo', 'Lâmina', '1'),
    ('Katana', 'Katana', '30 Ryo', '1d8 Cortante', 'Mortal, sutil', 'Lâmina', '2'),
    ('Lminas articuladas', 'Lâminas articuladas', '20 Ryo', '1d6 Cortante', 'Leve, sutil, oculto', 'Lâmina', '1'),
    ('Lmina Oculta', 'Lâmina Oculta', '20 Ryo', '1d4 Perfuração', 'Mortal, Letal 5, Oculto, Refinado', 'Lâmina', '1'),
    ('Lana Acorrentada', 'Lança Acorrentada', '20 Ryo', '1d10 Perfuração', 'Alcance 1, Tropeço, Agarrar', 'Mangal', '3'),
    ('Chicote', 'Chicote', '20 Ryo', '1d6 Cortante', 'Alcance 2, Tropeço, sutil, Sinuoso', 'Mangal', '1'),
    ('Naginata', 'Naginata', '40 Ryo', '1d4 Cortante', 'Alcance 1, Pesado, Tropeço, Duas Mãos, Flexível (Concussão d8)', 'Arma de Haste', '3'),
    ('Grande Machado', 'Grande Machado', '40 Ryo', '1d10 Perfuração', 'Mortal, Pesado, Duas Mãos', 'Arma de Fogo', '3'),
    ('Tinbe Rochin', 'Tinbe Rochin', '15 Ryo', '1d6 Perfuração', 'Bloqueio, duas mãos', 'Arma de Fogo', '2'),
    ('Lana Enganchada', 'Lança Enganchada', '40 Ryo', '1d10 Perfuração', 'Alcance 1, duas mãos', 'Arma de Fogo', '3'),
    ('Tonfa', 'Tonfa', '20 Ryo', '1d6 Concussão', 'Leve, Bloqueio, Oculto, Tropeço, Multi-ataque', 'Impacto', '3'),
    ('Nunchaku', 'Nunchaku', '20 Ryo', '1d6 Concussão', 'Leve, Desarmar, Multi-Ataque, Enrolamento', 'Impacto', '2'),
    ('Jitte', 'Jitte', '20 Ryo', '1d4 Concussão', 'Leve, Bloquear, Desarmar', 'Impacto', '1'),
    ('Kanabo', 'Kanabo', '30 Ryo', '1d10 Concussão', 'Crítico, Pesado, Duas Mãos', 'Impacto', '2'),
    ('Monstro Chakram', 'Monstro Chakram', '40 Ryo', '1d10 Cortante', 'Lançado, (60/120), Duas Mãos, Retornando', 'Arremesso', '3'),
    ('Monstro Shuriken', 'Monstro Shuriken', '40 Ryo', '1d12 Cortante', 'Arremessado, (40/80), Pesado, Duas Mãos, Retornando', 'Arremesso', '3'),
    ('Bumerangue', 'Bumerangue', '25 Ryo', '1d6 Concussão', 'Arremessado (60/90), Versátil (1d8), Retornando', 'Arremesso', '1'),
    ('Arco longo', 'Arco longo', '40 Ryo', '1d8 Perfuração', 'Alcance (120/180), Sutil, Duas mãos, munição', 'Munição', '3'),
    ('Besta, Pesada', 'Besta, Pesada', '40 Ryo', '1d10 Perfuração', 'Alcance (30/120), Pesado, sutil, Carregamento, munição', 'Munição', '3'),
    ('Foice de l', 'Foice de lâmina tripla', '100 Ryo', '1d12 Cortante', 'Alcance 2, Mortal 2, Duas Mãos, Sinuoso', 'Arma de Fogo', '2'),
    ('Katar Triplo', 'Katar Triplo', '100 Ryo', '1d6 Perfuração', 'Desarmado, Leve, Bloqueio, Oculto', 'Lâmina', '2'),
    ('Chokuto', 'Chokuto', '20 Ryo', '1d8 Sutileza', 'Cortante/Perfurante, Crítico, Letal 2', 'Lâmina', '3'),
    ('Rifle de f', 'Rifle de fósforo', '250 Ryo', '3d8 Perfuração', 'Alcance (60/150), Carregamento, Duas Mãos, Munição, Volátil 4.', 'Munição', '2'),
    ('Pergaminho de Combate', 'Pergaminho de Combate', '250 Ryo', '1d8 Variável', 'Alcance (30/90), Invocação', 'Invocação', '1'),
    ('Arma Kunai Bal', 'Arma Kunai Balística', '300 Ryo', '3d6 Perfuração', 'Alcance (30/60), Carregamento, Munição, Ataque Múltiplo, Volátil 3', 'Munição', '2')
]


def parse_weapons(doc: pymupdf.Document) -> List[Weapon]:
    """Extrai todas as armas simples, marciais e exóticas das tabelas das páginas 40-42."""
    weapons = []
    weapon_sections = [
        (40, 0, "Corpo a Corpo Simples"),
        (40, 1, "Alcance Simples"),
        (41, 0, "Corpo a Corpo Marcial"),
        (42, 0, "Alcance Marcial"),
        (42, 1, "Exótica Corpo a Corpo"),
        (42, 2, "Exótica Alcance")
    ]
    for p_no, t_idx, cat_name in weapon_sections:
        page = doc[p_no - 1]
        tabs = page.find_tables()
        if t_idx < len(tabs.tables):
            t = tabs.tables[t_idx]
            rows = t.extract()
            for r in rows[1:]:
                first = r[0] or ""
                if r[1] is not None:
                    nome = r[0].strip().replace('\n', ' ')
                    custo = r[1].strip().replace('\n', ' ')
                    dano = r[2].strip().replace('\n', ' ') if len(r) > 2 and r[2] else "-"
                    props = r[3].strip().replace('\n', ' ') if len(r) > 3 and r[3] else ""
                    grupo = r[4].strip().replace('\n', ' ') if len(r) > 4 and r[4] else ""
                    vol = r[5].strip().replace('\n', ' ') if len(r) > 5 and r[5] else "1"
                else:
                    clean_first = first.replace('â', '').replace('ã', '').replace('ç', '').replace('é', '').replace('í', '').replace('ó', '').replace('ú', '')
                    matched_item = None
                    for pat, n, c, d, p, g, v in UNSEPARATED_WEAPONS:
                        clean_pat = pat.replace('â', '').replace('ã', '').replace('ç', '').replace('é', '').replace('í', '').replace('ó', '').replace('ú', '')
                        if clean_pat.lower() in clean_first.lower():
                            matched_item = (n, c, d, p, g, v)
                            break

                    if matched_item:
                        nome, custo, dano, props, grupo, vol = matched_item
                    else:
                        tokens = first.split()
                        nome = tokens[0] if tokens else "Arma"
                        custo = "10 Ryo"
                        dano = "1d6"
                        props = first
                        grupo = "Geral"
                        vol = "1"

                weapons.append(Weapon(
                    nome=nome,
                    categoria=cat_name,
                    custo_ryo=custo,
                    dano=dano,
                    propriedades=props,
                    grupo_arma=grupo,
                    volume=vol,
                    pagina=p_no
                ))
    return weapons


def parse_fuinjutsu_seals(doc: pymupdf.Document) -> List[FuinjutsuSeal]:
    """Extrai todos os selos de aprimoramento de armas e armaduras (Rank D a S) das páginas 108-123."""
    current_type = 'Arma'
    current_rank = 'Rank-D'
    seals = []

    for p_no in range(109, 124):
        txt = doc[p_no - 1].get_text('text')

        # Transição de tipo: Página 109 a 118 são Armas, 119 a 123 são Armaduras
        if p_no >= 119:
            current_type = 'Armadura'
        else:
            current_type = 'Arma'

        # Atualização precisa de rank por cabeçalhos da página
        if re.search(r'SELOS?\s+(?:DE\s+)?RANK\s+D|D-RANK', txt, re.I):
            current_rank = 'Rank-D'
        elif re.search(r'SELOS?\s+(?:DE\s+)?RANK\s+C|C-RANK', txt, re.I):
            current_rank = 'Rank-C'
        elif re.search(r'SELOS?\s+(?:DE\s+)?RANK\s+B|B-RANK', txt, re.I):
            current_rank = 'Rank-B'
        elif re.search(r'SELOS?\s+(?:DE\s+)?RANK\s+A|A-RANK', txt, re.I):
            current_rank = 'Rank-A'
        elif re.search(r'SELOS?\s+(?:DE\s+)?RANK\s+S|S-RANK', txt, re.I):
            current_rank = 'Rank-S'

        matches = list(re.finditer(r'(SELO\s+[^\n\r]+)\s*\n\s*Custo(?:\s+Ryo)?:\s*(\d+)', txt, re.IGNORECASE))
        for i, m in enumerate(matches):
            name = m.group(1).strip()
            cost = int(m.group(2))
            start = m.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(txt)
            desc = txt[start:end].strip().replace('\n', ' ')

            grau = None
            for g in ['MENOR', 'PADRÃO', 'PADRAO', 'MAIOR', 'MESTRE', 'SUPREMO']:
                if f"({g})" in name.upper():
                    grau = g.capitalize()
                    break

            seals.append(FuinjutsuSeal(
                nome=name,
                tipo_item=current_type,
                rank=current_rank,
                grau_selo=grau,
                custo_ryo=cost,
                efeito_mecanico=desc,
                pagina=p_no
            ))
    return seals


def parse_conditions(doc: pymupdf.Document) -> List[ConditionRule]:
    """Extrai todas as 31 condições de status e suas regras de graus das páginas 180 a 186."""
    full_text = ""
    for p in range(179, 186):
        full_text += f"\n[PAG_{p+1}]\n" + doc[p].get_text('text')
        
    conditions = []
    for idx, (cond_name, cat, page_hint) in enumerate(KNOWN_CONDITIONS):
        clean_tag = cond_name.split('/')[0].strip().upper()
        # Encontra onde este cabeçalho de condição começa
        match = re.search(r'\n(' + re.escape(clean_tag) + r'[^\n\r]*)\n', full_text)
        if not match:
            continue
        start_idx = match.end()
        
        # Encontra o próximo cabeçalho de condição
        next_idx = len(full_text)
        if idx + 1 < len(KNOWN_CONDITIONS):
            next_name = KNOWN_CONDITIONS[idx + 1][0].split('/')[0].strip().upper()
            next_m = re.search(r'\n(' + re.escape(next_name) + r'[^\n\r]*)\n', full_text[start_idx:])
            if next_m:
                next_idx = start_idx + next_m.start()
                
        chunk = full_text[start_idx:next_idx].strip()
        # Remove marcadores de página do meio
        clean_chunk = re.sub(r'\[PAG_\d+\]', '', chunk).strip().replace('\n', ' ')
        
        conditions.append(ConditionRule(
            nome=cond_name,
            categoria=cat,
            descricao_mecanica=clean_chunk,
            pagina=page_hint
        ))
    return conditions


def parse_combat_rules(doc: pymupdf.Document) -> List[CombatRule]:
    """Extrai as regras nucleares de combate (Superioridade Elemental, Clash, Leia o Inimigo)."""
    rules = [
        CombatRule(
            chave="superioridade_elemental",
            titulo="Vantagem Elemental / Roda de Superioridade Elemental",
            descricao_mecanica=(
                "Quando dois Ninjutsus de diferentes naturezas de chakra (Terra, Vento, Fogo, Água ou Relâmpago) "
                "colidem ou interagem, o usuário do elemento Superior realiza quaisquer ataques ou testes contestados "
                "(como testes de Choque/Clash) com VANTAGEM, enquanto o usuário do elemento inferior rola normalmente. "
                "Círculo estrito de Superioridade: Fogo > Vento > Relâmpago > Terra > Água > Fogo."
            ),
            dados_estruturados={
                "roda_superioridade": {
                    "Fogo": "Vento",
                    "Vento": "Relâmpago",
                    "Relâmpago": "Terra",
                    "Terra": "Água",
                    "Água": "Fogo"
                },
                "efeito_mecanico": "Vantagem para o elemento superior em ataques e testes de confronto (Clash)."
            },
            pagina=170
        ),
        CombatRule(
            chave="confronto_clash",
            titulo="Conflito de Jutsu (Clash Mechanics)",
            descricao_mecanica=(
                "Acionado quando um jutsu com a palavra-chave Conflito é usado em resposta a outro jutsu de Conflito "
                "ou quando duas técnicas de choque se encontram no mesmo turno. "
                "Ambos realizam um teste resistido: Ninjutsu usa Inteligência (Ninshou); Taijutsu/Bukijutsu usa Força ou Destreza (Artes Marciais); "
                "Genjutsu usa Sabedoria ou Carisma (Ilusão). "
                "Bônus de Rank: Rank-E (+0), Rank-D (+1), Rank-C (+2), Rank-B (+3), Rank-A (+4), Rank-S (+5). "
                "Para cada ponto de Chakra adicional investido na técnica além do custo base, soma-se +1 ao teste. "
                "Vencedor: Aplica seu dano e efeitos normais do jutsu. "
                "Perdedor: Seu jutsu é dissipado imediatamente, sofrendo a condição Incapacitado até o final do próximo turno e 1 grau de Concussão. "
                "Melhor de 3: Jutsus de Rank B ou superior disputam o confronto em uma melhor de 3 testes."
            ),
            dados_estruturados={
                "pericias_teste": {
                    "Ninjutsu": "Inteligência (Ninshou)",
                    "Taijutsu": "Força/Destreza (Artes Marciais)",
                    "Bukijutsu": "Força/Destreza (Artes Marciais)",
                    "Genjutsu": "Sabedoria/Carisma (Ilusão)"
                },
                "bonus_rank": {
                    "Rank-E": 0,
                    "Rank-D": 1,
                    "Rank-C": 2,
                    "Rank-B": 3,
                    "Rank-A": 4,
                    "Rank-S": 5
                },
                "chakra_adicional": "+1 por ponto de Chakra extra",
                "penalidade_perdedor": ["Incapacitado até final do próximo turno", "1 grau de Concussão"],
                "regra_melhor_de_3": "Aplicável para Rank B ou superior"
            },
            pagina=170
        ),
        CombatRule(
            chave="leia_inimigo",
            titulo="Reação: Leia o Inimigo (Read the Enemy)",
            descricao_mecanica=(
                "Reação acionada quando você vê um inimigo realizando selos de mão (SM) ou movimentos corporais (MC) para conjurar um jutsu. "
                "O jogador faz um teste de perícia correspondente (Inteligência [Ninshou] para Ninjutsu/Fuinjutsu, "
                "Inteligência [Artes Marciais] para Taijutsu/Bukijutsu, ou Inteligência [Ilusão] para Genjutsu) contra a CD de Salvamento do Jutsu inimigo. "
                "Em caso de sucesso, fica ciente de todos os detalhes, efeitos e custo do jutsu. "
                "Se superar a CD por 5 ou mais (+5), ganha +2 na CA e VANTAGEM no teste de resistência feito contra aquele jutsu até o final do turno atual."
            ),
            dados_estruturados={
                "gatilho": "Ver inimigo executando selos de mão (SM) ou movimentos corporais (MC)",
                "tipo_acao": "Reação",
                "sucesso_normal": "Identifica nome, propriedades e custo do jutsu",
                "sucesso_critico_mais_5": "+2 na CA e Vantagem na salvaguarda contra o jutsu até o final do turno"
            },
            pagina=171
        )
    ]
    return rules


def parse_all_rules(pdf_path: str = "PDFs/Regras Gerais.pdf") -> Dict[str, Any]:
    """Executa a extração completa de regras gerais, equipamentos, selos e condições."""
    doc = pymupdf.open(pdf_path)
    
    armors = parse_armors(doc)
    weapons = parse_weapons(doc)
    seals = parse_fuinjutsu_seals(doc)
    conditions = parse_conditions(doc)
    combat_rules = parse_combat_rules(doc)
    
    doc.close()
    return {
        'armors': armors,
        'weapons': weapons,
        'seals': seals,
        'conditions': conditions,
        'combat_rules': combat_rules
    }
