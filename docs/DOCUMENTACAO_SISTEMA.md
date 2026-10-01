# 📜 Documentação Completa do Sistema — Naruto 5e Database

Este documento reúne todas as informações arquiteturais, mecânicas, estruturais e operacionais do projeto **Naruto 5e Database**, consolidando as regras extraídas dos 4 manuais oficiais e o banco de dados relacional indexado em SQLite (`data/naruto5e.db`).

---

## 1. Visão Geral e Filosofia do Projeto

O objetivo do projeto é transformar o compêndio de regras do RPG de mesa **Naruto 5e** (adaptação do sistema D&D 5e traduzida por Falha Crítica RPG) em uma base de dados relacional rápida, estrita e indexada, ideal para consultas táticas durante sessões de jogo.

### Diretrizes Fundamentais:
1. **Mecânica Pura ("Crunch Only"):**
   - Todo o conteúdo narrativo, vinhetas literárias, contos introdutórios e descrições poéticas (*fluff*) foram expurgados no processo de ingestão.
   - Foram mantidos unicamente: fórmulas de dano, tipos de dados, custos numéricos de chakra, condições aplicadas, salvaguardas, vantagens/desvantagens, tempos de ação, alcances, durações, restrições e propriedades de combate.
2. **Zero Inferência:**
   - Nenhum dado ausente nos manuais foi deduzido, interpolado ou preenchido por analogia a D&D 5e. Valores ausentes permanecem explicitamente como `NULL` / `None`.
3. **Extração Geométrica Direta de PDFs:**
   - PDFs diagramados em duas colunas sofrem de entrelaçamento horizontal ao serem convertidos em arquivos de texto plano simples. O pipeline utiliza análise de caixas delimitadoras e coordenadas $(X, Y)$ via **PyMuPDF**, garantindo a integridade sequencial das colunas e tabelas.

---

## 2. Estrutura de Diretórios do Projeto

```
narutorpg/
├── data/
│   └── naruto5e.db            # Banco SQLite unificado com 11 tabelas indexadas
├── docs/
│   └── DOCUMENTACAO_SISTEMA.md # Este documento de referência
├── markdown/                  # Transcrições auxiliares MarkItDown dos livros
│   ├── Clas.md
│   ├── Classes.md
│   ├── Jutsus.md
│   └── Regras Gerais.md
├── PDFs/                      # Livros oficiais de regras
│   ├── Clas.pdf               # Estudos da Tsunade (Clãs e Linhagens Latentes)
│   ├── Classes.pdf            # Observações do Orochimaru (11 Classes e Arquétipos)
│   ├── Jutsus.pdf             # Anotações do Jiraiya (Compêndio de Técnicas)
│   └── Regras Gerais.pdf      # Manual Shinobi (Regras de Combate e Equipamento)
├── scripts/                   # Scripts autônomos de ETL / Ingestão
│   ├── ingest_clans.py        # Ingestão de Clãs e Linhagens Latentes
│   ├── ingest_classes.py      # Ingestão de Classes, Tabelas 1-20, Arquétipos e Talentos
│   ├── ingest_jutsus.py       # Ingestão do Compêndio Unificado de Jutsus
│   └── ingest_rules.py        # Ingestão de Equipamentos, Selos, Condições e Combate
├── src/
│   ├── db/
│   │   └── database.py        # Schemas SQL, conexões, inserções e queries tipadas
│   ├── extractor/
│   │   ├── clan_parser.py     # Parser de Clãs e Linhagens
│   │   ├── class_parser.py    # Parser de Classes, Progressão e Arquétipos
│   │   ├── jutsu_parser.py    # Parser geométrico unificado de Jutsus
│   │   ├── pdf_reader.py      # Motor geométrico de blocos e colunas
│   │   └── rules_parser.py    # Parser de Equipamento, Fuinjutsu, Condições e Regras
│   └── models/
│       ├── clan.py            # Modelos Pydantic para Clãs e Linhagens
│       ├── classe.py          # Modelos Pydantic para Classes, Progressão e Arquétipos
│       ├── jutsu.py           # Modelos Pydantic para Jutsus
│       └── rules.py           # Modelos Pydantic para Armas, Armaduras, Selos e Condições
├── query.py                   # Interface CLI para filtros analíticos rápidos
└── README.md                  # Apresentação do projeto e comandos de terminal
```

