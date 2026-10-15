"""
VG90 Identity — Serviço central de identidade.
"""

from typing import Optional

from .models import VG90Identity


class IdentityService:
    """
    Regras relacionadas à identidade VG90.
    """

    @staticmethod
    def create_identity(
        uid: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        role: str = "user",
        status: str = "active",
    ) -> VG90Identity:

        if not uid or not uid.strip():
            raise ValueError(
                "O VG90 UID é obrigatório."
            )

        if not name or not name.strip():
            raise ValueError(
                "O nome do utilizador é obrigatório."
            )

        return VG90Identity(
            uid=uid.strip(),
            name=name.strip(),
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
            role=role,
            status=status,
        )
