"""
Rotas para Autenticação Simples de Usuários (Apenas Nome de Usuário, Sem Senha).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from src.models.report import UserLogin, UserResponse
from src.db.database import get_or_create_user, list_users, DEFAULT_DB_PATH

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/login", response_model=UserResponse)
def login(payload: UserLogin, db_path: str = DEFAULT_DB_PATH):
    """Realiza login simples apenas com o nome de usuário (sem senha). Registra o usuário se for novo."""
    username = payload.username.strip()
    if not username or len(username) < 2:
        raise HTTPException(status_code=400, detail="O nome de usuário deve conter pelo menos 2 caracteres.")
    
    try:
        user = get_or_create_user(username, db_path=db_path)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao registrar login: {str(e)}")


@router.get("/users", response_model=List[UserResponse])
def get_recent_users(limit: int = Query(20, ge=1, le=100), db_path: str = DEFAULT_DB_PATH):
    """Lista usuários que efetuaram login recentemente no sistema."""
    return list_users(limit=limit, db_path=db_path)


@router.get("/me", response_model=UserResponse)
def get_user_status(username: str = Query(..., description="Nome do usuário"), db_path: str = DEFAULT_DB_PATH):
    """Verifica e atualiza o status de atividade do usuário informado."""
    clean_username = username.strip()
    if not clean_username:
        raise HTTPException(status_code=400, detail="Nome de usuário inválido.")
    user = get_or_create_user(clean_username, db_path=db_path)
    return user
