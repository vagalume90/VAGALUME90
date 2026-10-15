"""
VG90 Identity — Modelo central de identidade.

A identidade VG90 utiliza o campo `uid` como identificador
público e transversal do utilizador no ecossistema.

O `_id` do MongoDB continua sendo um identificador interno.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VG90Identity:
    """
    Identidade central de um utilizador VG90.
    """

    uid: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    status: str = "active"

    def public_data(self) -> dict:
        """
        Representação segura da identidade para os módulos VG90.
        """

        return {
            "uid": self.uid,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
        }
