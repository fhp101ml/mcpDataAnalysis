import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class KDDSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_phase: str = "1_understanding_problem" # Fase inicial
    dataset_context: Optional[Dict[str, Any]] = None
    chat_history: list = Field(default_factory=list)

class SessionManager:
    """Gestor simple de sesiones en memoria para la Fase 1"""
    def __init__(self):
        self._sessions: Dict[str, KDDSession] = {}

    def create_session(self) -> KDDSession:
        session = KDDSession()
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[KDDSession]:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[KDDSession]:
        session = self.get_session(session_id)
        if session:
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            return session
        return None

# Instancia global para pruebas tempranas
session_manager = SessionManager()
