import argparse
import sys
import json
import unicodedata
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

from src.db.database import (
    query_jutsus,
    query_clans,
    query_latent_bloodlines,
    get_class,
    list_classes,
    query_archetypes,
    query_class_talents,
    query_weapons,
    query_armors,
    query_fuinjutsu_seals,
    query_conditions,
    get_combat_rule,
    list_combat_rules,
    create_error_report,
    list_error_reports,
    update_error_report_status,
    get_or_create_user,
    ensure_tables,
    DEFAULT_DB_PATH
)


def strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def display_clan_info(cla_nome: str, db_path: str):
    all_clans = query_clans(db_path=db_path)
    clean_target = strip_accents(cla_nome).lower()
    clans = [c for c in all_clans if clean_target in strip_accents(c['nome']).lower()]
    if not clans:
        print(f"\n❌ Nenhum clã encontrado com o nome '{cla_nome}'.")
        return

    c = clans[0]
    print(f"\n🧬 FICHA MECÂNICA DO CLÃ: {c['nome'].upper()}")
    print("=" * 80)
    print(f"📖 Livro de Origem: Estudos da Tsunade (Página {c['pagina']})")
    print(f"⚡ Bônus de Atributos: {c['aumento_atributos_raw']}")
    print(f"🏃 Deslocamento Base: {c['deslocamento']}")
    if c['pericias']:
        print(f"🎯 Perícias Concedidas: {', '.join(c['pericias'])}")

    print(f"\n🛡️ Recursos Mecânicos do Clã ({len(c['recursos'])}):")
    for f in c['recursos']:
        usos_str = f" [Usos: {f['usos']}]" if f.get('usos') else ""
        print(f"\n  • {f['nome']} (Nível {f.get('nivel', 1)}){usos_str}")
        print(f"    {f['descricao']}")

    # Jutsus exclusivos desse clã
    jutsus = query_jutsus(cla=c['nome'], db_path=db_path)
    print(f"\n🔥 Jutsus Exclusivos do Clã ({len(jutsus)} técnicas):")
    for j in jutsus:
        dano_str = f" | Dano: {j['dano_formula']} {j['dano_tipo']}" if j['dano_formula'] else ""
        save_str = f" | Save: {j['salvaguarda']}" if j['salvaguarda'] else ""
        print(f"  [{j['rank']}] {j['nome']} (Custo: {j['custo_chakra']} Chakra, Ação: {j['tempo_conjuracao']}){dano_str}{save_str}")

    # Linhagem Latente disponível
    latent = query_latent_bloodlines(cla=c['nome'], db_path=db_path)
    if latent:
        print(f"\n🩸 Habilidades de Linhagem Latente ({len(latent)} traços disponíveis):")
        for t in latent:
            req_str = f" [Pré-requisito: {t['pre_requisito']}]" if t.get('pre_requisito') else ""
            print(f"  • {t['nome_habilidade']} (Custo: {t['custo_pontos']} pts){req_str}")
            print(f"    {t['descricao']}")

    print("=" * 80)


