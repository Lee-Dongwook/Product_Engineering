from enum import Enum as PyEnum
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class OrderStatus(str, PyEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ORDERED = "ORDERED"

