"""Servicios (escritura) para movimientos.

Aqui vive la logica de negocio relacionada con crear / actualizar /
cambiar estado de movimientos. Las vistas y API consumen estos servicios.
"""

from decimal import Decimal

from django.db import transaction

from core.models import (
    EstadoConciliacion,
    OrigenMovimiento,
)
from auditoria.services import registrar_auditoria

from .models import Comprobante, Movimiento


@transaction.atomic
def crear_movimiento(form, usuario=None) -> Movimiento:
    """Crea un movimiento desde un formulario valido."""
    movimiento = form.save(commit=False)
    if movimiento.estado_conciliacion not in dict(EstadoConciliacion.choices):
        movimiento.estado_conciliacion = EstadoConciliacion.PENDIENTE
    if not movimiento.origen:
        movimiento.origen = OrigenMovimiento.MANUAL
    movimiento.creado_por = usuario
    movimiento.save()
    form.save_m2m()

    registrar_auditoria(
        usuario=usuario,
        accion="CREAR",
        movimiento=movimiento,
        datos_nuevos=_serializar(movimiento),
    )
    return movimiento


@transaction.atomic
def actualizar_movimiento(movimiento: Movimiento, form, usuario=None) -> Movimiento:
    anteriores = _serializar(movimiento)
    movimiento = form.save()
    registrar_auditoria(
        usuario=usuario,
        accion="EDITAR",
        movimiento=movimiento,
        datos_anteriores=anteriores,
        datos_nuevos=_serializar(movimiento),
    )
    return movimiento


@transaction.atomic
def eliminar_movimiento(movimiento: Movimiento, usuario=None) -> None:
    snapshot = _serializar(movimiento)
    registrar_auditoria(
        usuario=usuario,
        accion="ELIMINAR",
        movimiento=movimiento,
        datos_anteriores=snapshot,
    )
    movimiento.delete()


@transaction.atomic
def cambiar_estado_conciliacion(
    movimiento: Movimiento,
    nuevo_estado: str,
    usuario=None,
) -> Movimiento:
    if nuevo_estado not in dict(EstadoConciliacion.choices):
        raise ValueError("Estado de conciliacion invalido.")
    anterior = movimiento.estado_conciliacion
    movimiento.estado_conciliacion = nuevo_estado
    movimiento.save(update_fields=["estado_conciliacion", "actualizado_en"])
    registrar_auditoria(
        usuario=usuario,
        accion="CAMBIAR_ESTADO_CONCILIACION",
        movimiento=movimiento,
        datos_anteriores={"estado_conciliacion": anterior},
        datos_nuevos={"estado_conciliacion": nuevo_estado},
    )
    return movimiento


def _serializar(movimiento: Movimiento) -> dict:
    """Serializa los campos relevantes para auditoria."""
    return {
        "tipo": movimiento.tipo,
        "fecha": movimiento.fecha.isoformat() if movimiento.fecha else None,
        "hora": movimiento.hora.isoformat() if movimiento.hora else None,
        "valor": str(movimiento.valor),
        "concepto": movimiento.concepto,
        "descripcion": movimiento.descripcion,
        "categoria": movimiento.categoria.nombre if movimiento.categoria else None,
        "subcategoria": movimiento.subcategoria,
        "banco": movimiento.banco,
        "cuenta": movimiento.cuenta,
        "cuenta_destino": movimiento.cuenta_destino,
        "nombre_destinatario": movimiento.nombre_destinatario,
        "referencia": movimiento.referencia,
        "tercero": movimiento.tercero,
        "saldo_despues": str(movimiento.saldo_despues) if movimiento.saldo_despues is not None else None,
        "origen": movimiento.origen,
        "estado_conciliacion": movimiento.estado_conciliacion,
    }
