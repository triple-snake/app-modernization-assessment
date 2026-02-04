from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_handler import verify_access_token, TokenData

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """
    현재 사용자 정보 추출 (의존성)
    """
    token = credentials.credentials
    return verify_access_token(token)


async def get_current_admin_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    현재 사용자가 관리자인지 확인
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user