---

## 3. Esquema Detalhado do Banco de Dados SQLite (`data/naruto5e.db`)

O banco é composto por **11 tabelas relacionais e semiestruturadas**, com índices otimizados para busca rápida em tempo de execução:

### 3.1. Tabela `jutsus` (1.677 registros)
Unifica todas as técnicas do sistema (gerais e de clã):
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL): Nome oficial da técnica.
- `classificacao` (TEXT, NOT NULL): `Ninjutsu`, `Genjutsu`, `Taijutsu`, `Bukijutsu`.
- `natureza_estilo` (TEXT): `Fogo`, `Água`, `Terra`, `Vento`, `Relâmpago`, `Médico`, `Não Elemental`, etc.
- `rank` (TEXT, NOT NULL): `Rank-E`, `Rank-D`, `Rank-C`, `Rank-B`, `Rank-A`, `Rank-S`.
- `tempo_conjuracao` (TEXT, NOT NULL): Ex: `1 Ação`, `1 Ação Bônus`, `1 Reação`.
- `alcance` (TEXT, NOT NULL): Ex: `Próprio`, `Toque`, `9 metros`, `Linha de 18 metros`.
- `duracao` (TEXT, NOT NULL): Ex: `Instantâneo`, `Concentração, até 1 minuto`.
- `componentes` (TEXT, NOT NULL): JSON Array (`["SM"]`, `["MC"]`, `["FN"]`).
- `custo_chakra` (INTEGER, NOT NULL): Quantidade numérica inteira de Chakra.
- `palavras_chave` (TEXT, NOT NULL): JSON Array (`["Conflito"]`, `["Fuinjutsu"]`, `["Hijutsu"]`, etc.).
- `cla` (TEXT): Nome do clã a que pertence (ex: `"Uchiha"`) ou `NULL` para técnicas gerais.
- `exclusivo_cla` (BOOLEAN, NOT NULL): `1` se provém de `Clas.pdf`, `0` se provém de `Jutsus.pdf`.
- `efeito_mecanico` (TEXT, NOT NULL): Regra e mecânica integral da técnica.
- `dano_formula` (TEXT): Fórmula do dado de dano (ex: `4d6`, `2d8 + mod`).
- `dano_tipo` (TEXT): `Fogo`, `Cortante`, `Perfurante`, `Concussão`, etc.
- `salvaguarda` (TEXT): Atributo exigido (`Destreza`, `Constituição`, etc.).
- `condicoes` (TEXT, NOT NULL): JSON Array de condições aplicadas (ex: `["Queimado", "Atordoado"]`).
- `vantagem_desvantagem` (TEXT): Concessão de vantagens ou desvantagens mecânicas.
- `em_niveis_mais_altos` (TEXT): Regra exata de escalonamento numérico por upcast.
- `origem_livro` (TEXT, NOT NULL): `"Jutsus.pdf"` ou `"Clas.pdf"`.
- `pagina` (INTEGER): Número da página no respectivo livro.

**Índices:** `idx_jutsus_rank`, `idx_jutsus_natureza`, `idx_jutsus_cla`, `idx_jutsus_custo`, `idx_jutsus_classif`.

---

