from typing import List, Annotated
from fastapi import Header, HTTPException, status

import fastapi

async def get_user_roles(x_user_roles: Annotated[str | None, Header()] = None) -> List[str]:
    """
    Extracts user roles from X-User-Roles header.
    Expected format: "Role1,Role2,Role3"
    """
    if not x_user_roles:
        return []
    return [role.strip() for role in x_user_roles.split(",")]

def require_role(required_role: str):
    async def role_checker(roles: list[str] = fastapi.Depends(get_user_roles)):
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {required_role}"
            )
        return True
    return role_checker
