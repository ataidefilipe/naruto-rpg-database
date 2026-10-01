"""
Parser completo e robusto para Classes, Progressão (níveis 1-20),
Arquétipos e Talentos de Classe a partir de Classes.pdf.

Regra estrita: Apenas regras e dados mecânicos (Zero Fluff, Zero Inferência).
"""

import sys
import re
import json
from typing import List, Dict, Any, Tuple, Optional
import pymupdf

from src.models.classe import (
    ClassProgressionRow,
    FeatureDetail,
    Archetype,
    ClassTalent,
    ClassEntity
)


CLASSES_CONFIG = [
    {
        'nome': 'Especialista em Genjutsu',
        'nome_en': 'Genjutsu Specialist',
        'tipo_conjurador': 'Alto',
        'table_page': 4,
        'stats_page': 5,
        'core_start': 5,
        'core_end': 9,
        'class_end': 28,
        'extra_cols': ['miragens_maleaveis'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Compromisso de Genjutsu',
        'archetype_lvl': 2,
        'custom_categories': [
            {'nome': 'Início do Genjutsu', 'start': 18, 'end': 19},
            {'nome': 'Miragens Maleáveis', 'start': 20, 'end': 28},
        ],
        'archetypes': [
            {'nome': 'Sedutor', 'page': 9},
            {'nome': 'Pensamentos Corruptos', 'page': 10},
            {'nome': 'Ilusionista', 'page': 11},
            {'nome': 'Realidade em Camadas', 'page': 12},
            {'nome': 'Distorcionista Nebuloso', 'page': 13},
            {'nome': 'Manipulador do Tempo', 'page': 15},
            {'nome': 'Sereia', 'page': 16},
        ]
    },
    {
        'nome': 'Ninja Caçador',
        'nome_en': 'Hunter-Nin',
        'tipo_conjurador': 'Baixo',
        'table_page': 28,
        'stats_page': 30,
        'core_start': 30,
        'core_end': 33,
        'class_end': 58,
        'extra_cols': ['ataque_letal'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Credo do Caçador',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Façanhas de Caçador', 'start': 50, 'end': 58},
        ],
        'archetypes': [
            {'nome': 'Guarda da Lâmina', 'page': 33},
            {'nome': 'Mão Necrótica', 'page': 35},
            {'nome': 'Perseguidor Grave', 'page': 37},
            {'nome': 'Arsenalista', 'page': 39},
            {'nome': 'Agente Funerário', 'page': 42},
            {'nome': 'Vice Agente', 'page': 44},
        ]
    },
    {
        'nome': 'Operativo de Inteligência',
        'nome_en': 'Intelligence Operative',
        'tipo_conjurador': 'Médio',
        'table_page': 58,
        'stats_page': 59,
        'core_start': 59,
        'core_end': 63,
        'class_end': 86,
        'extra_cols': ['planos_conhecidos', 'ordens_corajosas'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Estratégia',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Ordens Corajosas', 'start': 81, 'end': 86},
        ],
        'archetypes': [
            {'nome': 'Analista Azure', 'page': 63},
            {'nome': 'Doutor da Mente', 'page': 67},
            {'nome': 'Agente Clandestino', 'page': 69},
            {'nome': 'Tático Principal', 'page': 71},
            {'nome': 'Oráculo', 'page': 73},
            {'nome': 'Mestre Sobrenatural', 'page': 75},
            {'nome': 'Operativo das Sombras', 'page': 77},
            {'nome': 'Mestre do Jogo', 'page': 80},
        ]
    },
    {
        'nome': 'Ninja Médico',
        'nome_en': 'Medical-Nin',
        'tipo_conjurador': 'Alto',
        'table_page': 86,
        'stats_page': 87,
        'core_start': 87,
        'core_end': 91,
        'class_end': 101,
        'extra_cols': ['canalizando_cura', 'chakra_bisturi', 'dano_chakra_bisturi'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Doutrina Médica',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Princípios da Medicina', 'start': 91, 'end': 92},
        ],
        'archetypes': [
            {'nome': 'Médico Adepto', 'page': 91},
            {'nome': 'Medicina Negra', 'page': 92},
            {'nome': 'Médico de Combate', 'page': 93},
            {'nome': 'Medicina Natural', 'page': 95},
            {'nome': 'Xamã', 'page': 97},
            {'nome': 'Transmutador', 'page': 99},
        ]
    },
    {
        'nome': 'Especialista em Ninjutsu',
        'nome_en': 'Ninjutsu Specialist',
        'tipo_conjurador': 'Alto',
        'table_page': 101,
        'stats_page': 102,
        'core_start': 102,
        'core_end': 104,
        'class_end': 128,
        'extra_cols': ['ninjutsus_refinados', 'moldagem_eficiente'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Tradição Ninjutsu',
        'archetype_lvl': 2,
        'custom_categories': [
            {'nome': 'Moldagem Eficiente', 'start': 102, 'end': 104},
        ],
        'archetypes': [
            {'nome': 'Liberação de Incêndio', 'page': 104},
            {'nome': 'Especialização Hijutsu', 'page': 106},
            {'nome': 'Estilo Relâmpago', 'page': 108},
            {'nome': 'Especialização Hemomântica', 'page': 110},
            {'nome': 'Especialização em Fuinjutsu', 'page': 112},
            {'nome': 'Estilo Terra', 'page': 114},
            {'nome': 'Liberação do Vento', 'page': 116},
            {'nome': 'Convocação Fortalecida', 'page': 118},
            {'nome': 'Lançamento Versátil', 'page': 120},
            {'nome': 'Especialização Anulada', 'page': 122},
            {'nome': 'Estilo Água', 'page': 124},
        ]
    },
    {
        'nome': 'Ninja Batedor',
        'nome_en': 'Scout-Nin',
        'tipo_conjurador': 'Médio',
        'table_page': 128,
        'stats_page': 129,
        'core_start': 129,
        'core_end': 133,
        'class_end': 166,
        'extra_cols': [],
        'extra_pos': 'after_feat',
        'archetype_type': 'Técnica de Escotismo',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Técnicas de Escotismo', 'start': 130, 'end': 133},
        ],
        'archetypes': [
            {'nome': 'Escoteiro Árbitro', 'page': 133},
            {'nome': 'Escoteiro Clonador', 'page': 138},
            {'nome': 'Escoteiro Fantasma', 'page': 153},
            {'nome': 'Escoteiro Tático', 'page': 157},
            {'nome': 'Batedor Trapaceiro', 'page': 161},
        ]
    },
    {
        'nome': 'Especialista em Taijutsu',
        'nome_en': 'Taijutsu Specialist',
        'tipo_conjurador': 'Baixo',
        'table_page': 166,
        'stats_page': 167,
        'core_start': 167,
        'core_end': 171,
        'class_end': 188,
        'extra_cols': ['dado_marcial', 'tecnicas_marciais'],
        'extra_pos': 'before_feat',
        'archetype_type': 'Estilo Taijutsu',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Técnicas Marciais', 'start': 185, 'end': 188},
        ],
        'archetypes': [
            {'nome': 'Estilo Perturbação', 'page': 171},
            {'nome': 'Estilo Rígido', 'page': 172},
            {'nome': 'Estilo Natureza', 'page': 174},
            {'nome': 'Estilo Frenético', 'page': 177},
            {'nome': 'Estilo Anti-Chakra', 'page': 179},
            {'nome': 'Estilo Artes Marciais Mistas', 'page': 181},
            {'nome': 'Estilo Punhos de Ferro', 'page': 184},
        ]
    },
    {
        'nome': 'Especialista em Armas',
        'nome_en': 'Weapon Specialist',
        'tipo_conjurador': 'Baixo',
        'table_page': 188,
        'stats_page': 189,
        'core_start': 189,
        'core_end': 192,
        'class_end': 207,
        'extra_cols': ['estilos_conhecidos', 'dado_rajada'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Forma de Arma',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Estilos de Arma', 'start': 191, 'end': 193},
        ],
        'archetypes': [
            {'nome': 'Dançarino de Batalha', 'page': 192},
            {'nome': 'Perfurador de Gungnir', 'page': 194},
            {'nome': 'Martelo de Obsidiana', 'page': 195},
            {'nome': 'Lâmina Fantasma', 'page': 197},
            {'nome': 'Arma Primordial', 'page': 199},
            {'nome': 'Ranger', 'page': 201},
            {'nome': 'Samurai', 'page': 203},
            {'nome': 'Matador', 'page': 205},
        ]
    },
    {
        'nome': 'Mestre das Marionetes',
        'nome_en': 'Puppet Master',
        'tipo_conjurador': 'Médio',
        'table_page': 207,
        'stats_page': 208,
        'core_start': 208,
        'core_end': 213,
        'class_end': 278,
        'extra_cols': ['camada_madeira', 'camada_bronze', 'camada_prata', 'camada_ouro', 'camada_platina'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Técnica de Marionetes',
        'archetype_lvl': 2,
        'custom_categories': [
            {'nome': 'Aprimoramentos de Marionetes', 'start': 214, 'end': 230},
        ],
        'archetypes': [
            {'nome': 'Técnica Negra', 'page': 213},
            {'nome': 'Técnica Verde', 'page': 231},
            {'nome': 'Técnica Púrpura', 'page': 240},
            {'nome': 'Técnica Vermelha', 'page': 251},
        ]
    },
    {
        'nome': 'Ninja Cozinheiro',
        'nome_en': 'Cooking-Nin',
        'tipo_conjurador': 'Médio',
        'table_page': 278,
        'stats_page': 279,
        'core_start': 279,
        'core_end': 283,
        'class_end': 306,
        'extra_cols': ['dado_cozinha'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Foco de Culinária',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Lanches Shinobi', 'start': 280, 'end': 283},
        ],
        'archetypes': [
            {'nome': 'Lanches Rápidos', 'page': 285},
            {'nome': 'Cheiro Doce', 'page': 287},
            {'nome': 'Lanches à Base de Ervas', 'page': 289},
            {'nome': 'Lanches Fritos', 'page': 292},
            {'nome': 'Lanches Grandiosos', 'page': 302},
            {'nome': 'Lanches Congelados', 'page': 304},
        ]
    },
    {
        'nome': 'Ninja Cientista',
        'nome_en': 'Science-Nin',
        'tipo_conjurador': 'Médio',
        'table_page': 306,
        'stats_page': 307,
        'core_start': 307,
        'core_end': 310,
        'class_end': 342,
        'extra_cols': ['pontos_criacao'],
        'extra_pos': 'after_feat',
        'archetype_type': 'Inquérito Científico',
        'archetype_lvl': 3,
        'custom_categories': [
            {'nome': 'Ferramentas Científicas Ninja', 'start': 334, 'end': 342},
        ],
        'archetypes': [
            {'nome': 'Alquimista', 'page': 310},
            {'nome': 'Shinobi de Metal Completo', 'page': 315},
            {'nome': 'Fantasma na Concha', 'page': 320},
            {'nome': 'Especialista em Armadilhas', 'page': 324},
            {'nome': 'Arsenal Aprimorado', 'page': 329},
            {'nome': 'Mestria Biótica', 'page': 333},
        ]
    },
]

