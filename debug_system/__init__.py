"""
Système de debug ultra-rapide pour AutomaTeX.
Architecture SOLID avec comparaison de versions et détection d'erreurs avancée.
"""

from .debug_coordinator import DebugCoordinator, DebugCoordinatorFactory

__version__ = "1.0.0"
__author__ = "AutomaTeX Debug System"

__all__ = [
    "DebugCoordinator",
    "DebugCoordinatorFactory"
]