### 3.2. Tabela `clans` (45 registros)
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL, UNIQUE): Nome do clã (ex: *Aburame*, *Hyūga*, *Uchiha*, *Sem Clã*).
- `aumento_atributos_raw` (TEXT, NOT NULL): Texto original do bônus (ex: `"+2 Inteligência, +1 Destreza"`).
- `aumento_atributos` (TEXT, NOT NULL): JSON Dict com mapeamento numérico (ex: `{"Inteligencia": 2, "Destreza": 1}`).
- `deslocamento` (TEXT, NOT NULL): Deslocamento base (ex: `"9 metros"`).
- `pericias` (TEXT, NOT NULL): JSON Array de perícias concedidas.
- `idiomas` (TEXT, NOT NULL): JSON Array de idiomas conhecidos.
- `recursos` (TEXT, NOT NULL): JSON Array de recursos mecânicos (`ClanFeature`), contendo nome, nível de obtenção, usos por descanso e descrição mecânica.
- `pagina` (INTEGER, NOT NULL): Página em `Clas.pdf`.

**Índices:** `idx_clans_nome`.

---

### 3.3. Tabela `latent_bloodlines` (473 registros)
Habilidades de compra de Linhagem Sanguínea Latente por clã:
- `id` (INTEGER, PK, AUTOINCREMENT)
- `cla` (TEXT, NOT NULL): Nome do clã de vínculo.
- `nome_habilidade` (TEXT, NOT NULL): Nome da técnica latente.
- `custo_pontos` (INTEGER, NOT NULL): Custo em pontos de linhagem latente (1 a 5).
- `pre_requisito` (TEXT): Requisitos exigidos (atributos mínimos, níveis, técnicas).
- `descricao` (TEXT, NOT NULL): Descrição mecânica da habilidade.
- `pagina` (INTEGER, NOT NULL): Página em `Clas.pdf`.

**Índices:** `idx_latent_cla`.

---

### 3.4. Tabela `classes` (11 registros)
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL, UNIQUE): Nome em português (ex: *Ninja Caçador*, *Ninja Médico*).
- `nome_en` (TEXT): Nome original (ex: *Hunter Nin*, *Medical Nin*).
- `tipo_conjurador` (TEXT, NOT NULL): Grau de conjuração (`Alto`, `Médio`, `Baixo`).
- `dado_vida` (TEXT, NOT NULL): `1d6`, `1d8`, `1d10`, `1d12`.
- `dado_chakra` (TEXT, NOT NULL): `1d8`, `1d10`, `1d12`.
- `hp_primeiro_nivel` (TEXT, NOT NULL): Fórmula de pontos de vida no nível 1.
- `chakra_primeiro_nivel` (TEXT, NOT NULL): Fórmula de pontos de chakra no nível 1.
- `proficiencias_armaduras` (TEXT): Tipos de armaduras permitidos.
- `proficiencias_armas` (TEXT): Armas simples, marciais ou exóticas.
- `proficiencias_ferramentas` (TEXT): Ferramentas, kits médicos ou venenos.
- `testes_resistencia` (TEXT, NOT NULL): JSON Array dos 2 atributos com proficiência em salvaguarda.
- `pericias_escolha` (TEXT): Quantidade e lista de opções de perícias selecionáveis.
- `equipamento_inicial` (TEXT): Pacotes e opções de equipamento de 1º nível.
- `tabela_progressao` (TEXT, NOT NULL): JSON Array com as 20 linhas de progressão de nível contendo:
  - Bônus de Proficiência (+2 a +6)
  - Características adquiridas no nível
  - Jutsus Conhecidos
  - Dado de Dano desarmado / Ataque Furtivo / etc.
  - Slots de Chakra / Rank Máximo conjurável
- `caracteristicas_classe` (TEXT, NOT NULL): JSON Array com os detalhes de todas as habilidades de classe.
- `recursos_customizacao` (TEXT, NOT NULL): JSON Array de opções modulares de customização.
- `pagina_inicio` (INTEGER, NOT NULL): Página de início em `Classes.pdf`.

**Índices:** `idx_classes_nome`.

---

