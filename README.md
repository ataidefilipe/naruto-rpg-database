# 🍃 Naruto 5e Database — Compêndio Shinobi RPG

Projeto dedicado a converter, normalizar e estruturar os dados mecânicos do sistema de RPG de mesa **Naruto 5e** (adaptação fan-made do conjunto de regras de **Dungeons & Dragons 5ª Edição**) para um **banco de dados estruturado**, possibilitando consultas rápidas e filtros analíticos para jogadores e mestres durante as partidas.

> 📜 **Documentação Completa do Sistema:** Para a referência exaustiva da arquitetura de dados (todas as 11 tabelas SQLite e índices), dicionário de campos, arquitetura do backend FastAPI, especificações de rotas e frontend SPA, consulte [docs/DOCUMENTACAO_SISTEMA.md](docs/DOCUMENTACAO_SISTEMA.md).

---

## 🎯 Filosofia de Dados & Diretrizes

1. **Apenas Mecânica ("Crunch Only"):**
   - Todo o conteúdo narrativo de introdução, "flavor text" e historinhas de exemplo (*fluff*) é descartado no processo de ingestão.
   - O foco reside exclusivamente em: **regras, valores numéricos, categorizações, dados de vida/chakra, condições, custos, alcances, durações, palavras-chave, vantagens e desvantagens**.
2. **Zero Inferência (Fidelidade Estrita ao Texto):**
   - **Nada pode ser deduzido ou presumido.** Se um jutsu não especifica salvaguarda ou duração no livro, o campo é registrado como nulo (`null`), jamais preenchido com suposições de regras gerais de D&D.