LEVEL_PATTERN = re.compile(r'\b(1st|2nd|3rd|[4-9]th|1\dth|20th)\b')


def parse_progression_table(doc: pymupdf.Document, cfg: Dict[str, Any]) -> List[ClassProgressionRow]:
    """Extrai as 20 linhas da tabela de progressão de nível de uma classe."""
    page = doc[cfg['table_page'] - 1]
    txt = page.get_text('text')
    matches = list(LEVEL_PATTERN.finditer(txt))
    
    rows = []
    num_extras = len(cfg['extra_cols'])
    extra_pos = cfg['extra_pos']
    
    for i in range(len(matches)):
        start = matches[i].start()
        if i + 1 < len(matches):
            end = matches[i+1].start()
        else:
            rank_s = txt.find('Rank-S', start)
            if rank_s != -1:
                end = rank_s + len('Rank-S') + 10
            else:
                end = start + 250
        
        chunk = txt[start:end].strip()
        lines = [l.strip() for l in chunk.split('\n') if l.strip()]
        if not lines:
            continue
            
        lvl_str = lines[0]
        lvl_match = re.search(r'\d+', lvl_str)
        lvl_num = int(lvl_match.group(0)) if lvl_match else (i + 1)
        
        if '+3' in lvl_str:
            prof_bonus = '+3'
            idx = 1
        elif len(lines) > 1 and lines[1].startswith('+'):
            prof_bonus = lines[1]
            idx = 2
        else:
            prof_bonus = '+3' if lvl_num <= 3 else ('+4' if lvl_num <= 6 else ('+5' if lvl_num <= 9 else ('+6' if lvl_num <= 12 else ('+7' if lvl_num <= 15 else ('+8' if lvl_num <= 18 else '+9')))))
            idx = 1
            
        # Encontra rank e quantidade de jutsus no final da linha
        rank_idx = -1
        rank_val = None
        for j in range(len(lines) - 1, idx - 1, -1):
            if re.search(r'Rank-[DCBAS]', lines[j], re.IGNORECASE):
                rank_idx = j
                rank_val = lines[j]
                break
        
        if rank_idx != -1:
            jutsus_val = None
            if rank_idx > idx:
                val_cand = lines[rank_idx - 1]
                if val_cand.isdigit():
                    jutsus_val = int(val_cand)
                    tail_start = rank_idx - 1
                else:
                    tail_start = rank_idx
            else:
                tail_start = rank_idx
        else:
            if lines[-1].isdigit():
                jutsus_val = int(lines[-1])
                tail_start = len(lines) - 1
            else:
                jutsus_val = None
                tail_start = len(lines)

        middle_tokens = lines[idx:tail_start]
        extra_vals = {}
        
        if extra_pos == 'before_feat':
            if len(middle_tokens) >= num_extras:
                for k in range(num_extras):
                    val = middle_tokens[k]
                    extra_vals[cfg['extra_cols'][k]] = None if val in ['–', '-', ''] else val
                feature_tokens = middle_tokens[num_extras:]
            else:
                feature_tokens = middle_tokens
        else:
            # extra_pos == 'after_feat'
            # Só extrai se o token se parecer com valor de coluna (dado, número, traço)
            if len(middle_tokens) >= num_extras:
                # Checa se os últimos num_extras tokens são valores válidos
                cand_extras = middle_tokens[-num_extras:]
                valid_extra = True
                for ce in cand_extras:
                    if not (re.match(r'^[\d+\-–]+$', ce) or re.search(r'\d*d\d+', ce)):
                        valid_extra = False
                        break
                
                if valid_extra:
                    feat_count = len(middle_tokens) - num_extras
                    feature_tokens = middle_tokens[:feat_count]
                    for k in range(num_extras):
                        val = cand_extras[k]
                        extra_vals[cfg['extra_cols'][k]] = None if val in ['–', '-', ''] else val
                else:
                    feature_tokens = middle_tokens
                    for k in range(num_extras):
                        extra_vals[cfg['extra_cols'][k]] = None
            else:
                feature_tokens = middle_tokens
                for k in range(num_extras):
                    extra_vals[cfg['extra_cols'][k]] = None
                
        features_raw = ' '.join(feature_tokens)
        feats = [f.strip() for f in re.split(r'[,;]\s*', features_raw) if f.strip() and f.strip() not in ['–', '-']]
        
        rows.append(ClassProgressionRow(
            nivel=lvl_num,
            bonus_proficiencia=prof_bonus,
            caracteristicas=feats,
            jutsu_conhecidos=jutsus_val,
            rank_max_jutsu=rank_val,
            colunas_extras=extra_vals
        ))
    return rows