### 3.5. Tabela `archetypes` (74 registros)
Subclasses das 11 classes principais:
- `id` (INTEGER, PK, AUTOINCREMENT)
- `classe_nome` (TEXT, NOT NULL): Classe mãe associada.
- `nome` (TEXT, NOT NULL): Nome do arquétipo (ex: *Lâmina Assassina*, *Mestre dos Venenos*).
- `tipo_arquetipo` (TEXT, NOT NULL): Rótulo temático da especialização.
- `nivel_obtencao` (INTEGER, NOT NULL): Nível em que a subclasse é escolhida (normalmente 3º nível).
- `descricao_mecanica` (TEXT, NOT NULL): Regras gerais concedidas no nível base.
- `caracteristicas` (TEXT, NOT NULL): JSON Array com recursos ganhos nos níveis 3, 7, 10, 15, 18 ou 20.
- `pagina` (INTEGER): Página de referência em `Classes.pdf`.

**Índices:** `idx_archetypes_classe`, `idx_archetypes_nome`.

---

### 3.6. Tabela `class_talents` (75 registros)
Talentos específicos de cada classe ou arquétipo:
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL): Nome do talento.
- `tipo` (TEXT, NOT NULL): `Arquétipo`, `Conjuntor`, `Marcial`, `Geral`.
- `classe` (TEXT, NOT NULL): Classe associada ou `"Geral"`.
- `arquetipo_requerido` (TEXT): Subclasse requerida ou `NULL`.
- `prerequisitos` (TEXT): Níveis, atributos ou jutsus necessários.
- `descricao_mecanica` (TEXT, NOT NULL): Regra mecânica completa do talento.
- `pagina` (INTEGER): Página em `Classes.pdf`.

**Índices:** `idx_class_talents_classe`, `idx_class_talents_tipo`.

---

### 3.7. Tabela `weapons` (68 registros)
Armas simples, marciais e exóticas:
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL): Ex: *Katana*, *Kunai*, *Odachi*, *Shuriken*, *Funda*.
- `categoria` (TEXT, NOT NULL): `Corpo a Corpo Simples`, `Alcance Simples`, `Corpo a Corpo Marcial`, `Alcance Marcial`, `Exótica Corpo a Corpo`, `Exótica Alcance`.
- `custo_ryo` (TEXT, NOT NULL): Custo comercial (ex: `10 Ryo`, `30 Ryo`, `250 Ryo`).
- `dano` (TEXT, NOT NULL): Expressão e tipo de dano (ex: `1d8 Cortante`, `1d4 Perfuração`).
- `propriedades` (TEXT, NOT NULL): Propriedades como `Mortal`, `Sutil`, `Leve`, `Pesada`, `Arremessada (30/60)`.
- `grupo_arma` (TEXT, NOT NULL): `Lâmina`, `Mangal`, `Arma de Haste`, `Impacto`, `Arremesso`, `Munição`.
- `volume` (TEXT, NOT NULL): Espaço ocupado no inventário (1, 2 ou 3).
- `pagina` (INTEGER): Página em `Regras Gerais.pdf` (páginas 40 a 42).

**Índices:** `idx_weapons_nome`, `idx_weapons_categoria`.

---

### 3.8. Tabela `armors` (18 registros)
Armaduras Leves (6), Médias (6) e Pesadas (6):
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL): Ex: *Tecido Shinobi*, *Jaqueta Chunin*, *Armadura Samurai*.
- `tipo` (TEXT, NOT NULL): `Armadura Leve`, `Armadura Média`, `Armadura Pesada`.
- `custo_ryo` (TEXT, NOT NULL): Custo comercial em Ryo.
- `bonus_ca` (TEXT, NOT NULL): Bônus direto na Classe de Armadura (+1 a +8).
- `bonus_des_max` (TEXT, NOT NULL): Limite aplicável do modificador de Destreza (`Máximo +7`, `Max. +3` ou `-`).
- `volume` (TEXT, NOT NULL): Espaço no inventário (1 a 8).
- `efeito_especial` (TEXT): Propriedades especiais (ex: `Camuflar`, `Fortificado`, `Volumoso`, `Reforçado`).
- `pagina` (INTEGER): Página 35 em `Regras Gerais.pdf`.

**Índices:** `idx_armors_tipo`, `idx_armors_nome`.

---

