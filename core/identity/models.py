from dataclasses import dataclass
from typing import Optional


@dataclass
class VG90Identity:
    """
    Identidade central de um utilizador no ecossistema VG90.

    Esta identidade pertence ao ecossistema inteiro,
    não a um módulo específico.
    """

    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "user"
    status: str = "active"

    def public_data(self) -> dict:
        """
        Dados seguros para os módulos do ecossistema.
        Não expõe palavra-passe ou outros segredos.
        """
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "status": self.status,
        }
