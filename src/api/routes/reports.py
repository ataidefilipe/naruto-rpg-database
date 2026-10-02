"""
Rotas para Relatório e Gestão de Erros de Extração / Texto Quebrado nas Querys.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Dict, Any
from src.models.report import (
    ErrorReportCreate,
    ErrorReportStatusUpdate,
    ErrorReportResponse,
    ErrorReportListResponse
)
from src.db.database import (
    create_error_report,
    list_error_reports,
    get_error_report,
    update_error_report_status,
    delete_error_report,
    DEFAULT_DB_PATH
)

router = APIRouter(prefix="/api/reports", tags=["Relatórios de Erros"])


@router.post("", response_model=ErrorReportResponse, status_code=201)
def submit_error_report(payload: ErrorReportCreate, db_path: str = DEFAULT_DB_PATH):
    """Envia um novo relatório de erro encontrado nas linhas de consulta ou texto extraído."""
    if not payload.usuario.strip():
        raise HTTPException(status_code=400, detail="Usuário é obrigatório para registrar o reporte.")
    if not payload.item_nome.strip():
        raise HTTPException(status_code=400, detail="Nome do item é obrigatório.")
    if not payload.descricao_erro.strip():
        raise HTTPException(status_code=400, detail="Descrição do erro é obrigatória.")

    try:
        report = create_error_report(
            usuario=payload.usuario,
            tabela_origem=payload.tabela_origem,
            item_nome=payload.item_nome,
            descricao_erro=payload.descricao_erro,
            item_id=payload.item_id,
            campo_afetado=payload.campo_afetado,
            texto_atual=payload.texto_atual,
            sugestao_correcao=payload.sugestao_correcao,
            db_path=db_path
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar reporte no banco: {str(e)}")


@router.get("", response_model=ErrorReportListResponse)
def get_error_reports(
    status: Optional[str] = Query(None, description="Filtro por status: pendente, em_analise, corrigido, rejeitado, todos"),
    tabela: Optional[str] = Query(None, description="Filtro por tabela de origem (jutsus, clans, classes, etc.)"),
    usuario: Optional[str] = Query(None, description="Filtro por usuário que reportou"),
    q: Optional[str] = Query(None, description="Busca livre no nome do item, descrição ou sugestão"),
    limit: int = Query(50, ge=1, le=500, description="Limite de registros por página"),
    offset: int = Query(0, ge=0, description="Offset de paginação"),
    db_path: str = DEFAULT_DB_PATH
):
    """Consulta relatórios de erros registrados com suporte a filtros e busca textual."""
    return list_error_reports(
        status=status,
        tabela_origem=tabela,
        usuario=usuario,
        q=q,
        limit=limit,
        offset=offset,
        db_path=db_path
    )


@router.get("/{report_id}", response_model=ErrorReportResponse)
def get_report_detail(report_id: int = Path(..., ge=1), db_path: str = DEFAULT_DB_PATH):
    """Obtém detalhes de um relatório de erro específico."""
    report = get_error_report(report_id, db_path=db_path)
    if not report:
        raise HTTPException(status_code=404, detail="Relatório de erro não encontrado.")
    return report


@router.patch("/{report_id}", response_model=ErrorReportResponse)
def update_report_status(
    payload: ErrorReportStatusUpdate,
    report_id: int = Path(..., ge=1),
    db_path: str = DEFAULT_DB_PATH
):
    """Atualiza o status de resolução de um relatório (pendente, em_analise, corrigido, rejeitado)."""
    updated = update_error_report_status(report_id, payload.status, db_path=db_path)
    if not updated:
        raise HTTPException(status_code=404, detail="Relatório de erro não encontrado.")
    return updated


@router.delete("/{report_id}")
def remove_report(report_id: int = Path(..., ge=1), db_path: str = DEFAULT_DB_PATH):
    """Exclui um relatório de erro do banco de dados."""
    success = delete_error_report(report_id, db_path=db_path)
    if not success:
        raise HTTPException(status_code=404, detail="Relatório de erro não encontrado.")
    return {"status": "ok", "message": f"Relatório #{report_id} excluído com sucesso."}
