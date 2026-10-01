"""
Modelos Pydantic para Armas, Armaduras, Selos de Fuinjutsu, Condições e Regras de Combate (Naruto 5e).
Regra estrita: Apenas regras e dados mecânicos (Zero Fluff, Zero Inferência).
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Weapon(BaseModel):
    """Arma do sistema Naruto 5e (Simples, Marcial ou Exótica)."""
    nome: str = Field(..., description="Nome da arma (ex: Kunai, Katana, Shuriken)")
    categoria: str = Field(..., description="Categoria (ex: Corpo a Corpo Simples, Alcance Marcial, Exótica)")
    custo_ryo: str = Field(..., description="Custo em Ryo (ex: 10 Ryo, 40 Ryo)")
    dano: str = Field(..., description="Fórmula e tipo de dano (ex: 1d4 Perfuração, 1d8 Cortante)")
    propriedades: str = Field(..., description="Propriedades mecânicas (ex: Leve, Sutil, Arremessado (30/60))")
    grupo_arma: str = Field(..., description="Grupo de arma (ex: Lâmina, Arremesso, Munição)")
    volume: str = Field(default="1", description="Espaço de volume ocupado no inventário")
    pagina: Optional[int] = None


class Armor(BaseModel):
    """Armadura ou Escudo do sistema Naruto 5e."""
    nome: str = Field(..., description="Nome da armadura (ex: Tecido Acolchoado, Jaqueta de Combate)")
    tipo: str = Field(..., description="Tipo de armadura (Armadura Leve, Armadura Média, Armadura Pesada)")
    custo_ryo: str = Field(..., description="Custo em Ryo (ex: 100 ryo, 750 ryo)")
    bonus_ca: str = Field(..., description="Bônus concedido na Classe de Armadura (ex: +1, +4)")
    bonus_des_max: str = Field(default="-", description="Limite de bônus de Destreza aplicável (ex: Máximo +7, Max. +2)")
    volume: str = Field(default="1", description="Espaço de volume ocupado no inventário")
    efeito_especial: Optional[str] = Field(None, description="Propriedades ou efeitos especiais (ex: Camuflar, Fortificado, Volumoso)")
    pagina: Optional[int] = None


class FuinjutsuSeal(BaseModel):
    """Selo de Aprimoramento de Fuinjutsu para Armas ou Armaduras."""
    nome: str = Field(..., description="Nome do selo (ex: SELO FLAMEJANTE (MENOR), SELO CHOCANTE (SUPREMO))")
    tipo_item: str = Field(..., description="Item aplicável: 'Arma' ou 'Armadura'")
    rank: str = Field(..., description="Rank do selo: Rank-D, Rank-C, Rank-B, Rank-A ou Rank-S")
    grau_selo: Optional[str] = Field(None, description="Grau do selo: Menor, Padrão, Maior, Mestre, Supremo")
    custo_ryo: int = Field(..., description="Custo em Ryo para adquirir/criar o selo")
    efeito_mecanico: str = Field(..., description="Descrição puramente mecânica das regras e benefícios do selo")
    pagina: Optional[int] = None


class ConditionRule(BaseModel):
    """Condição de status do sistema Naruto 5e."""
    nome: str = Field(..., description="Nome da condição (ex: Queimado, Sangramento, Chocado, Incapacitado)")
    categoria: str = Field(..., description="Categoria da condição: Elemental, Físico, Mental, Sensorial ou Geral")
    descricao_mecanica: str = Field(..., description="Regras mecânicas completas da condição, incluindo graus se aplicável")
    pagina: Optional[int] = None


class CombatRule(BaseModel):
    """Regra de combate central (ex: Superioridade Elemental, Confronto de Jutsu, Leia o Inimigo)."""
    chave: str = Field(..., description="Identificador único (ex: superioridade_elemental, confronto_clash, leia_inimigo)")
    titulo: str = Field(..., description="Título da regra")
    descricao_mecanica: str = Field(..., description="Descrição mecânica detalhada das regras")
    dados_estruturados: Dict[str, Any] = Field(default_factory=dict, description="Dados numéricos/estruturados (ex: roda elemental, tabela de bônus)")
    pagina: Optional[int] = None