def parse_base_info(doc: pymupdf.Document, stats_page: int) -> Dict[str, Any]:
    """Extrai dados de vida, chakra, proficiências e equipamento da página de estatísticas da classe."""
    page = doc[stats_page - 1]
    page_text = page.get_text('text')
    
    # Se a página de estatísticas não tiver 'Pontos de Vida', checa a página anterior
    if 'Pontos de Vida' not in page_text and 'PONTOS DE VIDA' not in page_text and stats_page > 1:
        prev_text = doc[stats_page - 2].get_text('text')
        if 'Pontos de Vida' in prev_text or 'PONTOS DE VIDA' in prev_text:
            page_text = prev_text + "\n" + page_text

    # Isola o bloco de proficiências especificamente
    prof_idx = -1
    for m in re.finditer(r'PROFICI[ÊE]NCIA[S]?|Profici[êe]ncia[s]?', page_text):
        prof_idx = m.start()
        break
        
    prof_text = page_text[prof_idx:] if prof_idx != -1 else page_text

    hd_m = re.search(r'Dado[s]? de Vida:\s*([^\n\r]+)', page_text, re.IGNORECASE)
    hd = hd_m.group(1).split('por')[0].strip() if hd_m else "1d8"
    
    cd_m = re.search(r'Dado[s]? de Chakra:\s*([^\n\r]+)', page_text, re.IGNORECASE)
    cd = cd_m.group(1).split('por')[0].strip() if cd_m else "1d8"
    
    hp1_m = re.search(r'(?:Pontos de [Vv]ida (?:no|a partir do) 1[ºo°] [Nn][íi]vel[^:]*:\s*)([^\n\r]+)', page_text, re.IGNORECASE)
    hp1 = hp1_m.group(1).strip() if hp1_m else None
    
    chk1_m = re.search(r'(?:Pontos de [Cc]hakra no 1[ºo°] [Nn][íi]vel:\s*)([^\n\r]+)', page_text, re.IGNORECASE)
    chk1 = chk1_m.group(1).strip() if chk1_m else None
    
    arm_m = re.search(r'(?:Armadura|Armaduras)[:\s]+([^\n\r]+)', prof_text, re.IGNORECASE)
    arm = arm_m.group(1).strip() if arm_m else None
    if arm and 'Armas' in arm:
        arm = arm.split('Armas')[0].strip()
    
    wpn_m = re.search(r'(?:Armas)[:\s]+([^\n\r]+(?:\n[^\n\r]+)?)', prof_text, re.IGNORECASE)
    wpn = wpn_m.group(1).replace('\n', ' ').strip() if wpn_m else None
    if wpn and 'Ferramenta' in wpn:
        wpn = wpn.split('Ferramenta')[0].strip()
        
    tls_m = re.search(r'(?:Ferramentas(?: Ninja)?)[:\s]+([^\n\r]+(?:\n[^\n\r]+)?)', prof_text, re.IGNORECASE)
    tls = tls_m.group(1).replace('\n', ' ').strip() if tls_m else None
    if tls and ('Teste' in tls or 'Arremesso' in tls):
        tls = re.split(r'Teste|Arremesso', tls)[0].strip()
        
    st_m = re.search(r'(?:Testes de resist[êe]ncia|Arremessos salvadores)[:\s]+([^\n\r]+(?:\n[^\n\r]+)?)', prof_text, re.IGNORECASE)
    saves = []
    if st_m:
        raw_st = st_m.group(1).replace('\n', ' ').strip()
        if 'Habilidade' in raw_st or 'Perícia' in raw_st:
            raw_st = re.split(r'Habilidade|Perícia', raw_st)[0].strip()
        for attr in ['Força', 'Destreza', 'Constituição', 'Inteligência', 'Sabedoria', 'Carisma']:
            if re.search(attr[:4], raw_st, re.IGNORECASE):
                saves.append(attr)
                
    skl_m = re.search(r'(?:Habilidades|Per[íi]cias)[:\s]+([^\n\r]+(?:\n[^\n\r]+)?)', prof_text, re.IGNORECASE)
    skl = skl_m.group(1).replace('\n', ' ').strip() if skl_m else None
    if skl and 'Equipamento' in skl:
        skl = skl.split('Equipamento')[0].strip()
        
    eqp_m = re.search(r'(?:Equipamento|Equipamentos)\s+(?:Você começa com[^\n\r]+:)?\s*([^\n\r]+(?:\n[^\n\r]+){1,6})', prof_text, re.IGNORECASE)
    eqp = eqp_m.group(0).replace('\n', ' ').strip() if eqp_m else None
    if eqp and 'FUNDIÇÃO' in eqp.upper():
        eqp = eqp.split('FUNDIÇÃO')[0].strip()
        
    return {
        'dado_vida': hd,
        'dado_chakra': cd,
        'hp_primeiro_nivel': hp1 or f"{hd.split('d')[-1]} + mod Constituição",
        'chakra_primeiro_nivel': chk1 or f"{cd.split('d')[-1]} + mod Constituição",
        'proficiencias_armaduras': arm,
        'proficiencias_armas': wpn,
        'proficiencias_ferramentas': tls,
        'testes_resistencia': saves,
        'pericias_escolha': skl,
        'equipamento_inicial': eqp
    }


