"""Template tags para paginacion con ventana (numerica + elipsis)."""

from django import template

register = template.Library()


@register.simple_tag
def pagination_window(page_obj, window=2):
    """Genera lista de paginas a mostrar con elipsis.

    Retorna una lista de enteros (paginas reales) y la cadena '...'
    para paginas omitidas. Ejemplo con window=2 en pagina 5 de 20:
        [1, '...', 3, 4, 5, 6, 7, '...', 20]
    """
    paginator = page_obj.paginator
    current = page_obj.number
    total = paginator.num_pages

    if total <= 1:
        return []

    # Siempre mostrar primera y ultima pagina
    pages = {1, total}

    # Paginas alrededor de la actual
    for i in range(current - window, current + window + 1):
        if 1 <= i <= total:
            pages.add(i)

    # Construir lista ordenada con elipsis
    result = []
    last = 0
    for p in sorted(pages):
        if p - last > 1:
            result.append("...")
        result.append(p)
        last = p
    return result
