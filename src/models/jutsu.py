from typing import List, Optional
from pydantic import BaseModel, Field


class Jutsu(BaseModel):
    """Modelo estrito para representação mecânica de Jutsus no sistema Naruto 5e.
    Zero inferência: valores ausentes no texto oficial devem ser estritamente None.
    """
    id: Optional[int] = None
    nome: str
    classificacao: str  # Ninjutsu, Genjutsu, Taijutsu, Bukijutsu
    natureza_estilo: Optional[str] = None  # Katon, Suiton, Doton, Futon, Raiton, Não Elemental, Médico, Invocação, etc.
    rank: str  # Rank-E, Rank-D, Rank-C, Rank-B, Rank-A, Rank-S
    tempo_conjuracao: str
    alcance: str
    duracao: str
    componentes: List[str] = Field(default_factory=list)  # FN, SM, MC
    custo_chakra: int
    palavras_chave: List[str] = Field(default_factory=list)
    cla: Optional[str] = None  # Nome do clã ou None se for jutsu geral
    exclusivo_cla: bool = False
    efeito_mecanico: str  # Regra estrita descrita no livro
    dano_formula: Optional[str] = None  # Expressão de dano extraída (ex: "4d6", "2d8")
    dano_tipo: Optional[str] = None  # Ex: "Fogo", "Cortante", "Veneno"
    salvaguarda: Optional[str] = None  # Atributo de resistência (ex: "Destreza", "Constituição")
    condicoes: List[str] = Field(default_factory=list)  # Ex: ["Envenenado", "Contido"]
    vantagem_desvantagem: Optional[str] = None  # Registro textual se concede vantagem/desvantagem
    em_niveis_mais_altos: Optional[str] = None  # Regra de upcasting
    origem_livro: str  # "Jutsus.pdf" ou "Clas.pdf"
    pagina: Optional[int] = None
