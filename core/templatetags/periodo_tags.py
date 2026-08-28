"""Template tags para selectores de periodo en exports."""

from datetime import date

from django import template

from core.context_processors import MESES_ES

register = template.Library()


@register.simple_tag
def meses_disponibles(anio_seleccionado):
    """Retorna los meses disponibles para el año seleccionado.

    - Para el año actual: solo hasta el mes actual
    - Para años pasados: los 12 meses
    - Para años futuros: lista vacia (no deberia pasar)

    Uso:
        {% meses_disponibles anio_seleccionado as meses %}
        {% for m in meses %}
            <option value="{{ m.num }}">{{ m.name }}</option>
        {% endfor %}
    """
    hoy = date.today()
    if anio_seleccionado is None or anio_seleccionado == hoy.year:
        max_mes = hoy.month
    elif anio_seleccionado < hoy.year:
        max_mes = 12
    else:
        return []
    return [{"num": n, "name": name} for n, name in MESES_ES if n <= max_mes]