def display_clan_comparison(cla_names: str, db_path: str):
    names = [n.strip() for n in cla_names.split(",") if n.strip()]
    if not names:
        print("\n❌ Forneça pelo menos um nome de clã para comparar.")
        return

    all_clans = query_clans(db_path=db_path)
    compared = []
    for n in names:
        clean = strip_accents(n).lower()
        matches = [c for c in all_clans if clean in strip_accents(c['nome']).lower()]
        if matches:
            c = matches[0]
            jutsus = query_jutsus(cla=c['nome'], db_path=db_path)
            latentes = query_latent_bloodlines(cla=c['nome'], db_path=db_path)
            ranks_set = sorted(list(set(j['rank'].replace("Rank-", "") for j in jutsus)))
            avg_chakra = round(sum(j['custo_chakra'] for j in jutsus) / len(jutsus), 1) if jutsus else 0
            compared.append({
                "cla": c,
                "jutsus": jutsus,
                "latentes": latentes,
                "ranks": ranks_set,
                "avg_chakra": avg_chakra
            })

    if not compared:
        print(f"\n❌ Nenhum dos clãs fornecidos foi encontrado: {cla_names}")
        return

    print(f"\n⚖️ PAINEL COMPARATIVO DE CLÃS: {' vs '.join(c['cla']['nome'] for c in compared)}")
    print("=" * 95)
    for item in compared:
        c = item['cla']
        print(f"\n🔹 CLÃ {c['nome'].upper()} (p.{c['pagina']})")
        print(f"   • Atributos:    {c['aumento_atributos_raw']}")
        print(f"   • Deslocamento: {c['deslocamento']}")
        print(f"   • Perícias:     {', '.join(c['pericias']) or 'Nenhuma fixa'}")
        print(f"   • Recursos ({len(c['recursos'])}):")
        for rec in c['recursos'][:3]:
            print(f"       - {rec['nome']} (Nível {rec.get('nivel', 1)})")
        if len(c['recursos']) > 3:
            print(f"       - ... e mais {len(c['recursos']) - 3} recursos de linhagem")
        print(f"   • Jutsus ({len(item['jutsus'])}): Ranks [{', '.join(item['ranks']) or '-'}] | Custo Médio: {item['avg_chakra']} Chakra")
        print(f"   • Latentes ({len(item['latentes'])} opções de compra)")
    print("=" * 95)


def display_latent_info(cla_nome: str, max_pontos: Optional[int], db_path: str):
    all_traits = query_latent_bloodlines(max_pontos=max_pontos, db_path=db_path)
    clean_target = strip_accents(cla_nome).lower() if cla_nome else ""
    traits = [t for t in all_traits if not clean_target or clean_target in strip_accents(t['cla']).lower()]
    print(f"\n🩸 Linhagens Latentes encontradas ({len(traits)}):")
    print("=" * 80)
    for t in traits:
        req = f" [Req: {t['pre_requisito']}]" if t.get('pre_requisito') else ""
        print(f"[{t['cla']}] {t['nome_habilidade']} | Custo: {t['custo_pontos']} pts{req}")
        print(f"  {t['descricao']}")
        print("-" * 80)


def display_classes_list(db_path: str):
    classes = list_classes(db_path=db_path)
    print(f"\n🥋 CLASSES DE NARUTO 5E ({len(classes)} classes):")
    print("=" * 80)
    print(f"{'Nome':28s} | {'Nome (EN)':22s} | {'Grau':6s} | {'Vida':5s} | {'Chakra':6s} | {'Pág'}")
    print("-" * 80)
    for c in classes:
        print(f"{c['nome']:28s} | {c['nome_en'] or '-':22s} | {c['tipo_conjurador']:6s} | {c['dado_vida']:5s} | {c['dado_chakra']:6s} | p.{c['pagina_inicio']}")
    print("=" * 80)


