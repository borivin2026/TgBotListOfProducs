import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.entities import User, ShoppingList, ListItem, Receipt, ReceiptItem
from config import DB_PATH
from utils.logger import logger

class DatabaseManager:
    """Менеджер для асинхронной работы с SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def _execute(self, query: str, parameters: tuple = ()) -> None:
        """Выполнение запроса без возврата данных."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, parameters)
            await db.commit()

    async def init_db(self) -> None:
        """Создание таблиц, если они не существуют."""
        logger.info("Инициализация базы данных...")
        
        # Таблица пользователей
        await self._execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица списков покупок
        await self._execute('''
            CREATE TABLE IF NOT EXISTS shopping_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Таблица товаров в списках
        await self._execute('''
            CREATE TABLE IF NOT EXISTS list_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER,
                name TEXT NOT NULL,
                quantity TEXT DEFAULT '1',
                note TEXT,
                is_bought BOOLEAN DEFAULT 0,
                FOREIGN KEY (list_id) REFERENCES shopping_lists (id)
            )
        ''')

        # Таблица чеков
        await self._execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_sum REAL,
                receipt_date TIMESTAMP,
                raw_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        logger.info("База данных готова к работе.")

    async def upsert_user(self, user: User) -> None:
        """Добавление или обновление данных пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO users (id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
            ''', (user.id, user.username, user.full_name))
            await db.commit()

    async def get_active_list(self, user_id: int) -> Optional[ShoppingList]:
        """Получение текущего активного списка пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM shopping_lists WHERE user_id = ? AND status = 'active' LIMIT 1",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                list_id = row['id']
                items = await self._get_list_items(list_id)
                
                return ShoppingList(
                    id=list_id,
                    user_id=row['user_id'],
                    status=row['status'],
                    items=items,
                    created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
                )

    async def create_shopping_list(self, user_id: int) -> int:
        """Создание нового пустого списка и возврат его ID."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO shopping_lists (user_id, status) VALUES (?, 'active')",
                (user_id,)
            )
            list_id = cursor.lastrowid
            await db.commit()
            return list_id

    async def _get_list_items(self, list_id: int) -> List[ListItem]:
        """Вспомогательный метод для получения товаров списка."""
        items = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM list_items WHERE list_id = ?", (list_id,)) as cursor:
                async for row in cursor:
                    items.append(ListItem(
                        name=row['name'],
                        quantity=row['quantity'],
                        note=row['note'],
                        is_bought=bool(row['is_bought'])
                    ))
        return items

    async def update_list_items(self, list_id: int, items: List[ListItem]) -> None:
        """Полное обновление товаров в списке (удаление старых и запись новых)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM list_items WHERE list_id = ?", (list_id,))
            for item in items:
                await db.execute('''
                    INSERT INTO list_items (list_id, name, quantity, note, is_bought)
                    VALUES (?, ?, ?, ?, ?)
                ''', (list_id, item.name, item.quantity, item.note, int(item.is_bought)))
            await db.commit()

    async def finalize_list(self, list_id: int) -> None:
        """Завершение списка (смена статуса)."""
        await self._execute(
            "UPDATE shopping_lists SET status = 'completed' WHERE id = ?",
            (list_id,)
        )

    async def save_receipt(self, receipt: Receipt) -> None:
        """Сохранение данных о чеке."""
        await self._execute('''
            INSERT INTO receipts (user_id, total_sum, receipt_date, raw_json)
            VALUES (?, ?, ?, ?)
        ''', (receipt.user_id, receipt.total_sum, receipt.date.isoformat(), receipt.raw_json))
