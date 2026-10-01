import sys
import os
import json

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractor.clan_parser import parse_all_clans, parse_all_latent_bloodlines

def main():
    print("=== TESTE DE EXTRAÇÃO DE CLÃS E LINHAGENS LATENTES ===")

    pdf_path = "PDFs/Clas.pdf"
    clans = parse_all_clans(pdf_path)
    print(f"\n✅ Total de clãs extraídos: {len(clans)}")

    # Exibir amostra de clãs clássicos
    amostras = [c for c in clans if c.nome in ["Aburame", "Akimichi", "Hyūga", "Nara", "Uchiha", "Sem Clã"]]
    for c in amostras:
        print(f"\n🍃 CLÃ: {c.nome} (Página {c.pagina})")
        print(f"   Atributos: {c.aumento_atributos} | Raw: '{c.aumento_atributos_raw}'")
        print(f"   Velocidade: {c.deslocamento}")
        if c.pericias:
            print(f"   Perícias: {', '.join(c.pericias)}")
        print(f"   Recursos Mecânicos ({len(c.recursos)}):")
        for f in c.recursos[:4]:
            usos = f" ({f.usos})" if f.usos else ""
            print(f"     • {f.nome} [Nível {f.nivel}]{usos}")

    print("\n" + "=" * 60)
    print("Extraindo Linhagens Sanguíneas Latentes...")
    latent = parse_all_latent_bloodlines(pdf_path)
    print(f"✅ Total de traços latentes extraídos: {len(latent)}")
    for t in latent[:6]:
        req = f" [Req: {t['pre_requisito']}]" if t['pre_requisito'] else ""
        print(f"   • [{t['cla']}] {t['nome_habilidade']} (Custo: {t['custo_pontos']} pts){req}")
        print(f"     -> {t['descricao'][:90]}...")

if __name__ == "__main__":
    main()