def display_class_info(classe_nome: str, db_path: str):
    c = get_class(classe_nome, db_path=db_path)
    if not c:
        print(f"\n❌ Classe '{classe_nome}' não encontrada.")
        return

    print(f"\n🥋 FICHA DA CLASSE: {c['nome'].upper()} ({c['nome_en']})")
    print("=" * 90)
    print(f"📖 Página no Livro: {c['pagina_inicio']} | Tipo Conjurador: {c['tipo_conjurador']}")
    print(f"❤️ Dado de Vida: {c['dado_vida']} (1º Nível: {c['hp_primeiro_nivel']})")
    print(f"🌀 Dado de Chakra: {c['dado_chakra']} (1º Nível: {c['chakra_primeiro_nivel']})")
    print(f"🛡️ Testes de Resistência: {', '.join(c['testes_resistencia'])}")
    print(f"🥋 Armaduras: {c['proficiencias_armaduras'] or 'Nenhuma'}")
    print(f"🗡️ Armas: {c['proficiencias_armas'] or 'Nenhuma'}")
    print(f"🔧 Ferramentas: {c['proficiencias_ferramentas'] or 'Nenhuma'}")
    print(f"🎯 Perícias: {c['pericias_escolha'] or 'Nenhuma'}")
    if c['equipamento_inicial']:
        print(f"🎒 Equipamento Inicial: {c['equipamento_inicial']}")

    print("\n📊 TABELA DE PROGRESSÃO (Níveis 1 a 20):")
    print("-" * 90)
    print(f"{'Nv':2s} | {'PB':3s} | {'Jutsus':6s} | {'Rank Max':8s} | {'Características & Recursos'}")
    print("-" * 90)
    for row in c['tabela_progressao']:
        feats_str = ", ".join(row['caracteristicas']) if row['caracteristicas'] else "-"
        extras_str = ""
        if row.get('colunas_extras'):
            extras_list = [f"{k}={v}" for k, v in row['colunas_extras'].items() if v is not None]
            if extras_list:
                extras_str = f" [{', '.join(extras_list)}]"
        jut_str = str(row['jutsu_conhecidos']) if row['jutsu_conhecidos'] is not None else "-"
        rank_str = row['rank_max_jutsu'] or "-"
        print(f"{row['nivel']:2d} | {row['bonus_proficiencia']:3s} | {jut_str:6s} | {rank_str:8s} | {feats_str}{extras_str}")
    print("-" * 90)

    # Arquétipos disponíveis
    archs = query_archetypes(classe_nome=c['nome'], db_path=db_path)
    if archs:
        tipo_arq = archs[0]['tipo_arquetipo']
        lvl_arq = archs[0]['nivel_obtencao']
        print(f"\n🔮 Arquétipos / Subclasses ({len(archs)} opções - {tipo_arq}, Nível {lvl_arq}):")
        for a in archs:
            print(f"  • {a['nome']:25s} (p.{a['pagina']}) - {len(a['caracteristicas'])} características concedidas")

    # Opções Modulares
    if c['recursos_customizacao']:
        cats = {}
        for opt in c['recursos_customizacao']:
            cat = opt.get('categoria', 'Opções')
            cats[cat] = cats.get(cat, 0) + 1
        print("\n⚙️ Opções Modulares de Customização:")
        for cat_name, count in cats.items():
            print(f"  • {cat_name}: {count} opções disponíveis")

    print("=" * 90)


def display_archetypes(classe_nome: Optional[str], nome: Optional[str], db_path: str):
    archs = query_archetypes(classe_nome=classe_nome, nome=nome, db_path=db_path)
    print(f"\n🔮 ARQUÉTIPOS ENCONTRADOS ({len(archs)}):")
    print("=" * 80)
    for a in archs:
        print(f"\n🔮 {a['nome'].upper()} [{a['classe_nome']}] - {a['tipo_arquetipo']} (Nível {a['nivel_obtencao']}, p.{a['pagina']})")
        print(f"  {a['descricao_mecanica']}")
        if a['caracteristicas']:
            print(f"  Recursos Concedidos ({len(a['caracteristicas'])}):")
            for f in a['caracteristicas']:
                usos_str = f" [Usos: {f['usos']}]" if f.get('usos') else ""
                print(f"    • {f['nome']} (Nível {f.get('nivel', a['nivel_obtencao'])}){usos_str}")
                print(f"      {f['descricao']}")
        print("-" * 80)


def display_class_talents(classe: Optional[str], tipo: Optional[str], nome: Optional[str], db_path: str):
    talents = query_class_talents(classe=classe, tipo=tipo, nome=nome, db_path=db_path)
    print(f"\n✨ TALENTOS DE CLASSE ({len(talents)} encontrados):")
    print("=" * 80)
    for t in talents:
        req = f" | Req: {t['prerequisitos']}" if t['prerequisitos'] else ""
        arq = f" [Arquétipo: {t['arquetipo_requerido']}]" if t['arquetipo_requerido'] else ""
        print(f"\n✨ {t['nome']} (Tipo: {t['tipo']}, Classe: {t['classe']}, p.{t['pagina']}){arq}{req}")
        print(f"   {t['descricao_mecanica']}")
        print("-" * 80)


