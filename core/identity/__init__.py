"""
VG90 Identity

Identidade central partilhada pelos mundos do ecossistema VG90.
"""

from .models import VG90Identity
from .service import IdentityService
from .repository import IdentityRepository

__all__ = [
    "VG90Identity",
    "IdentityService",
    "IdentityRepository",
]
