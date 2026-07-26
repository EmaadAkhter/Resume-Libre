import os

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services import auth

security = HTTPBearer()


def _verify_token(token: str) -> dict:
    """Verify a Supabase JWT and return the user dict {id, email}."""
    try:
        client = auth.get_supabase_client()
        response = client.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "id": response.user.id,
            "email": response.user.email,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify a Supabase JWT and return the user dict {id, email}."""
    return _verify_token(credentials.credentials)


def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "").lower() in ("1", "true", "yes")


async def require_user_or_demo(request: Request) -> dict:
    """Require a valid Supabase JWT, unless DEMO_MODE is enabled.

    Demo mode serves canned fixtures at zero LLM cost, so auth is skipped there.
    """
    if is_demo_mode():
        return {"id": "demo", "email": "demo@localhost", "demo": True}

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return _verify_token(auth_header.removeprefix("Bearer ").strip())


async def get_user_role(user: dict = Depends(verify_jwt)) -> dict:
    """Verify JWT and attach the user's role to the dict.

    Use this instead of verify_jwt when you need to know if the user is an admin.
    Eliminates the duplicated 3-line admin-check that was in every template route.
    """
    client = auth.get_supabase_client()
    result = (
        client.table("profiles").select("role").eq("id", user["id"]).single().execute()
    )

    role = result.data.get("role", "user") if result.data else "user"
    return {**user, "role": role}


async def require_admin(user: dict = Depends(get_user_role)) -> dict:
    """Require that the authenticated user has the 'admin' role."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
