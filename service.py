import secrets
from typing import Optional

from .models import VG90Identity


class IdentityService:
    """
    Serviço central de identidade VG90.

    Nesta primeira versão, a responsabilidade é criar
    e representar identidades. A persistência no MongoDB
    será ligada na próxima etapa.
    """

    @staticmethod
    def generate_user_id() -> str:
        """
        Gera um identificador único para o utilizador VG90.
        """
        return f"VG90-{secrets.token_hex(8).upper()}"

    @classmethod
    def create_identity(
        cls,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role: str = "user",
    ) -> VG90Identity:

        if not name or not name.strip():
            raise ValueError(
                "O nome do utilizador é obrigatório."
            )

        return VG90Identity(
            user_id=cls.generate_user_id(),
            name=name.strip(),
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
            role=role,
        )