def display_weapons(
    nome: Optional[str] = None,
    categoria: Optional[str] = None,
    grupo: Optional[str] = None,
    propriedade: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
):
    weapons = query_weapons(nome=nome, categoria=categoria, grupo=grupo, propriedade=propriedade, db_path=db_path)
    print(f"\n🗡️ ARMAS DE NARUTO 5E ({len(weapons)} encontradas):")
    print("=" * 95)
    print(f"{'Nome':22s} | {'Categoria':24s} | {'Dano':12s} | {'Custo':10s} | {'Propriedades'}")
    print("-" * 95)
    for w in weapons:
        print(f"{w['nome']:22s} | {w['categoria']:24s} | {w['dano']:12s} | {w['custo_ryo']:10s} | {w['propriedades']}")
    print("=" * 95)


def display_armors(
    nome: Optional[str] = None,
    tipo: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
):
    armors = query_armors(nome=nome, tipo=tipo, db_path=db_path)
    print(f"\n🛡️ ARMADURAS E ESCUDOS DE NARUTO 5E ({len(armors)} encontrados):")
    print("=" * 85)
    print(f"{'Nome':24s} | {'Tipo':18s} | {'Bônus CA':10s} | {'Des Máx':10s} | {'Custo':10s} | {'Efeito'}")
    print("-" * 85)
    for a in armors:
        efeito = a['efeito_especial'] or '-'
        print(f"{a['nome']:24s} | {a['tipo']:18s} | {a['bonus_ca']:10s} | {a['bonus_des_max']:10s} | {a['custo_ryo']:10s} | {efeito}")
    print("=" * 85)


def display_fuinjutsu_seals(
    nome: Optional[str] = None,
    rank: Optional[str] = None,
    tipo_item: Optional[str] = None,
    grau: Optional[str] = None,
    max_custo: Optional[int] = None,
    detalhe: bool = False,
    db_path: str = DEFAULT_DB_PATH
):
    seals = query_fuinjutsu_seals(nome=nome, rank=rank, tipo_item=tipo_item, grau=grau, max_custo=max_custo, db_path=db_path)
    print(f"\n📜 SELOS DE FUINJUTSU ({len(seals)} encontrados):")
    print("=" * 90)
    for i, s in enumerate(seals, 1):
        grau_str = f" ({s['grau_selo']})" if s['grau_selo'] else ""
        print(f"{i:3d}. [{s['rank']}] {s['nome']}{grau_str} | Item: {s['tipo_item']} | Custo: {s['custo_ryo']} Ryo (p.{s['pagina']})")
        if detalhe:
            print(f"     Efeito Mecânico:\n     {s['efeito_mecanico']}")
            print("-" * 90)
    if not detalhe:
        print("\n💡 Dica: Use --detalhe para ver a regra mecânica completa de cada selo.")
    print("=" * 90)


def display_conditions(
    nome: Optional[str] = None,
    categoria: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
):
    conditions = query_conditions(nome=nome, categoria=categoria, db_path=db_path)
    print(f"\n⚠️ CONDIÇÕES DE STATUS ({len(conditions)} encontradas):")
    print("=" * 85)
    for c in conditions:
        print(f"\n📌 [{c['categoria'].upper()}] {c['nome']} (p.{c['pagina']})")
        print(f"   {c['descricao_mecanica']}")
    print("=" * 85)


