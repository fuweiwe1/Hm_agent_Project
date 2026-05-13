from dataclasses import dataclass
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt as jose_jwt

from schemas.app_models import AuthenticatedUser, UserContext
from utils.config_handler import auth_conf


bearer_scheme = HTTPBearer(auto_error=False)


class JWTValidationError(ValueError):
    pass


@dataclass(frozen=True)
class JWTSettings:
    secret: str
    algorithms: tuple[str, ...]
    issuer: str | None
    audience: str | None
    user_id_claim: str
    city_claim: str
    tenant_id_claim: str
    roles_claim: str
    clock_skew_seconds: int


def get_jwt_settings() -> JWTSettings:
    raw_algorithms = auth_conf.get("jwt_algorithms", ["HS256"])
    if isinstance(raw_algorithms, str):
        raw_algorithms = [item.strip() for item in raw_algorithms.split(",") if item.strip()]

    secret = str(auth_conf.get("jwt_secret", "")).strip()
    if not secret:
        raise RuntimeError("JWT secret is not configured. Set APP_JWT_SECRET or config/auth.local.yml.")

    return JWTSettings(
        secret=secret,
        algorithms=tuple(raw_algorithms or ["HS256"]),
        issuer=str(auth_conf.get("jwt_issuer", "")).strip() or None,
        audience=str(auth_conf.get("jwt_audience", "")).strip() or None,
        user_id_claim=str(auth_conf.get("user_id_claim", "user_id")),
        city_claim=str(auth_conf.get("city_claim", "city")),
        tenant_id_claim=str(auth_conf.get("tenant_id_claim", "tenant_id")),
        roles_claim=str(auth_conf.get("roles_claim", "roles")),
        clock_skew_seconds=int(auth_conf.get("clock_skew_seconds", 30)),
    )


def create_signed_jwt(claims: dict[str, Any], secret: str, algorithm: str = "HS256") -> str:
    return jose_jwt.encode(claims, secret, algorithm=algorithm)


def decode_and_validate_jwt(token: str, settings: JWTSettings | None = None) -> dict[str, Any]:
    settings = settings or get_jwt_settings()
    try:
        return jose_jwt.decode(
            token,
            settings.secret,
            algorithms=list(settings.algorithms),
            issuer=settings.issuer,
            audience=settings.audience,
            options={"leeway": settings.clock_skew_seconds},
        )
    except JWTError as exc:
        raise JWTValidationError(str(exc)) from exc


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        settings = get_jwt_settings()
        claims = decode_and_validate_jwt(credentials.credentials, settings)
        user_id = _require_str_claim(claims, settings.user_id_claim)
        city = _require_str_claim(claims, settings.city_claim)
        tenant_id = _optional_str_claim(claims, settings.tenant_id_claim)
        roles = _normalize_roles(claims.get(settings.roles_claim))
        subject = _optional_str_claim(claims, "sub")
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except JWTValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AuthenticatedUser(
        user_id=user_id,
        city=city,
        tenant_id=tenant_id,
        roles=roles,
        token_subject=subject,
    )


def get_user_context(current_user: AuthenticatedUser = Depends(get_authenticated_user)) -> UserContext:
    return current_user.to_user_context()


def ensure_current_user_access(target_user_id: str, current_user: AuthenticatedUser) -> None:
    if target_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user cannot access another user's data.",
        )


def _require_str_claim(claims: dict[str, Any], claim_name: str) -> str:
    value = claims.get(claim_name)
    if not isinstance(value, str) or not value.strip():
        raise JWTValidationError(f"Missing required JWT claim: {claim_name}.")
    return value.strip()


def _optional_str_claim(claims: dict[str, Any], claim_name: str) -> str | None:
    value = claims.get(claim_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise JWTValidationError(f"JWT claim {claim_name} must be a string.")
    return value.strip() or None


def _normalize_roles(raw_roles: Any) -> list[str]:
    if raw_roles is None:
        return []
    if isinstance(raw_roles, str):
        return [raw_roles] if raw_roles else []
    if isinstance(raw_roles, list) and all(isinstance(role, str) for role in raw_roles):
        return raw_roles
    raise JWTValidationError("JWT roles claim must be a string or list of strings.")