3. **Pipeline de Extração Robusto (PDF Block Parser via PyMuPDF):**
   - Os arquivos de texto simples em Markdown gerados de PDFs com duas colunas sofrem com entrelaçamento horizontal de linhas (a coluna da esquerda se mistura com a da direita).
   - O pipeline utiliza leitura geométrica direta dos arquivos originais em [`PDFs/`](file:///d:/Python%20Projetos/narutorpg/PDFs) via coordenadas $X, Y$ (`pymupdf`), garantindo isolamento total entre colunas antes da extração estruturada.

---

## 📚 Estrutura do Repositório & Fontes de Dados

Os dados brutos provêm dos 4 livros oficiais do sistema (presentes em [`PDFs/`](file:///d:/Python%20Projetos/narutorpg/PDFs)):

```
narutorpg/
├── data/
│   └── naruto5e.db          # Banco SQLite unificado com 11 tabelas indexadas
├── docs/
│   └── DOCUMENTACAO_SISTEMA.md # Referência técnica completa do sistema
├── PDFs/                    # Manuais originais em PDF
│   ├── Clas.pdf             # Estudos da Tsunade (Clãs e Linhagens)
│   ├── Classes.pdf          # Observações do Orochimaru (Classes e Arquétipos)
│   ├── Jutsus.pdf           # Anotações do Jiraiya (Compêndio de Técnicas)
│   └── Regras Gerais.pdf    # Manual Shinobi (Regras Básicas e Mecânicas)
├── scripts/                 # Scripts autônomos de ETL e normalização
├── src/
│   ├── api/                 # Backend REST FastAPI (rotas e documentação Swagger)
│   ├── db/                  # Conexão SQLite e schemas relacionais
│   ├── extractor/           # Motor de extração geométrica de PDFs
│   ├── frontend/            # Interface SPA Vue 3 + Tailwind CSS (100% offline)
│   └── models/              # Modelos Pydantic tipados
├── query.py                 # Interface CLI de consulta rápida via terminal
├── run_app.py               # Launcher do Painel Tático Web (FastAPI + SPA)
└── README.md
```

---

## 🔍 Visão Prática dos Dados (Dicionário de Entidades)

### 1. ⚡ Compêndio Unificado de Jutsus (~1.660+ técnicas)
> **Unificação Central:** Todos os jutsus do sistema pertencem à mesma entidade/tabela `jutsus`. Isso inclui tanto os **~1.260 jutsus gerais** de [`Jutsus.pdf`](file:///d:/Python%20Projetos/narutorpg/PDFs/Jutsus.pdf) quanto os **~404 jutsus exclusivos de clã** de [`Clas.pdf`](file:///d:/Python%20Projetos/narutorpg/PDFs/Clas.pdf) (Hijutsus, técnicas de linhagem e Kekkei Genkai).

Campos extraídos estritamente conforme a ficha da técnica:

| Campo | Tipo | Descrição / Exemplo |
| :--- | :--- | :--- |
| `nome` | String | Nome oficial da técnica (ex: *Rasengan*, *Esfera de Insetos*, *Chidori*). |
| `classificacao` | Enum | `Ninjutsu`, `Genjutsu`, `Taijutsu`, `Bukijutsu`. |
| `natureza_estilo` | String | `Não Elemental`, `Katon`, `Suiton`, `Doton`, `Futon`, `Raiton`, `Médico`, `Invocação`, etc. |
| `rank` | Enum | `Rank-E`, `Rank-D`, `Rank-C`, `Rank-B`, `Rank-A`, `Rank-S`. |
| `tempo_conjuracao` | String | `1 Ação`, `1 Ação Bônus`, `1 Reação`. |
| `alcance` | String | `Próprio`, `Toque`, `9 metros (30 pés)`, etc. |
| `duracao` | String | `Instantâneo`, `Concentração, até 1 minuto`, etc. |
| `componentes` | Array[Enum] | `SM` (Selos de Mão), `FN` (Foco Ninja), `MC` (Movimento Corporal). |
| `custo_chakra` | Int | Quantidade numérica de Chakra necessária para conjurar. |
| `palavras_chave` | Array[String] | Tags como `Conflito`, `Fuinjutsu`, `Hijutsu`, `Kinjutsu`, `Invocação`. |
| `cla` | String/Null | Nome do clã a que pertence (ex: `"Aburame"`, `"Uchiha"`, `"Nara"`) ou `null` se for geral. |
| `exclusivo_cla` | Boolean | `true` se for técnica exclusiva de clã (extraída de `Clas.pdf`), `false` se for geral. |
| `efeito_mecanico` | Text | Descrição estrita das regras aplicadas pela técnica. |
| `dano_formula` | String/Null | Expressão de dano (ex: `4d6`, `2d8 + mod`). |
| `dano_tipo` | String/Null | `Fogo`, `Cortante`, `Vento`, `Terra`, `Veneno`, etc. |
| `salvaguarda` | Enum/Null | Atributo exigido do alvo (`Força`, `Destreza`, `Constituição`, etc.). |
| `condicoes` | Array/Null | `Envenenado`, `Contido`, `Cego`, `Caído`, etc. |
| `vantagem_desvantagem` | Text/Null | Concessão explícita de vantagem/desvantagem mecânica. |
| `em_niveis_mais_altos` | Text/Null | Regra exata de aumento de dano/custo quando conjurado em Rank superior. |

---

### 2. 🧬 Clãs (`Clas.pdf` — 40+ Clãs e Linhagens Latentes)
Apenas traços de regras e números para montagem da ficha:

| Campo | Tipo | Descrição / Exemplo |
| :--- | :--- | :--- |
| `nome` | String | Nome do clã (ex: *Uchiha*, *Hyuga*, *Aburame*, *Sem Clã*). |
| `aumento_atributos` | JSON | Bônus de habilidade (ex: `{"Inteligencia": 2, "Sabedoria": 1}`). |
| `deslocamento` | String | Velocidade básica de caminhada (ex: `9 metros / 30 pés`). |
| `recursos_mecanicos` | List[JSON] | Lista de habilidades (nome, nível em que ganha, usos por descanso, efeito mecânico). |
| `jutsus_exclusivos` | Array[Int/ID] | Relação direta (chaves estrangeiras) apontando para os jutsus do clã na tabela unificada `jutsus`. |
| `linhagem_latente` | JSON/Null | Regras e benefícios concedidos pela linhagem de sangue latente. |

---

### 3. 🥋 Classes & Arquétipos (`Classes.pdf` — 11 Classes)
Configuração mecânica e progressão do 1º ao 20º nível:

| Campo | Tipo | Descrição / Exemplo |
| :--- | :--- | :--- |
| `nome` | String | Nome da classe (ex: *Especialista em Taijutsu*, *Ninja Médico*). |
| `dado_vida` | String | `1d6`, `1d8`, `1d10`, `1d12`. |
| `dado_chakra` | String | `1d8`, `1d10`, `1d12`. |
| `nivel_jutsu` | Enum | `Alto` (Full Caster), `Médio` (Half Caster), `Baixo` (Martial). |
| `proficiencias` | JSON | Armaduras, armas, ferramentas, salvaguardas e perícias elegíveis. |
| `progressao_niveis` | List[JSON] | Tabela de 1 a 20: bônus de proficiência, recursos obtidos, jutsus conhecidos, rank máximo. |
| `arquetipos` | List[JSON] | Subclasses com regras obtidas em níveis específicos. |
| `talentos_classe` | List[JSON] | Talentos exclusivos disponíveis para a classe e arquétipo. |

---

### 4. ⚙️ Regras Gerais, Combate & Equipamentos (`Regras Gerais.pdf`)
Tabelas e sistemas objetivos de regras:

- **Superioridade Elemental:** Círculo estrito de vantagens:
  $$\text{Fogo} > \text{Vento} > \text{Raio} > \text{Terra} > \text{Água} > \text{Fogo}$$
  - *Regra explícita:* O elemento superior realiza ataque ou teste de confronto com **Vantagem**; o inferior rola normalmente.
- **Mecânica de Confronto (*Clash*):** Teste resistido imediato quando duas técnicas de choque se encontram no mesmo turno:
  - *Ninjutsu:* Teste de Ninshou vs Ninshou.
  - *Taijutsu:* Teste de Artes Marciais vs Artes Marciais.
- **Tabelas de Itens e Armas:** Custo em Ryo ($1\text{ Ryo} \approx 1\text{ GP}$), dano, tipo e propriedades de combate.
- **Selos de Fuinjutsu:** Selamentos de armas e armaduras por Rank (D a S) com efeitos numéricos diretos.
- **Talentos:** Lista categorizada com requisitos exatos e bônus mecânicos.

---

## 🛠️ Arquitetura de Extração (ETL)

```mermaid
flowchart LR
    A["PDFs Oficiais (PDFs/)"] --> B["PyMuPDF (fitz)
    Extração por Blocos X/Y"]
    B --> C["Limpeza & Normalização
    Zero Lore / Crunch Only"]
    C --> D["Validação Estrita
    (Pydantic Schemas)"]
    D --> E[("Banco de Dados
    SQLite / JSON")]
    E --> F["Consultas & Filtros Rápidos
    (Rank, Elemento, Custo, Efeito)"]
```

### Por que Regex sobre Markdown não basta:
- PDFs diagramados em duas colunas misturam linhas da esquerda e da direita quando exportados como texto plano simples.
- A extração via `pymupdf` analisa a caixa delimitadora (`bounding box`) de cada coluna individualmente, garantindo que o texto extraído seja sequencial e sem truncamento ou fusão indevida.
- A validação com **Pydantic** assegura que os tipos numéricos (custo, dados, ranks) estejam padronizados e indexáveis.

---

## 🚀 Status de Implementação

- [x] **Compêndio Unificado de Jutsus:** 1.677 jutsus (1.273 gerais + 404 de clãs) ingeridos e normalizados em `data/naruto5e.db`.
- [x] **Clãs & Linhagens Latentes:** 45 Clãs e 473 Habilidades Latentes ingeridos com atributos, velocidade, recursos e vínculos diretos.
- [x] **Classes, Progressão 1-20, Arquétipos & Talentos:** 11 Classes completas, tabelas de nível 1 a 20, 74 Arquétipos detalhados e 75 Talentos de Classe ingeridos.
- [x] **Equipamentos, Selos de Fuinjutsu, Condições & Regras de Combate (`Regras Gerais.pdf`):** 18 Armaduras e Escudos, 68 Armas, 139 Selos de Fuinjutsu (Rank D a S), 31 Condições de Status com regras de graus e 3 Regras de Combate nucleares (Superioridade Elemental, Clash, Leia o Inimigo).
- [x] **Backend REST API (FastAPI):** Servidor local rápido sem autenticação (`src/api/`) com 12+ endpoints analíticos, suporte a CORS aberto e Swagger UI interativo.
- [x] **Frontend SPA Tático (Vue 3 + Tailwind):** Painel web de alta densidade (`src/frontend/index.html`), 100% autossuficiente e offline, com alternância de visualização (planilha/cartão), modal de regras e cópia para área de transferência (`📋 Copiar Regra`).
- [x] **Painel Comparativo de Clãs:** Matriz analítica de todos os 45 clãs com filtros massivos, ordenação dinâmica em todas as colunas e comparador síncrono Lado a Lado (2 a 4 clãs) com presets rápidos e exportação Markdown.
- [x] **Calculadora de Confronto (Clash):** Motor de cálculo da roda de superioridade elemental, vantagens e bônus por rank superior e acréscimo de chakra.
- [x] **Launcher em Comando Único:** Executável `python run_app.py` que sobe o servidor e abre automaticamente a interface no navegador.
- [x] **Ferramenta CLI de Consulta (`query.py`):** Filtros analíticos rápidos diretamente no terminal para todas as 11 entidades e comparação de clãs.
- [x] **Documentação Técnica Exaustiva:** Documento completo em [`docs/DOCUMENTACAO_SISTEMA.md`](docs/DOCUMENTACAO_SISTEMA.md).

---

## 💻 Painel Tático Web (FastAPI + Vue 3 SPA)

O sistema conta com um **Painel Tático Web** de alta performance, projetado especialmente para ser rápido e denso durante as sessões de jogo:

### 🌟 Destaques da Interface:
- **100% Offline & Autossuficiente:** Vue 3 e Tailwind CSS rodam diretamente a partir de arquivos locais em `src/frontend/static/`. Não há requisições a CDNs ou dependência de internet.
- **Zero Atrito:** Configurado para uso pessoal local (`localhost`), sem necessidade de login, tokens ou chaves de API.
- **Modos de Exibição:** Alterne instantaneamente entre **Modo Tabela (Planilha Compacta)** para máxima densidade de leitura e **Modo Cartão**.
- **Filtros Massivos Simultâneos:**
  - 🔍 Busca textual em tempo real por nome ou descrição mecânica (com debounce).
  - 🎚️ Seletores de Ranks (Rank-E a Rank-S).
  - ⚡ Classificações (Ninjutsu, Taijutsu, Genjutsu, Bukijutsu).
  - 🔥 Naturezas e Estilos Elementais (Katon, Suiton, Doton, Futon, Raiton, Não Elemental, Médico, etc.).
  - 🧬 Filtro por Clã e seletor de exclusividade (Gerais vs. Exclusivos de Clã).
  - 🧪 Sliders e Presets de Custo de Chakra (0-5, 6-10, 11-18, 19+).
  - ⏱️ Tempos de Ação (1 Ação, 1 Ação Bônus, 1 Reação).
  - 🛡️ Salvaguarda Exigida (FOR, DES, CON, INT, SAB, CAR).
  - 💥 Tipos de Dano e Condições Aplicadas (Queimado, Contido, Atordoado, etc.).
  - 🏷️ Tags de Palavras-Chave (Conflito, Fuinjutsu, Kinjutsu, etc.).
  - 🎲 Toggles: *Apenas com Vantagem/Desvantagem* e *Apenas com Upcast*.
- **⚖️ Comparador Tático de Clãs:**
  - **Modo 1: Matriz Geral (Spreadsheet Analítico):** Tabela densa com todos os 45 clãs, ordenável por qualquer coluna e filtrável por atributo (+2/+1), mobilidade, perícias concedidas, ranks de jutsus acessíveis, estilos elementais e presença de linhagens latentes.
  - **Modo 2: Comparativo Lado a Lado (2 a 4 Clãs):** Colunas síncronas confrontando atributos, deslocamento, perícias, recursos de linhagem, arsenal de jutsus (com modal e cópia de regras) e árvore de compra de poderes latentes.
  - **Presets Temáticos:** Acesso em 1 clique para matchups clássicos (*Dojutsus*, *Fundadores*, *Ino-Shika-Cho*, *Linhagens de Cura*).
  - **Exportação Markdown:** Botão `📋 Copiar Comparativo` que formata a tabela comparativa pronta para colar no Discord, fórum ou ficha.
- **Cópia Instantânea (`📋 Copiar Regra`):** Um clique formata a regra mecânica completa em Markdown e a copia para o clipboard, pronta para envio no Discord, Roll20 ou Foundry VTT.
- **Calculadora de Confronto (Clash):** Testador interativo da pág. 170:
  $$\text{Fogo} > \text{Vento} > \text{Relâmpago} > \text{Terra} > \text{Água} > \text{Fogo}$$
  Aplica os bônus numéricos por rank superior (+2 por degrau) e chakra investido, calculando vantagens, testes resistidos e penalidades ao perdedor.

### 🚀 Como Iniciar a Aplicação Web:

Execute o comando:
```bash
python run_app.py
```
> O servidor Uvicorn iniciará em `http://127.0.0.1:8000` e seu navegador padrão será aberto automaticamente.
> A documentação Swagger de todos os endpoints está disponível em [http://localhost:8000/docs](http://localhost:8000/docs).

---

## ⌨️ Interface CLI de Terminal (`query.py`)

Para consultas rápidas sem abrir o navegador, utilize o script `query.py`:
```bash
# 1. Listar todas as 11 Classes
python query.py --classes

# 2. Consultar ficha completa de uma Classe (dados, proficiências, progressão 1-20 e arquétipos)
python query.py --info-classe "Genjutsu"
python query.py --info-classe "Caçador"

# 3. Listar Arquétipos e suas regras mecânicas por nível
python query.py --arquetipos "Ninja Caçador"
python query.py --arquetipos "Especialista em Genjutsu"
python query.py --nome-arquetipo "Sedutor"

# 4. Consultar Talentos de Classe e Arquétipo
python query.py --talentos-classe "Ninja Médico"
python query.py --tipo-talento "Arquétipo"

# 5. Consultar ficha mecânica completa de um Clã e seus Jutsus
python query.py --info-cla Uchiha
python query.py --info-cla Hyūga

# 6. Comparar clãs lado a lado (atributos, deslocamento, recursos, jutsus e latentes)
python query.py --comparar-clas "Uchiha,Hyūga,Senju"

# 7. Buscar clãs por bônus de atributo
python query.py --cla-atributo Inteligência

# 8. Consultar habilidades de linhagem latente
python query.py --latente Uchiha
python query.py --latente Hyūga

# 8. Buscar jutsus com filtros de combate
python query.py --estilo Fogo --rank "Rank-C" --max-chakra 8
python query.py --save Destreza --condicao Contido --detalhe

# 9. Consultar Armas e Equipamentos
python query.py --armas
python query.py --armas Katana
python query.py --categoria-arma "Corpo a Corpo Marcial"

# 10. Consultar Armaduras e Escudos
python query.py --armaduras
python query.py --tipo-armadura "Armadura Média"

# 11. Consultar Selos de Fuinjutsu (Rank D a S, Armas e Armaduras)
python query.py --selos --rank-selo Rank-D --tipo-selo Armadura
python query.py --selos "QUENTE" --detalhe
python query.py --selos --max-ryo 500

# 12. Consultar Condições de Status e Graus
python query.py --condicoes Queimado
python query.py --categoria-condicao Elemental

# 13. Consultar Regras de Combate Centrais (Superioridade Elemental, Clash, Leia o Inimigo)
python query.py --regras-combate
python query.py --regras-combate confronto_clash
python query.py --regras-combate superioridade_elemental
python query.py --regras-combate leia_inimigo
```