### 3.9. Tabela `fuinjutsu_seals` (139 registros)
Melhorias de Fuinjutsu aplicadas em Armas ou Armaduras:
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL): Nome do selo (ex: *SELO QUENTE (MENOR)*, *SELO DE ESMAGAMENTO (SUPREMO)*).
- `tipo_item` (TEXT, NOT NULL): `Arma` ou `Armadura`.
- `rank` (TEXT, NOT NULL): `Rank-D`, `Rank-C`, `Rank-B`, `Rank-A`, `Rank-S`.
- `grau_selo` (TEXT): `Menor`, `Padrão`, `Maior`, `Mestre`, `Supremo`.
- `custo_ryo` (INTEGER, NOT NULL): Custo monetário de compra/criação em Ryo.
- `efeito_mecanico` (TEXT, NOT NULL): Regra e bônus aplicados ao item imbuído.
- `pagina` (INTEGER): Páginas 109 a 123 em `Regras Gerais.pdf`.

**Índices:** `idx_fuinjutsu_rank`, `idx_fuinjutsu_tipo`, `idx_fuinjutsu_nome`.

---

### 3.10. Tabela `conditions` (31 registros)
Condições de status com suas respectivas mecânicas de graus acumulativos (*ranks*):
- `id` (INTEGER, PK, AUTOINCREMENT)
- `nome` (TEXT, NOT NULL, UNIQUE): Ex: *Queimado*, *Refrigerado*, *Chocado*, *Sangramento*, *Incapacitado*, *Berserk*.
- `categoria` (TEXT, NOT NULL): `Elemental`, `Físico`, `Mental`, `Sensorial`, `Geral`.
- `descricao_mecanica` (TEXT, NOT NULL): Regras completas de penalidades por grau, testes de salvaguarda e remoção.
- `pagina` (INTEGER): Páginas 180 a 186 em `Regras Gerais.pdf`.

**Índices:** `idx_conditions_nome`, `idx_conditions_categoria`.

---

### 3.11. Tabela `combat_rules` (3 registros)
Regras centrais do combate de Naruto 5e:
- `id` (INTEGER, PK, AUTOINCREMENT)
- `chave` (TEXT, NOT NULL, UNIQUE): Identificador da regra (`superioridade_elemental`, `confronto_clash`, `leia_inimigo`).
- `titulo` (TEXT, NOT NULL): Título descritivo.
- `descricao_mecanica` (TEXT, NOT NULL): Texto completo da regra.
- `dados_estruturados` (TEXT, NOT NULL): JSON Dict com tabelas e relacionamentos diretos (ex: roda elemental, testes resistidos por rank, penalidades ao perdedor).
- `pagina` (INTEGER): Páginas 170 e 171 em `Regras Gerais.pdf`.

**Índices:** `idx_combat_rules_chave`.

---

## 4. Totais e Métricas Oficiais do Banco de Dados

```
==================================================
RESUMO COMPLETO DO BANCO data/naruto5e.db:
==================================================
jutsus                :  1677 registros
clans                 :    45 registros
latent_bloodlines     :   473 registros
classes               :    11 registros
archetypes            :    74 registros
class_talents         :    75 registros
weapons               :    68 registros
armors                :    18 registros
fuinjutsu_seals       :   139 registros
conditions            :    31 registros
combat_rules          :     3 registros
==================================================
```

---

## 5. Arquitetura do Backend REST (FastAPI)

O backend do sistema reside em `src/api/` e foi construído com **FastAPI** para oferecer respostas em sub-milissegundos para consultas locais, com documentação automática OpenAPI/Swagger.

### 5.1. Diretrizes Técnicas
- **Zero Auth / Uso Pessoal Local:** Configurado para execução em `localhost` sem travas de autenticação, tokens ou sessões, maximizando velocidade e simplicidade.
- **CORS Aberto (`allow_origins=["*"]`):** Permite acesso de qualquer cliente local ou ferramentas externas de automação.
- **Persistência SQLite Otimizada:** Consultas SQL parametrizadas aproveitando os 11 índices criados no banco.
- **Suporte a Servir SPA:** Monta os arquivos estáticos de `src/frontend/static/` e serve `index.html` na raiz (`/`).

