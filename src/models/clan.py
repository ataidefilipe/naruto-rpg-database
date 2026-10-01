from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ClanFeature(BaseModel):
    """Característica ou recurso mecânico exclusivo de um clã."""
    nome: str
    descricao: str
    nivel: Optional[int] = None
    usos: Optional[str] = None


class LatentTrait(BaseModel):
    """Habilidade de linhagem sanguínea latente."""
    nome: str
    custo_pontos: int
    pre_requisito: Optional[str] = None
    descricao: str


class Clan(BaseModel):
    """Modelo estrito para representação mecânica de Clãs shinobi.
    Zero inferência: armazena estritamente regras, bônus numéricos e traços.
    """
    id: Optional[int] = None
    nome: str
    aumento_atributos_raw: str  # Texto literal extraído (ex: "+2 Inteligência, +1 Sabedoria")
    aumento_atributos: Dict[str, int] = Field(default_factory=dict)  # Ex: {"Inteligência": 2, "Sabedoria": 1}
    deslocamento: str  # Ex: "9 Metros" ou "30 pés"
    pericias: List[str] = Field(default_factory=list)
    idiomas: List[str] = Field(default_factory=list)
    recursos: List[ClanFeature] = Field(default_factory=list)
    tracos_latentes: List[LatentTrait] = Field(default_factory=list)
    pagina: int