def display_combat_rules(
    chave: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
):
    if chave and chave != "ALL":
        rule = get_combat_rule(chave, db_path=db_path)
        if not rule:
            print(f"\n❌ Nenhuma regra de combate encontrada com o identificador '{chave}'.")
            return
        rules = [rule]
    else:
        rules = list_combat_rules(db_path=db_path)

    print(f"\n⚔️ REGRAS DE COMBATE NUCLEARES ({len(rules)} regras):")
    print("=" * 85)
    for r in rules:
        print(f"\n🔹 {r['titulo'].upper()} [Chave: {r['chave']}] (Página {r['pagina']})")
        print(f"   {r['descricao_mecanica']}")
        if r.get('dados_estruturados'):
            print(f"   Dados Estruturados:")
            for k, v in r['dados_estruturados'].items():
                print(f"     • {k}: {v}")
    print("=" * 85)


def display_error_reports(status: Optional[str] = None, db_path: str = DEFAULT_DB_PATH):
    """Exibe no terminal a lista de relatórios de erros registrados no banco."""
    ensure_tables(db_path)
    data = list_error_reports(status=status, db_path=db_path)
    total = data["total"]
    items = data["items"]
    print(f"\n📝 RELATÓRIOS DE ERROS REGISTRADOS ({total} encontrados):")
    print("=" * 95)
    if not items:
        print("  Nenhum relatório de erro encontrado com os filtros informados.")
        print("=" * 95)
        return

    for r in items:
        status_icon = "⏳" if r['status'] == 'pendente' else ("🔍" if r['status'] == 'em_analise' else "✅")
        item_id_str = f" [ID: {r['item_id']}]" if r['item_id'] else ""
        print(f"\n{status_icon} Relatório #{r['id']} | Status: {r['status'].upper()} | Usuário: {r['usuario']} ({r['criado_em']})")
        print(f"   Origem: [{r['tabela_origem'].upper()}]{item_id_str} {r['item_nome']}")
        if r['campo_afetado']:
            print(f"   Campo Afetado: {r['campo_afetado']}")
        print(f"   ⚠️ Descrição: {r['descricao_erro']}")
        if r['sugestao_correcao']:
            print(f"   💡 Correção sugerida: {r['sugestao_correcao']}")
        print("-" * 95)
    print("=" * 95)