### 5.2. Catálogo de Endpoints da API

| Método | Rota | Descrição & Parâmetros Principais |
| :--- | :--- | :--- |
| `GET` | `/` | Serve a aplicação SPA interativa (Vue 3). |
| `GET` | `/docs` | Interface interativa Swagger UI para testes de todos os endpoints. |
| `GET` | `/api/meta/filters` | Retorna listas dinâmicas de ranks, elementos, classificações, clãs, salvaguardas, danos e condições para preencher filtros. |
| `GET` | `/api/meta/counts` | Retorna a contagem exata e atualizada de registros de todas as 11 tabelas. |
| `GET` | `/api/jutsus` | Consulta com filtros massivos: `q`, `rank`, `classificacao`, `natureza`, `cla`, `apenas_cla`, `apenas_gerais`, `min_chakra`, `max_chakra`, `tempo_conjuracao`, `salvaguarda`, `dano_tipo`, `condicao`, `palavra_chave`, `possui_vantagem`, `possui_upcast`, `sort_by`, `limit`, `offset`. |
| `GET` | `/api/jutsus/{id}` | Retorna a ficha completa e sem cortes de um jutsu específico pelo seu ID. |
| `GET` | `/api/clans` | Lista resumida de todos os 45 clãs (nome, bônus de atributo, deslocamento). |
| `GET` | `/api/clans/compare/summary` | Matriz analítica resumida dos 45 clãs com métricas de jutsus, ranks acessíveis, estilos elementais, recursos e linhagens latentes. |
| `GET` | `/api/clans/compare` | Comparação detalhada simultânea de múltiplos clãs passados por vírgula (`?names=Uchiha,Hyūga,Senju`). |
| `GET` | `/api/clans/{nome}` | Ficha detalhada do clã: recursos mecânicos, proficiências, jutsus exclusivos e habilidades latentes completas. |
| `GET` | `/api/clans/latent/all` | Lista filtrável de todas as 473 habilidades latentes por clã ou por custo de pontos. |
| `GET` | `/api/classes` | Lista das 11 classes com dados de vida, dados de chakra e tipo de conjurador. |
| `GET` | `/api/classes/{nome}` | Progressão completa de níveis 1 a 20, proficiências, recursos de classe, arquétipos e talentos vinculados. |
| `GET` | `/api/classes/sub/archetypes` | Busca e filtro dos 74 arquétipos por classe ou nome. |
| `GET` | `/api/classes/sub/talents` | Busca dos 75 talentos de classe e arquétipo. |
| `GET` | `/api/equipment/weapons` | Lista e filtros das 68 armas por categoria, grupo ou custo em Ryo. |
| `GET` | `/api/equipment/armors` | Lista das 18 armaduras com bônus de CA, limite de Destreza e propriedades. |
| `GET` | `/api/equipment/fuinjutsu` | Catálogo dos 139 selos de Fuinjutsu por Rank (D a S), tipo (arma/armadura) e preço. |
| `GET` | `/api/rules/conditions` | Dicionário das 31 condições de status com tabela de graus e efeitos mecânicos. |
| `GET` | `/api/rules/combat` | Regras centrais de combate (Superioridade Elemental, Clash, Leia o Inimigo). |
| `POST` | `/api/rules/clash-calculator` | **Calculadora de Confronto (Clash):** Recebe o elemento, rank e chakra extra dos dois combatentes e calcula vantagem elemental, modificadores de teste resistido e consequências para o perdedor conforme a pág. 170. |

---

## 6. Arquitetura do Frontend SPA (Painel Tático Shinobi)

O frontend reside em `src/frontend/` e foi concebido especificamente para ser **denso, rápido e 100% autossuficiente offline**.

