"""API HTTP del MVP de Fitlosophy (docs/14).

Capa fina sobre el paquete `fitlosophy` (motor, generador y modelo de carga):
persistencia en SQLite, autenticación de usuario único y endpoints del flujo
diario. Toda la lógica de decisión vive en `fitlosophy`; aquí solo hay
persistencia, serialización y orquestación.
"""

from .app import create_app

__all__ = ["create_app"]
