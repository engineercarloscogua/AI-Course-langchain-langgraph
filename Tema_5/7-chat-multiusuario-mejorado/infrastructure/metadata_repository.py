"""Repositorio SQLite de usuarios y metadatos de conversaciones.

Los mensajes no se duplican en esta base: LangGraph ya los conserva en sus
checkpoints. Aquí solo guardamos aquello que la interfaz necesita para listar
usuarios y chats con rapidez.
"""

from pathlib import Path
import sqlite3
from threading import RLock
from uuid import uuid4

from domain.models import (
    Chat,
    ResourceNotFoundError,
    User,
    ValidationError,
    utc_now_iso,
)


class SQLiteMetadataRepository:
    """Implementa usuarios y chats sobre una conexión SQLite compartida."""

    def __init__(self, database_path: Path | str):
        # 1. ``check_same_thread=False`` es necesario porque Streamlit puede
        # volver a ejecutar la página desde hilos distintos. El RLock protege
        # cada transacción para que una conexión no se use simultáneamente.
        self._connection = sqlite3.connect(
            str(database_path),
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._lock = RLock()
        self._setup()

    def _setup(self) -> None:
        """Crea tablas e índices de manera idempotente."""

        with self._lock, self._connection:
            # WAL mejora la convivencia entre lecturas y escrituras. Las claves
            # foráneas impiden conservar chats cuyo usuario fue eliminado.
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chats (
                    chat_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    turn_count INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chats_user_updated
                ON chats(user_id, updated_at DESC);
                """
            )

    @staticmethod
    def _user_from_row(row: sqlite3.Row) -> User:
        return User(
            user_id=row["user_id"],
            display_name=row["display_name"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _chat_from_row(row: sqlite3.Row) -> Chat:
        return Chat(
            chat_id=row["chat_id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            turn_count=row["turn_count"],
        )

    def ensure_default_user(self) -> User:
        """Devuelve el primer usuario o crea uno para el primer arranque."""

        users = self.list_users()
        if users:
            return users[0]
        return self.create_user("Usuario principal")

    def create_user(self, display_name: str) -> User:
        """Crea un usuario con ID interno impredecible y nombre visible."""

        clean_name = " ".join(display_name.split())
        if not clean_name:
            raise ValidationError("El nombre del usuario no puede estar vacío.")
        if len(clean_name) > 80:
            raise ValidationError("El nombre del usuario no puede superar 80 caracteres.")

        user = User(
            user_id=uuid4().hex,
            display_name=clean_name,
            created_at=utc_now_iso(),
        )
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO users(user_id, display_name, created_at) VALUES (?, ?, ?)",
                (user.user_id, user.display_name, user.created_at),
            )
        return user

    def list_users(self) -> list[User]:
        """Lista los usuarios por fecha de creación."""

        with self._lock:
            rows = self._connection.execute(
                "SELECT user_id, display_name, created_at "
                "FROM users ORDER BY created_at, display_name"
            ).fetchall()
        return [self._user_from_row(row) for row in rows]

    def get_user(self, user_id: str) -> User | None:
        """Busca un usuario por su ID interno."""

        with self._lock:
            row = self._connection.execute(
                "SELECT user_id, display_name, created_at FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return self._user_from_row(row) if row else None

    def create_chat(self, user_id: str) -> Chat:
        """Crea una conversación vacía que pertenezca al usuario."""

        if self.get_user(user_id) is None:
            raise ResourceNotFoundError("El usuario seleccionado no existe.")

        timestamp = utc_now_iso()
        chat = Chat(
            chat_id=uuid4().hex,
            user_id=user_id,
            title="Nueva conversación",
            created_at=timestamp,
            updated_at=timestamp,
            turn_count=0,
        )
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO chats(
                    chat_id, user_id, title, created_at, updated_at, turn_count
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chat.chat_id,
                    chat.user_id,
                    chat.title,
                    chat.created_at,
                    chat.updated_at,
                    chat.turn_count,
                ),
            )
        return chat

    def list_chats(self, user_id: str) -> list[Chat]:
        """Lista primero la conversación usada más recientemente."""

        with self._lock:
            rows = self._connection.execute(
                """
                SELECT chat_id, user_id, title, created_at, updated_at, turn_count
                FROM chats WHERE user_id = ? ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._chat_from_row(row) for row in rows]

    def get_chat(self, user_id: str, chat_id: str) -> Chat | None:
        """Busca un chat comprobando al mismo tiempo quién es su dueño."""

        with self._lock:
            row = self._connection.execute(
                """
                SELECT chat_id, user_id, title, created_at, updated_at, turn_count
                FROM chats WHERE user_id = ? AND chat_id = ?
                """,
                (user_id, chat_id),
            ).fetchone()
        return self._chat_from_row(row) if row else None

    def record_turn(self, user_id: str, chat_id: str, first_message: str) -> Chat:
        """Incrementa el contador y crea un título local en el primer turno."""

        chat = self.get_chat(user_id, chat_id)
        if chat is None:
            raise ResourceNotFoundError("La conversación seleccionada no existe.")

        # Generar el título localmente ahorra una llamada al LLM. Es suficiente
        # para una lista de chats y hace que la interfaz responda más rápido.
        clean_message = " ".join(first_message.split())
        title = chat.title
        if chat.turn_count == 0:
            title = clean_message[:47] + ("…" if len(clean_message) > 47 else "")

        updated_at = utc_now_iso()
        with self._lock, self._connection:
            self._connection.execute(
                """
                UPDATE chats
                SET title = ?, updated_at = ?, turn_count = turn_count + 1
                WHERE user_id = ? AND chat_id = ?
                """,
                (title, updated_at, user_id, chat_id),
            )

        updated_chat = self.get_chat(user_id, chat_id)
        if updated_chat is None:  # Defensa ante una eliminación concurrente.
            raise ResourceNotFoundError("La conversación dejó de existir.")
        return updated_chat

    def delete_chat(self, user_id: str, chat_id: str) -> bool:
        """Elimina solo el chat que pertenece al usuario indicado."""

        with self._lock, self._connection:
            cursor = self._connection.execute(
                "DELETE FROM chats WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
            )
        return cursor.rowcount > 0

    def close(self) -> None:
        """Cierra la conexión; es útil en tests y procesos de consola."""

        with self._lock:
            self._connection.close()
