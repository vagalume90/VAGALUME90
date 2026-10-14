"""
VG90 Identity — Repositório de identidade.

Esta camada será responsável por guardar e consultar
a identidade VG90 no banco de dados.

Não contém credenciais nem URLs do banco.
"""

from typing import Optional

from .models import VG90Identity


class IdentityRepository:
    """
    Interface inicial para persistência das identidades VG90.

    A ligação ao MongoDB será implementada na próxima etapa.
    """

    def __init__(self):
        self._ready = False

    def save(self, identity: VG90Identity) -> VG90Identity:
        """
        Guarda uma identidade.

        Nesta primeira versão apenas valida a identidade.
        """
        if not identity.user_id:
            raise ValueError(
                "A identidade precisa de um user_id."
            )

        if not identity.name:
            raise ValueError(
                "A identidade precisa de um nome."
            )

        return identity

    def find_by_id(
        self,
        user_id: str,
    ) -> Optional[VG90Identity]:
        """
        Procura uma identidade pelo seu VG90 ID.

        Será ligado ao MongoDB posteriormente.
        """
        if not user_id:
            return None

        return None
