"""Middleware personalizado para ALLOWED_HOSTS y CSRF en Fly.io.

Fly.io usa IPs privadas (RFC1918: 10.x, 172.16-31.x, 192.168.x) en su red
interna. Las requests internas (health checks, load balancer) llevan
la IP de la maquina como Host header, no el hostname publico.

Este middleware agrega esas IPs a ALLOWED_HOSTS dinamicamente para
evitar errores DisallowedHost cada vez que Fly cambia la IP.
"""

import ipaddress


RFC1918_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _is_fly_internal_ip(host: str) -> bool:
    """Devuelve True si el host es una IP privada RFC1918 (red interna Fly)."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in net for net in RFC1918_NETWORKS)


class FlyInternalHostMiddleware:
    """Si el Host header es una IP privada, la agrega a ALLOWED_HOSTS en runtime.

    Corre antes que CommonMiddleware (que hace la validacion ALLOWED_HOSTS),
    asi que el cambio aplica al chequeo de Django.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings as django_settings

        host = request.get_host().split(":")[0]
        if _is_fly_internal_ip(host):
            allowed = list(django_settings.ALLOWED_HOSTS)
            if host not in allowed:
                allowed.append(host)
                django_settings.ALLOWED_HOSTS = allowed

            origins = list(django_settings.CSRF_TRUSTED_ORIGINS)
            for proto in ("http", "https"):
                candidate = f"{proto}://{host}"
                if candidate not in origins:
                    origins.append(candidate)
            django_settings.CSRF_TRUSTED_ORIGINS = origins

        return self.get_response(request)