def parse_core_features(doc: pymupdf.Document, start_page: int, end_page: int) -> List[FeatureDetail]:
    """Extrai características de classe base entre start_page e end_page."""
    features = []
    for p_no in range(start_page - 1, end_page):
        page = doc[p_no]
        blocks = page.get_text('blocks')
        
        left = sorted([b for b in blocks if b[0] < 300 and b[1] > 30 and b[3] < 810], key=lambda b: b[1])
        right = sorted([b for b in blocks if b[0] >= 300 and b[1] > 30 and b[3] < 810], key=lambda b: b[1])
        all_b = left + right
        
        i = 0
        while i < len(all_b):
            b = all_b[i]
            txt = b[4].strip()
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            
            # Checa se é cabeçalho de recurso de classe
            if len(lines) == 1 and 3 < len(lines[0]) < 45 and not lines[0].isdigit():
                title = lines[0]
                if not any(k in title.upper() for k in [
                    'PONTOS DE VIDA', 'PONTOS DE CHAKRA', 'PROFICI', 'EQUIP', 'NINJUTSU',
                    'GENJUTSU', 'TAIJUTSU', 'INSPIRAÇÕES', 'CRIANDO', 'CONSTRUÇÃO RÁPIDA',
                    'CARACTERÍSTICAS DA CLASSE', 'RECURSOS DE CLASSE', 'TABELA'
                ]):
                    # Agrupa parágrafos subsequentes até o próximo título
                    desc_parts = []
                    j = i + 1
                    while j < len(all_b):
                        next_b = all_b[j]
                        next_lines = [l.strip() for l in next_b[4].strip().split('\n') if l.strip()]
                        if len(next_lines) == 1 and 3 < len(next_lines[0]) < 45 and not next_lines[0].isdigit():
                            break
                        desc_parts.append(next_b[4].strip().replace('\n', ' '))
                        j += 1
                        
                    desc = ' '.join(desc_parts).strip()
                    if desc:
                        lvl_m = re.search(r'\b(?:a partir do|no|a começar no|começando no)\s+(\d+)[ºo°]?\s+n[íi]vel', desc, re.IGNORECASE)
                        lvl = int(lvl_m.group(1)) if lvl_m else None
                        
                        uses_m = re.search(r'(\d+|uma vez|duas vezes|três vezes|número de vezes[^\n\r.]+)\s+por\s+(?:descanso\s+(?:curto\s+ou\s+longo|curto|longo)|descanso)', desc, re.IGNORECASE)
                        uses = uses_m.group(0).strip() if uses_m else None
                        
                        features.append(FeatureDetail(
                            nome=title,
                            nivel=lvl,
                            descricao=desc,
                            usos=uses
                        ))
                    i = j
                    continue
            i += 1
    return features


