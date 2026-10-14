"""
VG90 Core — Configuração central.

As configurações sensíveis são obtidas através
das variáveis de ambiente do servidor.
"""

import os


class Settings:
    """
    Configurações partilhadas pelo ecossistema VG90.
    """

    APP_NAME = os.getenv(
        "VG90_APP_NAME",
        "VAGALUME90",
    )

    ENVIRONMENT = os.getenv(
        "VG90_ENVIRONMENT",
        "production",
    )

    MONGO_URI = os.getenv(
        "MONGO_URI",
    )

    PERSY_URL = os.getenv(
        "PERSY_URL",
        "https://persy-ai.onrender.com",
    )


settings = Settings()
