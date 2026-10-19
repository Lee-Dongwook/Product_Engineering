from pydantic import BaseModel, ConfigDict

from app.models.tenant import UserRole

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: UserRole
    tenant_id: int
