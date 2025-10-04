from .routes import stress_bp
from .sockets import StressNamespace

stress_namespace = StressNamespace('/stress')

__all__ = ['stress_bp', 'stress_namespace']
