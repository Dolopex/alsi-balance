import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from gmail_integration.parser import parsear

texto = "Listo! Todo salio bien con tus movimientos Bancolombia: $14,088,000 de NELSON ACEVEDO en tu cuenta **0736, el 10/08/2026 a las 14:32."
resultado = parsear("alertasynotificaciones@an.notificacionesbancolombia.com", "Movimiento", texto)
if resultado:
    for k, v in resultado.to_dict().items():
        print(f"  {k}: {v}")
else:
    print("No reconocido")