def parse_archetypes(doc: pymupdf.Document, cfg: Dict[str, Any]) -> List[Archetype]:
    """Extrai todos os arquétipos e seus recursos para uma determinada classe."""
    archetypes = []
    arch_list = cfg['archetypes']
    
    for idx, arch_info in enumerate(arch_list):
        arch_name = arch_info['nome']
        next_arch_name = arch_list[idx + 1]['nome'] if idx + 1 < len(arch_list) else None
        p_start = arch_info['page']
        
        # Define limite de páginas para não vazar nas opções modulares
        custom_starts = [c['start'] for c in cfg.get('custom_categories', []) if c['start'] >= p_start]
        if idx + 1 < len(arch_list):
            p_end = arch_list[idx + 1]['page']
        elif custom_starts:
            p_end = min(custom_starts)
        else:
            p_end = min(cfg.get('class_end', p_start + 4), p_start + 4)
        
        # Coleta blocos
        all_blocks = []
        for p in range(p_start - 1, min(len(doc), p_end)):
            page = doc[p]
            blocks = page.get_text('blocks')
            left = sorted([b for b in blocks if b[0] < 300 and b[1] > 30 and b[3] < 810], key=lambda b: b[1])
            right = sorted([b for b in blocks if b[0] >= 300 and b[1] > 30 and b[3] < 810], key=lambda b: b[1])
            all_blocks.extend(left + right)
            
        features = []
        arch_desc = ""
        
        i = 0
        while i < len(all_blocks):
            b = all_blocks[i]
            txt = b[4].strip()
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            if not lines:
                i += 1
                continue
                
            first_line = lines[0]
            # Se atingir o próximo arquétipo, interrompe a extração deste arquétipo
            if next_arch_name:
                norm_next = re.sub(r'[^a-zA-Z0-9]', '', next_arch_name.lower())[:8]
                norm_line = re.sub(r'[^a-zA-Z0-9]', '', first_line.lower())
                if norm_next in norm_line:
                    break

            # Se atingir uma seção modular da classe (ex: Início do Genjutsu, Miragens, etc.), encerra
            reached_custom = False
            for ccat in cfg.get('custom_categories', []):
                norm_cat = re.sub(r'[^a-zA-Z0-9]', '', ccat['nome'].lower())[:8]
                if norm_cat in re.sub(r'[^a-zA-Z0-9]', '', first_line.lower()):
                    reached_custom = True
                    break
            if reached_custom:
                break

            # Se for o título do arquétipo em si
            if arch_name.upper() in first_line.upper() or first_line.upper() in arch_name.upper():
                # Descrição introdutória mecânica
                if i + 1 < len(all_blocks):
                    arch_desc = all_blocks[i+1][4].strip().replace('\n', ' ')
                i += 2
                continue
                
            # Se for um título de recurso do arquétipo
            if len(lines) == 1 and 3 < len(first_line) < 45 and not first_line.isdigit():
                title = first_line
                if not any(k in title.upper() for k in ['TABELA', 'PÁGINA', cfg['archetype_type'].upper()]):
                    desc_parts = []
                    j = i + 1
                    while j < len(all_blocks):
                        next_b = all_blocks[j]
                        next_lines = [l.strip() for l in next_b[4].strip().split('\n') if l.strip()]
                        if len(next_lines) == 1 and 3 < len(next_lines[0]) < 45 and not next_lines[0].isdigit():
                            break
                        desc_parts.append(next_b[4].strip().replace('\n', ' '))
                        j += 1
                        
                    desc = ' '.join(desc_parts).strip()
                    if desc:
                        lvl_m = re.search(r'\b(?:a partir do|no|a começar no|começando no|ao escolher[^\n\r]+?no|quando você escolhe[^\n\r]+?no)\s+(\d+)[ºo°]?\s+n[íi]vel', desc, re.IGNORECASE)
                        lvl = int(lvl_m.group(1)) if lvl_m else cfg['archetype_lvl']
                        
                        uses_m = re.search(r'(\d+|uma vez|duas vezes|três vezes|número de vezes[^\n\r.]+)\s+por\s+(?:descanso\s+(?:curto\s+ou\s+longo|curto|longo)|descanso)', desc, re.IGNORECASE)
                        uses = uses_m.group(0).strip() if uses_m else None
                        
                        features.append(FeatureDetail(
                            nome=title,
                            nivel=lvl,
                            descricao=desc,
                            usos=uses
                        ))
                    i = j
                    continue
            i += 1
            
        archetypes.append(Archetype(
            nome=arch_name,
            classe_nome=cfg['nome'],
            tipo_arquetipo=cfg['archetype_type'],
            nivel_obtencao=cfg['archetype_lvl'],
            descricao_mecanica=arch_desc or f"Arquétipo {arch_name} da classe {cfg['nome']}.",
            caracteristicas=features,
            pagina=p_start
        ))
    return archetypes


