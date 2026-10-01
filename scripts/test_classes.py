import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractor.class_parser import parse_all_classes

t0 = time.time()
print("Iniciando extração de Classes, Arquétipos e Talentos...")
classes, archetypes, talents = parse_all_classes("PDFs/Classes.pdf")
t1 = time.time()

print(f"\nExtração concluída em {t1 - t0:.2f}s!")
print(f"Classes extraídas: {len(classes)}")
print(f"Arquétipos extraídos: {len(archetypes)}")
print(f"Talentos de classe extraídos: {len(talents)}")

print("\n=== RESUMO DAS 11 CLASSES ===")
for c in classes:
    print(f"\n--- {c.nome} ({c.nome_en}) ---")
    print(f"  Tipo Conjurador: {c.tipo_conjurador} | HD: {c.dado_vida} | CD: {c.dado_chakra}")
    print(f"  HP Nível 1: {c.hp_primeiro_nivel} | Chakra Nível 1: {c.chakra_primeiro_nivel}")
    print(f"  Saves: {c.testes_resistencia}")
    print(f"  Armaduras: {c.proficiencias_armaduras}")
    print(f"  Armas: {c.proficiencias_armas[:60] if c.proficiencias_armas else 'None'}...")
    print(f"  Níveis na tabela: {len(c.tabela_progressao)}")
    print(f"  Recursos base: {len(c.caracteristicas_classe)}")
    print(f"  Opções modulares: {len(c.recursos_customizacao)}")
    
    # Amostra nível 1 e nível 20
    lvl1 = c.tabela_progressao[0]
    lvl20 = c.tabela_progressao[-1]
    print(f"  Progresso L1: PB={lvl1.bonus_proficiencia}, Jutsus={lvl1.jutsu_conhecidos}, Rank={lvl1.rank_max_jutsu}, Feats={lvl1.caracteristicas}")
    print(f"  Progresso L20: PB={lvl20.bonus_proficiencia}, Jutsus={lvl20.jutsu_conhecidos}, Rank={lvl20.rank_max_jutsu}, Feats={lvl20.caracteristicas}")

print("\n=== AMOSTRA DE ARQUÉTIPOS ===")
for a in archetypes[:6]:
    print(f"\nArquétipo: {a.nome} ({a.classe_nome}) - Tipo: {a.tipo_arquetipo} (Nível {a.nivel_obtencao})")
    print(f"  Recursos ({len(a.caracteristicas)}): {[f.nome for f in a.caracteristicas]}")
    if a.caracteristicas:
        f0 = a.caracteristicas[0]
        print(f"  Amostra 1º Recurso: {f0.nome} (Nível {f0.nivel}) -> {f0.descricao[:80]}...")

print("\n=== AMOSTRA DE TALENTOS DE CLASSE ===")
for t in talents[:6]:
    print(f"\nTalento: {t.nome} | Tipo: {t.tipo} | Classe: {t.classe}")
    print(f"  Pré-requisito: {t.prerequisitos}")
    print(f"  Descrição: {t.descricao_mecanica[:100]}...")
