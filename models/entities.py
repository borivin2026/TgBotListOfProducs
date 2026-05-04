from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    """Сущность пользователя Telegram."""
    id: int
    username: Optional[str] = None
    full_name: str
    created_at: datetime = Field(default_factory=datetime.now)

class ListItem(BaseModel):
    """Сущность товара в списке покупок."""
    name: str
    quantity: str = "1"
    note: Optional[str] = None
    is_bought: bool = False

class ShoppingList(BaseModel):
    """Сущность списка покупок (сессия)."""
    id: Optional[int] = None
    user_id: int
    items: List[ListItem] = []
    status: str = "active"  # active, completed
    created_at: datetime = Field(default_factory=datetime.now)

class ReceiptItem(BaseModel):
    """Сущность товара, извлеченного из чека."""
    name: str
    price: float = 0.0
    quantity: float = 1.0
    total: float = 0.0

class Receipt(BaseModel):
    """Сущность оцифрованного чека."""
    user_id: int
    items: List[ReceiptItem]
    total_sum: float
    date: datetime
    raw_json: Optional[str] = None