### 6.1. Tecnologias & Escolhas de Projeto
- **Vue 3 (Composition API):** Fornece reatividade instantânea sem necessidade de etapas de compilação ou bundlers (Webpack/Vite). O arquivo `vue.global.prod.js` fica armazenado localmente em `static/`.
- **Tailwind CSS (Standalone Local):** Armazenado em `static/tailwind.js`, eliminando dependência de conexões de internet e CDNs externos durante partidas presenciais ou sem rede.
- **Foco em Informação Tática ("Zero Lore / Alta Densidade"):**
  - Layout escuro (*Dark Mode Slate*) com tipografia limpa e tabelas condensadas.
  - Alternância imediata entre **Modo Tabela (Planilha Compacta)** e **Modo Cartão**.
  - **Filtros Massivos Combinados:** Barra lateral retrátil permitindo cruzar múltiplos atributos simultaneamente com debounce automático de digitação.
  - **Cópia Rápida para Clipboard (`📋 Copiar Regra`):** Um clique copia a regra mecânica formatada em Markdown pronta para ser colada em fichas, chat do Discord, Roll20 ou Foundry VTT.

### 6.2. Abas do Painel Tático
1. **🍃 Jutsus:** Busca e filtros sobre as 1.677 técnicas, com paginação rápida, modal de detalhamento completo de regras e escalonamento numérico por upcast.
2. **🧬 Clãs & Linhagens:** Ficha mecânica de cada um dos 45 clãs, listagem dos jutsus exclusivos de linhagem e árvore de compra de Habilidades Latentes por pontos.
3. **⚖️ Comparador de Clãs:** Painel analítico comparativo com **Modo Matriz Geral** (tabela densa dos 45 clãs com filtros por atributo, mobilidade, perícias, ranks de jutsus, estilos e ordenação dinâmica em todas as colunas) e **Modo Lado a Lado** (2 a 4 clãs simultâneos com colunas síncronas detalhando atributos, recursos de clã, arsenal de jutsus e linhagens latentes, presets temáticos como Dojutsus/Fundadores e exportação/cópia em Markdown).
4. **🥋 Classes & Arquétipos:** Ficha das 11 classes, tabela dinâmica de progressão do 1º ao 20º nível (bônus de proficiência, jutsus conhecidos, dados de chakra/vida), explorador de subclasses (arquétipos) e catálogo de talentos.
5. **🗡️ Equipamentos & Selos:** Sub-abas para Armas (dano, propriedades, peso), Armaduras (CA, limite DES, camuflagem) e Selos de Fuinjutsu (Rank D a S para armas e armaduras).
6. **⚠️ Regras & Condições:** Dicionário completo de status com regras de escalonamento de graus e regras nucleares de combate.
7. **⚔️ Calculadora de Clash:** Simulador interativo da roda elemental ($\text{Fogo} > \text{Vento} > \text{Relâmpago} > \text{Terra} > \text{Água} > \text{Fogo}$) com cômputo de bônus por rank superior e acréscimo de chakra.

---

## 7. Como Executar o Sistema

### 7.1. Execução do Painel Web Completo (Recomendado)
Para iniciar o servidor FastAPI e abrir automaticamente a interface SPA no navegador:

```bash
python run_app.py
```

- **Painel Tático (SPA):** [http://localhost:8000](http://localhost:8000)
- **Documentação Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 7.2. Execução da Interface CLI de Terminal
Para consultas rápidas diretamente pelo terminal:

```bash
# Consultar jutsus de Fogo de Rank-C com custo até 8 de chakra
python query.py --estilo Fogo --rank "Rank-C" --max-chakra 8

# Consultar ficha mecânica do Clã Uchiha
python query.py --info-cla Uchiha

# Comparar clãs lado a lado diretamente no terminal
python query.py --comparar-clas "Uchiha,Hyūga,Senju"

# Consultar progressão e arquétipos da classe Ninja Médico
python query.py --info-classe "Ninja Médico"

# Consultar regras de Confronto (Clash)
python query.py --regras-combate confronto_clash
```

### 7.3. Manutenção e Normalização do Banco
Se novos jutsus forem inseridos ou houver necessidade de revalidar a padronização dos ranks:

```bash
python scripts/normalize_db.py
```

