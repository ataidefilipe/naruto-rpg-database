import sqlite3
import json
import os
from typing import List, Optional, Dict, Any
from src.models.jutsu import Jutsu
from src.models.clan import Clan
from src.models.classe import ClassEntity, Archetype, ClassTalent
from src.models.rules import Weapon, Armor, FuinjutsuSeal, ConditionRule, CombatRule

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(PROJECT_ROOT, "data", "naruto5e.db"))



def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Inicializa as tabelas do banco de dados SQLite."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Tabela unificada de Jutsus
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jutsus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        classificacao TEXT NOT NULL,
        natureza_estilo TEXT,
        rank TEXT NOT NULL,
        tempo_conjuracao TEXT NOT NULL,
        alcance TEXT NOT NULL,
        duracao TEXT NOT NULL,
        componentes TEXT NOT NULL,       -- JSON Array
        custo_chakra INTEGER NOT NULL,
        palavras_chave TEXT NOT NULL,    -- JSON Array
        cla TEXT,
        exclusivo_cla BOOLEAN NOT NULL DEFAULT 0,
        efeito_mecanico TEXT NOT NULL,
        dano_formula TEXT,
        dano_tipo TEXT,
        salvaguarda TEXT,
        condicoes TEXT NOT NULL,         -- JSON Array
        vantagem_desvantagem TEXT,
        em_niveis_mais_altos TEXT,
        origem_livro TEXT NOT NULL,
        pagina INTEGER
    );
    """)

    # 2. Tabela de Clãs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        aumento_atributos_raw TEXT NOT NULL,
        aumento_atributos TEXT NOT NULL, -- JSON Dict
        deslocamento TEXT NOT NULL,
        pericias TEXT NOT NULL,          -- JSON Array
        idiomas TEXT NOT NULL,           -- JSON Array
        recursos TEXT NOT NULL,          -- JSON Array de ClanFeature
        pagina INTEGER NOT NULL
    );
    """)

    # 3. Tabela de Linhagens Sanguíneas Latentes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS latent_bloodlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cla TEXT NOT NULL,
        nome_habilidade TEXT NOT NULL,
        custo_pontos INTEGER NOT NULL,
        pre_requisito TEXT,
        descricao TEXT NOT NULL,
        pagina INTEGER NOT NULL
    );
    """)

    # 4. Tabela de Classes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        nome_en TEXT,
        tipo_conjurador TEXT NOT NULL,
        dado_vida TEXT NOT NULL,
        dado_chakra TEXT NOT NULL,
        hp_primeiro_nivel TEXT NOT NULL,
        chakra_primeiro_nivel TEXT NOT NULL,
        proficiencias_armaduras TEXT,
        proficiencias_armas TEXT,
        proficiencias_ferramentas TEXT,
        testes_resistencia TEXT NOT NULL,       -- JSON Array
        pericias_escolha TEXT,
        equipamento_inicial TEXT,
        tabela_progressao TEXT NOT NULL,        -- JSON Array de 20 linhas
        caracteristicas_classe TEXT NOT NULL,   -- JSON Array de FeatureDetail
        recursos_customizacao TEXT NOT NULL,    -- JSON Array
        pagina_inicio INTEGER NOT NULL
    );
    """)

    # 5. Tabela de Arquétipos (Subclasses)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS archetypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        classe_nome TEXT NOT NULL,
        nome TEXT NOT NULL,
        tipo_arquetipo TEXT NOT NULL,
        nivel_obtencao INTEGER NOT NULL,
        descricao_mecanica TEXT NOT NULL,
        caracteristicas TEXT NOT NULL,          -- JSON Array de FeatureDetail
        pagina INTEGER
    );
    """)

    # 6. Tabela de Talentos de Classe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS class_talents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        classe TEXT NOT NULL,
        arquetipo_requerido TEXT,
        prerequisitos TEXT,
        descricao_mecanica TEXT NOT NULL,
        pagina INTEGER
    );
    """)

    # 7. Tabela de Armas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weapons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        custo_ryo TEXT NOT NULL,
        dano TEXT NOT NULL,
        propriedades TEXT NOT NULL,
        grupo_arma TEXT NOT NULL,
        volume TEXT NOT NULL DEFAULT '1',
        pagina INTEGER
    );
    """)

    # 8. Tabela de Armaduras e Escudos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS armors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        custo_ryo TEXT NOT NULL,
        bonus_ca TEXT NOT NULL,
        bonus_des_max TEXT NOT NULL DEFAULT '-',
        volume TEXT NOT NULL DEFAULT '1',
        efeito_especial TEXT,
        pagina INTEGER
    );
    """)

    # 9. Tabela de Selos de Fuinjutsu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fuinjutsu_seals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo_item TEXT NOT NULL,
        rank TEXT NOT NULL,
        grau_selo TEXT,
        custo_ryo INTEGER NOT NULL,
        efeito_mecanico TEXT NOT NULL,
        pagina INTEGER
    );
    """)

    # 10. Tabela de Condições
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        categoria TEXT NOT NULL,
        descricao_mecanica TEXT NOT NULL,
        pagina INTEGER
    );
    """)

    # 11. Tabela de Regras de Combate
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combat_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chave TEXT NOT NULL UNIQUE,
        titulo TEXT NOT NULL,
        descricao_mecanica TEXT NOT NULL,
        dados_estruturados TEXT NOT NULL, -- JSON Dict
        pagina INTEGER
    );
    """)

    # Índices de performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jutsus_rank ON jutsus(rank);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jutsus_natureza ON jutsus(natureza_estilo);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jutsus_cla ON jutsus(cla);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jutsus_custo ON jutsus(custo_chakra);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jutsus_classif ON jutsus(classificacao);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clans_nome ON clans(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_latent_cla ON latent_bloodlines(cla);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classes_nome ON classes(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_archetypes_classe ON archetypes(classe_nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_archetypes_nome ON archetypes(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_talents_classe ON class_talents(classe);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_talents_tipo ON class_talents(tipo);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weapons_nome ON weapons(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_weapons_categoria ON weapons(categoria);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_armors_tipo ON armors(tipo);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_armors_nome ON armors(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuinjutsu_rank ON fuinjutsu_seals(rank);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuinjutsu_tipo ON fuinjutsu_seals(tipo_item);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fuinjutsu_nome ON fuinjutsu_seals(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conditions_nome ON conditions(nome);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conditions_categoria ON conditions(categoria);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_combat_rules_chave ON combat_rules(chave);")

    conn.commit()
    conn.close()


def insert_jutsus(jutsus: List[Jutsu], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere uma lista de jutsus no banco. Se clear_first=True, limpa a tabela antes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM jutsus;")

    inserted = 0
    for j in jutsus:
        cursor.execute("""
        INSERT INTO jutsus (
            nome, classificacao, natureza_estilo, rank, tempo_conjuracao,
            alcance, duracao, componentes, custo_chakra, palavras_chave,
            cla, exclusivo_cla, efeito_mecanico, dano_formula, dano_tipo,
            salvaguarda, condicoes, vantagem_desvantagem, em_niveis_mais_altos,
            origem_livro, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            j.nome,
            j.classificacao,
            j.natureza_estilo,
            j.rank,
            j.tempo_conjuracao,
            j.alcance,
            j.duracao,
            json.dumps(j.componentes, ensure_ascii=False),
            j.custo_chakra,
            json.dumps(j.palavras_chave, ensure_ascii=False),
            j.cla,
            1 if j.exclusivo_cla else 0,
            j.efeito_mecanico,
            j.dano_formula,
            j.dano_tipo,
            j.salvaguarda,
            json.dumps(j.condicoes, ensure_ascii=False),
            j.vantagem_desvantagem,
            j.em_niveis_mais_altos,
            j.origem_livro,
            j.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_clans(clans: List[Clan], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere ou atualiza os clãs no banco."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM clans;")

    inserted = 0
    for c in clans:
        recursos_dicts = [f.model_dump() for f in c.recursos]
        cursor.execute("""
        INSERT OR REPLACE INTO clans (
            nome, aumento_atributos_raw, aumento_atributos, deslocamento,
            pericias, idiomas, recursos, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c.nome,
            c.aumento_atributos_raw,
            json.dumps(c.aumento_atributos, ensure_ascii=False),
            c.deslocamento,
            json.dumps(c.pericias, ensure_ascii=False),
            json.dumps(c.idiomas, ensure_ascii=False),
            json.dumps(recursos_dicts, ensure_ascii=False),
            c.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_latent_bloodlines(traits: List[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere habilidades de linhagens latentes no banco."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM latent_bloodlines;")

    inserted = 0
    for t in traits:
        cursor.execute("""
        INSERT INTO latent_bloodlines (
            cla, nome_habilidade, custo_pontos, pre_requisito, descricao, pagina
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            t["cla"],
            t["nome_habilidade"],
            t["custo_pontos"],
            t.get("pre_requisito"),
            t["descricao"],
            t["pagina"]
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def query_jutsus(
    nome: Optional[str] = None,
    rank: Optional[str] = None,
    natureza: Optional[str] = None,
    cla: Optional[str] = None,
    max_chakra: Optional[int] = None,
    salvaguarda: Optional[str] = None,
    condicao: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta jutsus com filtros combinados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM jutsus WHERE 1=1"
    params = []

    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if rank:
        query += " AND rank LIKE ?"
        params.append(f"%{rank}%")
    if natureza:
        query += " AND natureza_estilo LIKE ?"
        params.append(f"%{natureza}%")
    if cla:
        query += " AND cla LIKE ?"
        params.append(f"%{cla}%")
    if max_chakra is not None:
        query += " AND custo_chakra <= ?"
        params.append(max_chakra)
    if salvaguarda:
        query += " AND salvaguarda = ?"
        params.append(salvaguarda)
    if condicao:
        query += " AND condicoes LIKE ?"
        params.append(f"%{condicao}%")

    query += " ORDER BY rank, custo_chakra, nome"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["componentes"] = json.loads(d["componentes"])
        d["palavras_chave"] = json.loads(d["palavras_chave"])
        d["condicoes"] = json.loads(d["condicoes"])
        d["exclusivo_cla"] = bool(d["exclusivo_cla"])
        results.append(d)

    conn.close()
    return results


def query_clans(
    nome: Optional[str] = None,
    atributo: Optional[str] = None,
    pericia: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta clãs cadastrados com filtros."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM clans WHERE 1=1"
    params = []

    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if atributo:
        query += " AND aumento_atributos LIKE ?"
        params.append(f"%{atributo}%")
    if pericia:
        query += " AND pericias LIKE ?"
        params.append(f"%{pericia}%")

    query += " ORDER BY nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["aumento_atributos"] = json.loads(d["aumento_atributos"])
        d["pericias"] = json.loads(d["pericias"])
        d["idiomas"] = json.loads(d["idiomas"])
        d["recursos"] = json.loads(d["recursos"])
        results.append(d)

    conn.close()
    return results


def query_latent_bloodlines(
    cla: Optional[str] = None,
    max_pontos: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta habilidades de linhagens latentes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM latent_bloodlines WHERE 1=1"
    params = []

    if cla:
        query += " AND cla LIKE ?"
        params.append(f"%{cla}%")
    if max_pontos is not None:
        query += " AND custo_pontos <= ?"
        params.append(max_pontos)

    query += " ORDER BY cla, custo_pontos, nome_habilidade"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def insert_classes(classes: List[ClassEntity], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere as classes no banco. Se clear_first=True, limpa a tabela antes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM classes;")

    inserted = 0
    for c in classes:
        cursor.execute("""
        INSERT OR REPLACE INTO classes (
            nome, nome_en, tipo_conjurador, dado_vida, dado_chakra,
            hp_primeiro_nivel, chakra_primeiro_nivel,
            proficiencias_armaduras, proficiencias_armas, proficiencias_ferramentas,
            testes_resistencia, pericias_escolha, equipamento_inicial,
            tabela_progressao, caracteristicas_classe, recursos_customizacao,
            pagina_inicio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c.nome,
            c.nome_en,
            c.tipo_conjurador,
            c.dado_vida,
            c.dado_chakra,
            c.hp_primeiro_nivel,
            c.chakra_primeiro_nivel,
            c.proficiencias_armaduras,
            c.proficiencias_armas,
            c.proficiencias_ferramentas,
            json.dumps(c.testes_resistencia, ensure_ascii=False),
            c.pericias_escolha,
            c.equipamento_inicial,
            json.dumps([r.model_dump() for r in c.tabela_progressao], ensure_ascii=False),
            json.dumps([f.model_dump() for f in c.caracteristicas_classe], ensure_ascii=False),
            json.dumps(c.recursos_customizacao, ensure_ascii=False),
            c.pagina_inicio
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_archetypes(archetypes: List[Archetype], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere os arquétipos no banco. Se clear_first=True, limpa a tabela antes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM archetypes;")

    inserted = 0
    for a in archetypes:
        cursor.execute("""
        INSERT INTO archetypes (
            classe_nome, nome, tipo_arquetipo, nivel_obtencao,
            descricao_mecanica, caracteristicas, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            a.classe_nome,
            a.nome,
            a.tipo_arquetipo,
            a.nivel_obtencao,
            a.descricao_mecanica,
            json.dumps([f.model_dump() for f in a.caracteristicas], ensure_ascii=False),
            a.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_class_talents(talents: List[ClassTalent], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere talentos de classe no banco. Se clear_first=True, limpa a tabela antes."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM class_talents;")

    inserted = 0
    for t in talents:
        cursor.execute("""
        INSERT INTO class_talents (
            nome, tipo, classe, arquetipo_requerido, prerequisitos,
            descricao_mecanica, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            t.nome,
            t.tipo,
            t.classe,
            t.arquetipo_requerido,
            t.prerequisitos,
            t.descricao_mecanica,
            t.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def get_class(nome: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Obtém detalhes completos de uma classe pelo nome ou nome em inglês."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM classes WHERE nome LIKE ? OR nome_en LIKE ?
    """, (f"%{nome}%", f"%{nome}%"))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["testes_resistencia"] = json.loads(d["testes_resistencia"])
    d["tabela_progressao"] = json.loads(d["tabela_progressao"])
    d["caracteristicas_classe"] = json.loads(d["caracteristicas_classe"])
    d["recursos_customizacao"] = json.loads(d["recursos_customizacao"])
    return d


def list_classes(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Lista todas as classes cadastradas."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, nome, nome_en, tipo_conjurador, dado_vida, dado_chakra, pagina_inicio FROM classes ORDER BY nome")
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def query_archetypes(
    classe_nome: Optional[str] = None,
    nome: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta arquétipos por classe ou por nome."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM archetypes WHERE 1=1"
    params = []

    if classe_nome:
        query += " AND classe_nome LIKE ?"
        params.append(f"%{classe_nome}%")
    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")

    query += " ORDER BY classe_nome, nivel_obtencao, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        d = dict(r)
        d["caracteristicas"] = json.loads(d["caracteristicas"])
        results.append(d)

    conn.close()
    return results


def query_class_talents(
    classe: Optional[str] = None,
    tipo: Optional[str] = None,
    nome: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta talentos de classe por classe associada, tipo ou nome."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM class_talents WHERE 1=1"
    params = []

    if classe:
        query += " AND (classe LIKE ? OR classe = 'Geral')"
        params.append(f"%{classe}%")
    if tipo:
        query += " AND tipo LIKE ?"
        params.append(f"%{tipo}%")
    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")

    query += " ORDER BY tipo, classe, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


# ==========================================
# Inserções de Equipamentos e Regras Gerais
# ==========================================

def insert_weapons(weapons: List[Weapon], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere armas no banco de dados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM weapons;")

    inserted = 0
    for w in weapons:
        cursor.execute("""
        INSERT INTO weapons (
            nome, categoria, custo_ryo, dano, propriedades,
            grupo_arma, volume, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            w.nome,
            w.categoria,
            w.custo_ryo,
            w.dano,
            w.propriedades,
            w.grupo_arma,
            w.volume,
            w.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_armors(armors: List[Armor], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere armaduras e escudos no banco de dados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM armors;")

    inserted = 0
    for a in armors:
        cursor.execute("""
        INSERT INTO armors (
            nome, tipo, custo_ryo, bonus_ca, bonus_des_max,
            volume, efeito_especial, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            a.nome,
            a.tipo,
            a.custo_ryo,
            a.bonus_ca,
            a.bonus_des_max,
            a.volume,
            a.efeito_especial,
            a.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_fuinjutsu_seals(seals: List[FuinjutsuSeal], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere selos de fuinjutsu no banco de dados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM fuinjutsu_seals;")

    inserted = 0
    for s in seals:
        cursor.execute("""
        INSERT INTO fuinjutsu_seals (
            nome, tipo_item, rank, grau_selo, custo_ryo, efeito_mecanico, pagina
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            s.nome,
            s.tipo_item,
            s.rank,
            s.grau_selo,
            s.custo_ryo,
            s.efeito_mecanico,
            s.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_conditions(conditions: List[ConditionRule], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere condições no banco de dados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM conditions;")

    inserted = 0
    for c in conditions:
        cursor.execute("""
        INSERT OR REPLACE INTO conditions (
            nome, categoria, descricao_mecanica, pagina
        ) VALUES (?, ?, ?, ?)
        """, (
            c.nome,
            c.categoria,
            c.descricao_mecanica,
            c.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


def insert_combat_rules(rules: List[CombatRule], db_path: str = DEFAULT_DB_PATH, clear_first: bool = False) -> int:
    """Insere regras de combate no banco de dados."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    if clear_first:
        cursor.execute("DELETE FROM combat_rules;")

    inserted = 0
    for r in rules:
        cursor.execute("""
        INSERT OR REPLACE INTO combat_rules (
            chave, titulo, descricao_mecanica, dados_estruturados, pagina
        ) VALUES (?, ?, ?, ?, ?)
        """, (
            r.chave,
            r.titulo,
            r.descricao_mecanica,
            json.dumps(r.dados_estruturados, ensure_ascii=False),
            r.pagina
        ))
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


# ==========================================
# Consultas de Equipamentos e Regras Gerais
# ==========================================

def query_weapons(
    nome: Optional[str] = None,
    categoria: Optional[str] = None,
    grupo: Optional[str] = None,
    propriedade: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta armas por nome, categoria, grupo ou propriedade."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM weapons WHERE 1=1"
    params = []

    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if categoria:
        query += " AND categoria LIKE ?"
        params.append(f"%{categoria}%")
    if grupo:
        query += " AND grupo_arma LIKE ?"
        params.append(f"%{grupo}%")
    if propriedade:
        query += " AND propriedades LIKE ?"
        params.append(f"%{propriedade}%")

    query += " ORDER BY categoria, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def query_armors(
    nome: Optional[str] = None,
    tipo: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta armaduras e escudos por tipo ou nome."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM armors WHERE 1=1"
    params = []

    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if tipo:
        query += " AND tipo LIKE ?"
        params.append(f"%{tipo}%")

    query += " ORDER BY tipo, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def query_fuinjutsu_seals(
    nome: Optional[str] = None,
    rank: Optional[str] = None,
    tipo_item: Optional[str] = None,
    grau: Optional[str] = None,
    max_custo: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta selos de fuinjutsu por nome, rank, tipo de item, grau ou custo máximo."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM fuinjutsu_seals WHERE 1=1"
    params = []

    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if rank:
        query += " AND rank LIKE ?"
        params.append(f"%{rank}%")
    if tipo_item:
        query += " AND tipo_item LIKE ?"
        params.append(f"%{tipo_item}%")
    if grau:
        query += " AND grau_selo LIKE ?"
        params.append(f"%{grau}%")
    if max_custo is not None:
        query += " AND custo_ryo <= ?"
        params.append(max_custo)

    query += " ORDER BY rank, custo_ryo, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def query_conditions(
    nome: Optional[str] = None,
    categoria: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Consulta condições por nome ou categoria (Elemental, Físico, Mental, Sensorial, Geral)."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM conditions WHERE 1=1"
    params = []

    if nome:
        query += " AND nome LIKE ?"
        params.append(f"%{nome}%")
    if categoria:
        query += " AND categoria LIKE ?"
        params.append(f"%{categoria}%")

    query += " ORDER BY categoria, nome"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results


def get_combat_rule(chave: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Obtém uma regra de combate pela chave única."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM combat_rules WHERE chave LIKE ?", (f"%{chave}%",))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    d = dict(row)
    d["dados_estruturados"] = json.loads(d["dados_estruturados"])
    return d


def list_combat_rules(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Lista todas as regras de combate cadastradas."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT chave, titulo, descricao_mecanica, dados_estruturados, pagina FROM combat_rules ORDER BY id")
    rows = cursor.fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["dados_estruturados"] = json.loads(d["dados_estruturados"])
        results.append(d)
    conn.close()
    return results


