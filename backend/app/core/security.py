from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.core.config import get_settings
from backend.app.models.schemas import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scopes={
        "meeting:run": "Run meeting intelligence",
        "research:run": "Run investor research",
        "crm:sync": "Prepare or sync CRM payloads",
        "admin:config": "Manage configuration",
    },
)

DEMO_USERS = {
    "analyst": {
        "username": "analyst",
        "full_name": "Analyst Demo User",
        "hashed_password": pwd_context.hash("indago-demo"),
        "scopes": ["meeting:run", "research:run", "crm:sync"],
    },
    "admin": {
        "username": "admin",
        "full_name": "IRIP Admin",
        "hashed_password": pwd_context.hash("indago-admin"),
        "scopes": ["meeting:run", "research:run", "crm:sync", "admin:config"],
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str) -> User | None:
    record = DEMO_USERS.get(username)
    if not record or not verify_password(password, record["hashed_password"]):
        return None
    return User(username=record["username"], full_name=record["full_name"], scopes=record["scopes"])


def create_access_token(subject: str, scopes: list[str]) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "scopes": scopes, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


async def get_current_user(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
) -> User:
    settings = get_settings()
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        username: str | None = payload.get("sub")
        token_scopes: list[str] = payload.get("scopes", [])
        if username is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc
    record = DEMO_USERS.get(username)
    if not record:
        raise credentials_exception
    user = User(username=record["username"], full_name=record["full_name"], scopes=token_scopes)
    missing_scopes = [scope for scope in security_scopes.scopes if scope not in token_scopes]
    if missing_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing scopes: {', '.join(missing_scopes)}",
            headers={"WWW-Authenticate": authenticate_value},
        )
    return user


def require_scopes(*scopes: str):
    return Security(get_current_user, scopes=list(scopes))
