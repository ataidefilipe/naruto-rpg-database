"""
Modelos Pydantic para Usuários e Relatórios de Erros (Extração e Mecânica).
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    """Modelo para login simples (apenas nome de usuário)."""
    username: str = Field(..., min_length=2, max_length=50, description="Nome do Shinobi/Usuário")


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: str
    last_login: str


class ErrorReportCreate(BaseModel):
    """Payload para criação de um relatório de erro nas querys."""
    usuario: str = Field(..., min_length=2, max_length=50, description="Nome do usuário reportante")
    tabela_origem: str = Field(..., description="Nome da tabela de origem (jutsus, clans, classes, etc.)")
    item_id: Optional[int] = Field(None, description="ID do item no banco de dados (se aplicável)")
    item_nome: str = Field(..., min_length=1, max_length=150, description="Nome da técnica, clã, item ou regra")
    campo_afetado: Optional[str] = Field(None, description="Campo que contém o erro (ex: efeito_mecanico, dano, nome)")
    texto_atual: Optional[str] = Field(None, description="Trecho extraído com erro para referência")
    descricao_erro: str = Field(..., min_length=3, description="Descrição detalhada do erro encontrado")
    sugestao_correcao: Optional[str] = Field(None, description="Sugestão de texto correto ou correção de regra")


class ErrorReportStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pendente|em_analise|corrigido|rejeitado)$")


class ErrorReportResponse(BaseModel):
    id: int
    usuario: str
    tabela_origem: str
    item_id: Optional[int] = None
    item_nome: str
    campo_afetado: Optional[str] = None
    texto_atual: Optional[str] = None
    descricao_erro: str
    sugestao_correcao: Optional[str] = None
    status: str
    criado_em: str
    atualizado_em: Optional[str] = None


class ErrorReportListResponse(BaseModel):
    total: int
    items: List[ErrorReportResponse]