def parse_modular_options(doc: pymupdf.Document, cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai opções customizáveis modulares da classe (Miragens, Façanhas, Ordens, etc.)."""
    options = []
    cats = cfg.get('custom_categories', [])
    for cat in cats:
        c_name = cat['nome']
        s_p = cat['start']
        e_p = cat['end']
        
        for p in range(s_p - 1, min(len(doc), e_p)):
            page = doc[p]
            blocks = page.get_text('blocks')
            left = sorted([b for b in blocks if b[0] < 300 and b[1] > 30 and b[3] < 810], key=lambda b: b[1])
            right = sorted([b for b in blocks if b[0] >= 300 and b[1] > 30 and b[3] < 810], key=lambda b: b[1])
            all_b = left + right
            
            i = 0
            while i < len(all_b):
                b = all_b[i]
                lines = [l.strip() for l in b[4].strip().split('\n') if l.strip()]
                if len(lines) == 1 and 3 < len(lines[0]) < 45 and not lines[0].isdigit():
                    title = lines[0]
                    if i + 1 < len(all_b):
                        body = all_b[i+1][4].strip().replace('\n', ' ')
                        options.append({
                            'categoria': c_name,
                            'nome': title,
                            'descricao': body,
                            'pagina': p + 1
                        })
                        i += 2
                        continue
                i += 1
    return options


def parse_class_talents(doc: pymupdf.Document) -> List[ClassTalent]:
    """Extrai todos os talentos de classe e de arquétipo das páginas 342-358."""
    talents = []
    full_text = ""
    for p in range(341, len(doc)):
        full_text += f"\n[PAG_{p+1}]\n" + doc[p].get_text('text')
        
    cat_matches = list(re.finditer(r'Categoria:\s*([^\n\r]+)', full_text, re.IGNORECASE))
    
    current_page = 343
    for i, m in enumerate(cat_matches):
        cat_type = m.group(1).strip()
        start = m.start()
        
        # Encontra o título antes de 'Categoria:'
        before_text = full_text[:start]
        # Atualiza número de página atual
        page_tags = list(re.finditer(r'\[PAG_(\d+)\]', before_text))
        if page_tags:
            current_page = int(page_tags[-1].group(1))
            
        before_lines = [l.strip() for l in before_text.split('\n') if l.strip() and not l.strip().startswith('[PAG_')]
        title = before_lines[-1] if before_lines else "Talento Sem Nome"
        if title.isupper() and len(before_lines) > 1 and len(before_lines[-2]) < 40 and before_lines[-2].isupper():
            # Possível título quebrado em 2 linhas
            if not any(k in before_lines[-2] for k in ['ARQUÉTIPO', 'TALENTOS', 'CONJUNTOR', 'MARCIAL']):
                title = f"{before_lines[-2]} {title}"
                
        # Limite até o próximo talento
        if i + 1 < len(cat_matches):
            next_start = cat_matches[i+1].start()
            # O texto deste talento termina antes das linhas de título do próximo
            next_before = full_text[:next_start].split('\n')
            # remove últimas 2 linhas (que pertencem ao título do próximo)
            chunk = full_text[m.end():next_start].strip()
        else:
            chunk = full_text[m.end():].strip()
            
        # Parse Arquétipo/Classe, Pré-requisito e Descrição
        arch_req = None
        arch_m = re.search(r'(?:Arquétipo|Classe)[:\s]+([^\n\r]+)', chunk, re.IGNORECASE)
        if arch_m:
            arch_req = arch_m.group(1).strip()
            
        prereq = None
        pre_m = re.search(r'Pr[ée]-requisito[s]?[:\s]+([^\n\r]+(?:\n[^\n\r]+)?)', chunk, re.IGNORECASE)
        if pre_m:
            prereq = pre_m.group(1).replace('\n', ' ').strip()
            
        # Remove cabeçalhos de Categoria/Arquétipo/Pré-requisito do corpo
        clean_lines = []
        for line in chunk.split('\n'):
            line_str = line.strip()
            if not line_str or line_str.startswith('[PAG_'):
                continue
            if any(line_str.lower().startswith(pfx) for pfx in ['arquétipo:', 'classe:', 'pré-requisito:', 'prerequisito:', 'categoria:']):
                continue
            clean_lines.append(line_str)
            
        # Se as últimas linhas forem em maiúsculas (título do próximo talento), remove-as
        while clean_lines and len(clean_lines[-1]) < 45 and clean_lines[-1].isupper() and not clean_lines[-1].endswith('.'):
            clean_lines.pop()
            
        desc = ' '.join(clean_lines).strip()
        
        # Limpa o título caso tenha herdado cabeçalho de classe ou do livro
        for c in CLASSES_CONFIG:
            c_upper = c['nome'].upper()
            if title.upper().startswith(c_upper):
                title = title[len(c_upper):].strip()
            c_en_upper = c['nome_en'].upper() if c['nome_en'] else ""
            if c_en_upper and title.upper().startswith(c_en_upper):
                title = title[len(c_en_upper):].strip()
        for pfx in ['TALENTOS DE CLASSE', 'DO ARQUÉTIPO', 'TALENTOS']:
            if title.upper().startswith(pfx):
                title = title[len(pfx):].strip()
        title = title.strip() or "Talento de Classe"
        
        # Mapeia classe associada
        classe_associada = "Geral"
        if arch_req:
            for c in CLASSES_CONFIG:
                if c['nome'].lower() in arch_req.lower() or c['nome_en'].lower() in arch_req.lower():
                    classe_associada = c['nome']
                    break
        
        talents.append(ClassTalent(
            nome=title,
            tipo=cat_type,
            classe=classe_associada,
            arquetipo_requerido=arch_req,
            prerequisitos=prereq,
            descricao_mecanica=desc,
            pagina=current_page
        ))
        
    return talents


def parse_all_classes(pdf_path: str = "PDFs/Classes.pdf") -> Tuple[List[ClassEntity], List[Archetype], List[ClassTalent]]:
    """Executa a extração completa de Classes, Arquétipos e Talentos de Classe."""
    doc = pymupdf.open(pdf_path)
    
    classes: List[ClassEntity] = []
    all_archetypes: List[Archetype] = []
    
    for cfg in CLASSES_CONFIG:
        # 1. Tabela de progressão
        prog_rows = parse_progression_table(doc, cfg)
        
        # 2. Informações base e proficiências
        base_info = parse_base_info(doc, cfg['stats_page'])
        
        # 3. Recursos de classe base
        core_feats = parse_core_features(doc, cfg['core_start'], cfg['core_end'])
        
        # 4. Opções modulares customizáveis
        custom_opts = parse_modular_options(doc, cfg)
        
        # 5. Arquétipos
        archs = parse_archetypes(doc, cfg)
        all_archetypes.extend(archs)
        
        # Monta a entidade
        cls_entity = ClassEntity(
            nome=cfg['nome'],
            nome_en=cfg['nome_en'],
            tipo_conjurador=cfg['tipo_conjurador'],
            dado_vida=base_info['dado_vida'],
            dado_chakra=base_info['dado_chakra'],
            hp_primeiro_nivel=base_info['hp_primeiro_nivel'],
            chakra_primeiro_nivel=base_info['chakra_primeiro_nivel'],
            proficiencias_armaduras=base_info['proficiencias_armaduras'],
            proficiencias_armas=base_info['proficiencias_armas'],
            proficiencias_ferramentas=base_info['proficiencias_ferramentas'],
            testes_resistencia=base_info['testes_resistencia'],
            pericias_escolha=base_info['pericias_escolha'],
            equipamento_inicial=base_info['equipamento_inicial'],
            tabela_progressao=prog_rows,
            caracteristicas_classe=core_feats,
            recursos_customizacao=custom_opts,
            pagina_inicio=cfg['table_page']
        )
        classes.append(cls_entity)
        
    # 6. Talentos de classe
    talents = parse_class_talents(doc)
    
    doc.close()
    return classes, all_archetypes, talents
