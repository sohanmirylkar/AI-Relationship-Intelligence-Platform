from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.core.security import authenticate_user, create_access_token
from backend.app.models.schemas import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    requested_scopes = form_data.scopes or user.scopes
    allowed_scopes = [scope for scope in requested_scopes if scope in user.scopes]
    return TokenResponse(
        access_token=create_access_token(user.username, allowed_scopes),
        scopes=allowed_scopes,
    )
