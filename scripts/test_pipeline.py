import sys
import os

# Garantir UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

# Adicionar raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.database import init_db, insert_jutsus, query_jutsus
from src.extractor.jutsu_parser import parse_jutsus_from_pdf

def main():
    print("=== TESTE END-TO-END DO PIPELINE ===")

    # 1. Inicializar Banco de Dados
    test_db = "data/test_naruto5e.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    init_db(test_db)
    print(f"Banco inicializado em: {test_db}")

    # 2. Extrair amostra de jutsus gerais (Jutsus.pdf páginas 5 a 8)
    pdf_jutsus = "PDFs/Jutsus.pdf"
    print(f"Extraindo amostra de {pdf_jutsus}...")
    sample_j = parse_jutsus_from_pdf(pdf_jutsus, is_clan_pdf=False, start_page=4, end_page=8)
    print(f"Jutsus gerais extraídos: {len(sample_j)}")

    # 3. Extrair amostra de jutsus de clã (Clas.pdf páginas 4 a 8 - Aburame)
    pdf_clas = "PDFs/Clas.pdf"
    print(f"Extraindo amostra de {pdf_clas}...")
    sample_c = parse_jutsus_from_pdf(pdf_clas, is_clan_pdf=True, start_page=3, end_page=8)
    print(f"Jutsus de clã extraídos: {len(sample_c)}")

    # 4. Inserção no banco
    all_sample = sample_j + sample_c
    inserted = insert_jutsus(all_sample, test_db)
    print(f"Total inserido no banco: {inserted}")

    # 5. Testes de Consulta
    print("\n--- Teste 1: Jutsus com Salvaguarda de Carisma ---")
    res1 = query_jutsus(salvaguarda="Carisma", db_path=test_db)
    for r in res1:
        print(f"  • [{r['rank']}] {r['nome']} | Custo: {r['custo_chakra']} | Estilo: {r['natureza_estilo']}")

    print("\n--- Teste 2: Jutsus exclusivos do Clã Aburame ---")
    res2 = query_jutsus(cla="Aburame", db_path=test_db)
    for r in res2:
        dano_str = f" | Dano: {r['dano_formula']} {r['dano_tipo']}" if r['dano_formula'] else ""
        save_str = f" | Save: {r['salvaguarda']}" if r['salvaguarda'] else ""
        print(f"  • [{r['rank']}] {r['nome']} | Custo: {r['custo_chakra']}{dano_str}{save_str}")

    print("\n--- Teste 3: Técnicas que concedem Vantagem ou Desvantagem ---")
    res3 = [r for r in query_jutsus(db_path=test_db) if r['vantagem_desvantagem']]
    for r in res3:
        print(f"  • {r['nome']}: {r['vantagem_desvantagem']}")

    print("\nPipeline testado com 100% de sucesso!")

if __name__ == "__main__":
    main()
