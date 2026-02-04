from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from models import User, get_async_db
from utils.jwt_handler import hash_password, verify_password, create_access_token, create_refresh_token
from datetime import datetime

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ==================== Pydantic 모델 ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str
    expires_at: datetime


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str = None


class SignupResponse(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str


# ==================== 엔드포인트 ====================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    사용자 로그인
    JWT 액세스 토큰 발급
    """
    # 사용자 조회
    result = await db.execute(
        select(User).filter(User.username == request.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 잘못되었습니다"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다"
        )
    
    # 토큰 생성
    token, expires_at = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )
    
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        expires_at=expires_at
    )


@router.post("/signup", response_model=SignupResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    신규 사용자 가입
    """
    # 중복 확인
    existing_user = await db.execute(
        select(User).filter(
            (User.username == request.username) | (User.email == request.email)
        )
    )
    
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자명 또는 이메일입니다"
        )
    
    # 새 사용자 생성
    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return SignupResponse(
        user_id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )


@router.post("/logout")
async def logout():
    """
    사용자 로그아웃
    (클라이언트에서 토큰 삭제)
    """
    return {"message": "로그아웃 완료"}


@router.post("/refresh")
async def refresh_token(request: dict):
    """
    토큰 갱신
    """
    # TODO: 리프레시 토큰으로 새 액세스 토큰 발급
    return {"message": "토큰이 갱신되었습니다"}
