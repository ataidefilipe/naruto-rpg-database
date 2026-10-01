"""
Modelos Pydantic para Classes, Progressão, Arquétipos e Talentos de Classe (Naruto 5e).
Regra estrita: Apenas regras e dados mecânicos (Zero Fluff, Zero Inferência).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ClassProgressionRow(BaseModel):
    """Linha da tabela de progressão de nível (1 a 20) de uma classe."""
    nivel: int = Field(..., description="Nível do personagem (1-20)")
    bonus_proficiencia: str = Field(..., description="Bônus de proficiência (+3 a +9)")
    caracteristicas: List[str] = Field(default_factory=list, description="Lista de características obtidas neste nível")
    jutsu_conhecidos: Optional[int] = Field(None, description="Quantidade de jutsus conhecidos")
    rank_max_jutsu: Optional[str] = Field(None, description="Rank mais alto de jutsu que pode ser conjurado (ex: Rank-D, Rank-C, etc.)")
    colunas_extras: Dict[str, Any] = Field(default_factory=dict, description="Outras colunas específicas da classe (ex: Ataque Letal, Dado de Cozinha, etc.)")


class FeatureDetail(BaseModel):
    """Característica de classe ou de arquétipo."""
    nome: str
    nivel: Optional[int] = None
    descricao: str
    usos: Optional[str] = None


class Archetype(BaseModel):
    """Subclasse / Arquétipo de uma classe (ex: Sedutor, Ilusionista, Guarda da Lâmina)."""
    nome: str = Field(..., description="Nome do arquétipo/subclasse")
    classe_nome: str = Field(..., description="Nome da classe à qual pertence")
    tipo_arquetipo: str = Field(..., description="Tipo do arquétipo (Compromisso, Credo, Doutrina, Tradição, etc.)")
    nivel_obtencao: int = Field(..., description="Nível no qual a subclasse é escolhida (2 ou 3)")
    descricao_mecanica: str = Field(..., description="Descrição puramente mecânica das regras da subclasse")
    caracteristicas: List[FeatureDetail] = Field(default_factory=list, description="Lista de habilidades/recursos concedidos pela subclasse")
    pagina: Optional[int] = None


class ClassTalent(BaseModel):
    """Talento exclusivo de classe ou de arquétipo (pág 342-358 de Classes.pdf)."""
    nome: str
    tipo: str = Field(..., description="Tipo de talento: Arquétipo, Conjuntor ou Marcial")
    classe: str = Field(..., description="Classe associada (ex: Especialista em Genjutsu, Ninja Caçador, etc.)")
    arquetipo_requerido: Optional[str] = None
    prerequisitos: Optional[str] = None
    descricao_mecanica: str
    pagina: Optional[int] = None


class ClassEntity(BaseModel):
    """Entidade completa de uma Classe de Naruto 5e."""
    nome: str = Field(..., description="Nome da classe em português")
    nome_en: Optional[str] = Field(None, description="Nome original em inglês")
    tipo_conjurador: str = Field(..., description="Grau de conjuração: Alto (Full Caster), Médio (Half Caster) ou Baixo (Martial)")
    dado_vida: str = Field(..., description="Dado de Vida (ex: 1d6, 1d8, 1d10, 1d12)")
    dado_chakra: str = Field(..., description="Dado de Chakra (ex: 1d6, 1d8, 1d10, 1d12)")
    hp_primeiro_nivel: str = Field(..., description="Pontos de vida no 1º nível (ex: 6 + mod de Constituição)")
    chakra_primeiro_nivel: str = Field(..., description="Pontos de chakra no 1º nível (ex: 12 + mod de Constituição)")
    proficiencias_armaduras: Optional[str] = None
    proficiencias_armas: Optional[str] = None
    proficiencias_ferramentas: Optional[str] = None
    testes_resistencia: List[str] = Field(default_factory=list, description="Testes de resistência nos quais a classe é proficiente")
    pericias_escolha: Optional[str] = Field(None, description="Opções de perícias iniciais")
    equipamento_inicial: Optional[str] = Field(None, description="Equipamento fornecido no 1º nível")
    tabela_progressao: List[ClassProgressionRow] = Field(default_factory=list, description="Tabela de progressão dos 20 níveis")
    caracteristicas_classe: List[FeatureDetail] = Field(default_factory=list, description="Lista de recursos de classe base")
    recursos_customizacao: List[Dict[str, Any]] = Field(default_factory=list, description="Opções modulares de classe (ex: Miragens Maleáveis, Façanhas, etc.)")
    pagina_inicio: int