def report_error_interactive(args, db_path: str = DEFAULT_DB_PATH):
    """Executa o fluxo para reportar erro em texto quebrado (interativo ou via flags)."""
    ensure_tables(db_path)
    print("\n" + "=" * 70)
    print("⚠️  REPORTE DE ERRO DE EXTRAÇÃO / TEXTO QUEBRADO (NARUTO 5E)")
    print("=" * 70)

    usuario = args.usuario
    if not usuario:
        usuario = input("👤 Digite seu nome de Shinobi/Usuário: ").strip()
    while not usuario:
        usuario = input("❌ O nome de usuário é obrigatório. Digite seu nome: ").strip()

    get_or_create_user(usuario, db_path=db_path)

    tabela = args.tabela
    if not tabela:
        tabela = input("📂 Tabela afetada [jutsus, clans, classes, weapons, armors, selos, regras] (padrão: jutsus): ").strip()
    if not tabela:
        tabela = "jutsus"

    item_nome = args.item
    if not item_nome:
        item_nome = input("🏷️  Nome ou título do item com texto quebrado (ex: Rasengan): ").strip()
    while not item_nome:
        item_nome = input("❌ Nome do item é obrigatório. Digite o nome: ").strip()

    campo = args.campo
    if campo is None:
        campo = input("📑 Campo afetado (ex: efeito_mecanico, dano, nome) [Opcional]: ").strip()

    erro = args.erro
    if not erro:
        erro = input("✍️  O que está quebrado? Descreva o erro detalhadamente: ").strip()
    while not erro:
        erro = input("❌ A descrição do erro é obrigatória: ").strip()

    correcao = args.correcao
    if correcao is None:
        correcao = input("💡 Sugestão de texto correto [Opcional]: ").strip()

    report = create_error_report(
        usuario=usuario,
        tabela_origem=tabela,
        item_nome=item_nome,
        campo_afetado=campo or None,
        descricao_erro=erro,
        sugestao_correcao=correcao or None,
        db_path=db_path
    )
    print(f"\n✅ Relatório de erro #{report['id']} gravado com sucesso no banco de dados!")
    print(f"   Usuário: {report['usuario']} | Origem: [{report['tabela_origem']}] {report['item_nome']}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Consulta rápida no banco de dados Naruto 5e (Jutsus, Clãs, Classes, Equipamentos e Regras)")

    # Autenticação e Reporte de Erros
    parser.add_argument("--reportar", action="store_true", help="Reportar texto quebrado ou erro em linhas de querys")
    parser.add_argument("--ver-erros", action="store_true", help="Listar relatórios de erros salvos no banco de dados")
    parser.add_argument("--marcar-corrigido", type=int, help="Marcar relatório de erro como corrigido pelo seu ID")
    parser.add_argument("--usuario", type=str, help="Nome do usuário/Shinobi para login e reporte")
    parser.add_argument("--tabela", type=str, help="Tabela do registro com erro (jutsus, clans, classes, weapons, etc.)")
    parser.add_argument("--item", type=str, help="Nome do jutsu/item com erro")
    parser.add_argument("--campo", type=str, help="Campo específico que está com texto quebrado")
    parser.add_argument("--erro", type=str, help="Descrição detalhada do erro encontrado")
    parser.add_argument("--correcao", type=str, help="Sugestão de correção para o texto")

    # Filtros de Jutsu
    parser.add_argument("--nome", type=str, help="Filtrar por nome do jutsu")
    parser.add_argument("--rank", type=str, help="Filtrar por rank (ex: Rank-D, Rank-C, Rank-B, Rank-A, Rank-S)")
    parser.add_argument("--estilo", type=str, help="Filtrar por estilo/natureza (ex: Fogo, Água, Terra, Vento, Relâmpago, Médico)")
    parser.add_argument("--cla", type=str, help="Filtrar por clã associado")
    parser.add_argument("--max-chakra", type=int, help="Filtrar por custo máximo de Chakra")
    parser.add_argument("--save", type=str, help="Filtrar por salvaguarda exigida (ex: Destreza, Constituição, Sabedoria)")
    parser.add_argument("--condicao", type=str, help="Filtrar por condição aplicada (ex: Envenenado, Contido, Cego)")
    parser.add_argument("--detalhe", action="store_true", help="Exibir descrição mecânica completa de cada registro")

    # Filtros de Clã
    parser.add_argument("--info-cla", type=str, help="Consultar ficha mecânica completa de um Clã específico")
    parser.add_argument("--comparar-clas", type=str, help="Comparar dois ou mais clãs lado a lado (ex: --comparar-clas 'Uchiha,Hyūga,Senju')")
    parser.add_argument("--cla-atributo", type=str, help="Listar clãs que concedem bônus em determinado atributo (ex: Inteligência, Destreza)")
    parser.add_argument("--latente", type=str, help="Listar traços de linhagem latente de um Clã")
    parser.add_argument("--max-pontos-latente", type=int, help="Custo máximo de pontos de linhagem")

    # Filtros de Classe e Arquétipo
    parser.add_argument("--classes", action="store_true", help="Listar todas as 11 classes de Naruto 5e")
    parser.add_argument("--info-classe", type=str, help="Consultar ficha mecânica e tabela de progressão de uma Classe")
    parser.add_argument("--arquetipos", nargs="?", const="ALL", help="Listar arquétipos (opcionalmente de uma classe específica)")
    parser.add_argument("--nome-arquetipo", type=str, help="Filtrar arquétipo por nome")
    parser.add_argument("--talentos-classe", nargs="?", const="ALL", help="Listar talentos de classe (opcionalmente filtrados por classe)")
    parser.add_argument("--tipo-talento", type=str, help="Filtrar talento por tipo (ex: Arquétipo, Conjuntor, Marcial)")

    # Filtros de Equipamento e Regras Gerais
    parser.add_argument("--armas", nargs="?", const="ALL", help="Listar armas (opcionalmente filtrar por nome)")
    parser.add_argument("--categoria-arma", type=str, help="Filtrar armas por categoria (ex: Simples, Marcial, Exótica)")
    parser.add_argument("--grupo-arma", type=str, help="Filtrar armas por grupo (ex: Lâmina, Arremesso, Munição)")
    parser.add_argument("--prop-arma", type=str, help="Filtrar armas por propriedade (ex: Finesse, Leve, Pesada, Versátil)")

    parser.add_argument("--armaduras", nargs="?", const="ALL", help="Listar armaduras e escudos (opcionalmente filtrar por nome)")
    parser.add_argument("--tipo-armadura", type=str, help="Filtrar armaduras por tipo (ex: Leve, Média, Pesada, Escudos)")

    parser.add_argument("--selos", nargs="?", const="ALL", help="Listar selos de Fuinjutsu (opcionalmente filtrar por nome)")
    parser.add_argument("--rank-selo", type=str, help="Filtrar selos por rank (ex: Rank-D, Rank-C, Rank-B, Rank-A, Rank-S)")
    parser.add_argument("--tipo-selo", type=str, help="Filtrar selos por tipo de item (Arma ou Armadura)")
    parser.add_argument("--grau-selo", type=str, help="Filtrar selos por grau (Menor, Padrão, Maior, Mestre, Supremo)")
    parser.add_argument("--max-ryo", type=int, help="Filtrar selos por custo máximo em Ryo")

    parser.add_argument("--condicoes", nargs="?", const="ALL", help="Listar condições de status (opcionalmente filtrar por nome)")
    parser.add_argument("--categoria-condicao", type=str, help="Filtrar condições por categoria (Elemental, Físico, Mental, Sensorial, Geral)")

    parser.add_argument("--regras-combate", nargs="?", const="ALL", help="Consultar regras de combate centrais (superioridade_elemental, confronto_clash, leia_inimigo)")

    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Caminho do banco SQLite")

    args = parser.parse_args()

    # 0. Gestão de Relatórios de Erros
    if args.ver_erros:
        display_error_reports(db_path=args.db)
        return

    if args.marcar_corrigido:
        res = update_error_report_status(args.marcar_corrigido, status="corrigido", db_path=args.db)
        if res:
            print(f"\n✅ Relatório #{args.marcar_corrigido} marcado como 'corrigido' com sucesso no banco de dados!")
        else:
            print(f"\n❌ Relatório #{args.marcar_corrigido} não encontrado no banco de dados.")
        return

    if args.reportar:
        report_error_interactive(args, db_path=args.db)
        return

    # 1. Consulta de Classes
    if args.classes:
        display_classes_list(args.db)
        return

    if args.info_classe:
        display_class_info(args.info_classe, args.db)
        return

    # 2. Consulta de Arquétipos
    if args.arquetipos is not None:
        target_class = None if args.arquetipos == "ALL" else args.arquetipos
        display_archetypes(classe_nome=target_class, nome=args.nome_arquetipo, db_path=args.db)
        return

    # 3. Consulta de Talentos de Classe
    if args.talentos_classe is not None or args.tipo_talento:
        target_class = None if args.talentos_classe in (None, "ALL") else args.talentos_classe
        display_class_talents(classe=target_class, tipo=args.tipo_talento, nome=None, db_path=args.db)
        return

    # 4. Consulta de Ficha de Clã
    if args.info_cla:
        display_clan_info(args.info_cla, args.db)
        return

    if args.comparar_clas:
        display_clan_comparison(args.comparar_clas, args.db)
        return

    # 5. Consulta de Linhagens Latentes
    if args.latente:
        display_latent_info(args.latente, args.max_pontos_latente, args.db)
        return

    # 6. Consulta de Clãs por Atributo
    if args.cla_atributo:
        clans = query_clans(atributo=args.cla_atributo, db_path=args.db)
        print(f"\n🧬 Clãs que concedem bônus em '{args.cla_atributo}' ({len(clans)} encontrados):")
        print("=" * 80)
        for c in clans:
            print(f"  • {c['nome']:20s} | Bônus: {c['aumento_atributos_raw']} | Vel: {c['deslocamento']}")
        print("=" * 80)
        return

    # 7. Consulta de Armas
    if args.armas is not None or args.categoria_arma or args.grupo_arma or args.prop_arma:
        target_name = None if args.armas in (None, "ALL") else args.armas
        display_weapons(nome=target_name, categoria=args.categoria_arma, grupo=args.grupo_arma, propriedade=args.prop_arma, db_path=args.db)
        return

    # 8. Consulta de Armaduras
    if args.armaduras is not None or args.tipo_armadura:
        target_name = None if args.armaduras in (None, "ALL") else args.armaduras
        display_armors(nome=target_name, tipo=args.tipo_armadura, db_path=args.db)
        return

    # 9. Consulta de Selos de Fuinjutsu
    if args.selos is not None or args.rank_selo or args.tipo_selo or args.grau_selo or args.max_ryo:
        target_name = None if args.selos in (None, "ALL") else args.selos
        display_fuinjutsu_seals(
            nome=target_name,
            rank=args.rank_selo,
            tipo_item=args.tipo_selo,
            grau=args.grau_selo,
            max_custo=args.max_ryo,
            detalhe=args.detalhe,
            db_path=args.db
        )
        return

    # 10. Consulta de Condições de Status
    if args.condicoes is not None or args.categoria_condicao:
        target_name = None if args.condicoes in (None, "ALL") else args.condicoes
        display_conditions(nome=target_name, categoria=args.categoria_condicao, db_path=args.db)
        return

    # 11. Consulta de Regras de Combate
    if args.regras_combate is not None:
        target_chave = None if args.regras_combate == "ALL" else args.regras_combate
        display_combat_rules(chave=target_chave, db_path=args.db)
        return

    # 12. Consulta Padrão de Jutsus
    results = query_jutsus(
        nome=args.nome,
        rank=args.rank,
        natureza=args.estilo,
        cla=args.cla,
        max_chakra=args.max_chakra,
        salvaguarda=args.save,
        condicao=args.condicao,
        db_path=args.db
    )

    print(f"\n🍃 Encontrados {len(results)} jutsus correspondentes aos filtros:")
    print("=" * 80)

    for i, j in enumerate(results, 1):
        cla_tag = f" [Clã: {j['cla']}]" if j['cla'] else ""
        dano_tag = f" | Dano: {j['dano_formula']} {j['dano_tipo']}" if j['dano_formula'] else ""
        save_tag = f" | Save: {j['salvaguarda']}" if j['salvaguarda'] else ""
        cond_tag = f" | Condição: {', '.join(j['condicoes'])}" if j['condicoes'] else ""

        print(f"{i:3d}. [ID: {j['id']}] [{j['rank']}] {j['nome']}{cla_tag}")
        print(f"     Custo: {j['custo_chakra']} Chakra | Ação: {j['tempo_conjuracao']} | Alcance: {j['alcance']}{dano_tag}{save_tag}{cond_tag}")
        if j['vantagem_desvantagem']:
            print(f"     ⚡ {j['vantagem_desvantagem']}")

        if args.detalhe:
            print(f"\n     Regra Mecânica:\n     {j['efeito_mecanico']}")
            if j['em_niveis_mais_altos']:
                print(f"     Escalonamento (Upcasting): {j['em_niveis_mais_altos']}")
            print("-" * 80)

    print("=" * 80)
    print("💡 Encontrou texto quebrado em alguma linha? Use 'python query.py --reportar' ou use o painel web (http://localhost:8000)!")


if __name__ == "__main__":
    main()
