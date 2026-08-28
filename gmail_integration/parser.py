"""Parser de correos de Bancolombia.

Detecta y extrae la informacion relevante de un correo enviado por
Bancolombia notificando un movimiento. El parser es MODULAR:
- `parsear(correo)` devuelve un `MovimientoParseado` o `None` si no
  se reconoce el formato.

Para agregar nuevos formatos, registre nuevos parsers en
`PARSERS_REGISTRADOS`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

@dataclass
class MovimientoParseado:
    """Datos extraidos de un correo de Bancolombia."""

    tipo: str  # INGRESO o EGRESO
    valor: Decimal
    fecha: datetime
    concepto: str = ""
    referencia: str = ""
    cuenta: str = ""
    cuenta_destino: str = ""
    tercero: str = ""
    hora: Optional["time"] = None
    saldo_despues: Optional[Decimal] = None
    parser_usado: str = ""

    def to_dict(self) -> dict:
        """Convierte a dict serializable JSON."""
        return {
            "tipo": self.tipo,
            "valor": str(self.valor) if self.valor is not None else None,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "concepto": self.concepto,
            "referencia": self.referencia,
            "cuenta": self.cuenta,
            "cuenta_destino": self.cuenta_destino,
            "tercero": self.tercero,
            "hora": self.hora.isoformat() if self.hora else None,
            "saldo_despues": str(self.saldo_despues) if self.saldo_despues is not None else None,
            "parser_usado": self.parser_usado,
        }

# --- Utilidades --------------------------------------------------------------

def _to_decimal(texto: str) -> Optional[Decimal]:
    """Convierte un texto con formato monetario colombiano a Decimal.

    Reglas (formato colombiano):
    - "1,360,000"   -> comas son separador de miles -> 1360000
    - "1.360.000"   -> puntos son separador de miles -> 1360000
    - "1.234.567,89"-> coma decimal, puntos miles -> 1234567.89
    - "1,234,567.89"-> punto decimal, comas miles -> 1234567.89
    - "75.500"      -> sin coma, todos los segmentos 3 digitos -> 75500
    - "75.50"       -> sin coma, "50" no son 3 digitos -> decimal -> 75.50
    - "1.5"         -> decimal -> 1.5
    - "100"         -> entero -> 100
    """
    if texto is None:
        return None
    limpio = re.sub(r"[^\d,.\-]", "", texto)
    if not limpio:
        return None

    if "," in limpio and "." in limpio:
        # Ambos separadores presentes.
        # En Colombia, la coma es mas comun como separador decimal (formato "X.XXX,XX"),
        # pero tambien se ve el opuesto (formato US "X,XXX.XX").
        # El ultimo separador en aparecer suele ser el decimal.
        last_comma = limpio.rfind(",")
        last_dot = limpio.rfind(".")
        if last_dot > last_comma:
            # El punto aparece despues -> probablemente decimal
            # Eliminar comas (separadores de miles) y dejar el punto decimal
            limpio = limpio.replace(",", "")
        else:
            # La coma aparece despues -> probablemente decimal
            # Eliminar puntos (separadores de miles) y reemplazar coma por punto
            limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        # Solo comas. Decidir si es decimal o miles.
        # Si hay UNA sola coma y despues hay exactamente 2 digitos, es decimal
        # estilo "75,50" -> 75.50. Si hay multiples comas, son separadores de miles.
        partes = limpio.split(",")
        if len(partes) == 2 and len(partes[1]) == 2:
            # Decimal: "75,50" -> 75.50
            limpio = limpio.replace(",", ".")
        else:
            # Separadores de miles: "1,360,000" -> 1360000
            limpio = limpio.replace(",", "")
    elif "." in limpio:
        # Solo puntos. Decidir si son separador de miles o decimal.
        partes = limpio.split(".")
        if len(partes) == 2 and len(partes[1]) != 3:
            # Un solo punto y la parte decimal NO tiene 3 digitos
            # -> es decimal (ej "75.50", "1.5", "100.5")
            # Dejar como esta
            pass
        elif all(len(p) == 3 for p in partes[1:]):
            # Todos los segmentos tienen 3 digitos -> separador de miles
            # Ej "1.500" -> 1500, "1.234.567" -> 1234567
            limpio = limpio.replace(".", "")
        else:
            # Caso ambiguo: dejar como esta (probablemente decimal)
            pass

    try:
        return Decimal(limpio)
    except Exception:
        return None

def _normalizar_valor(texto: str) -> Optional[Decimal]:
    """Quita simbolos de moneda y separadores."""
    if texto is None:
        return None
    texto = texto.replace("\xa0", " ").strip()
    return _to_decimal(texto)

def _parsear_fecha(texto: str) -> Optional[datetime]:
    """Intenta varios formatos comunes en correos colombianos."""
    if not texto:
        return None
    texto = texto.strip()
    formatos = (
        "%d/%m/%Y",       # 03/08/2026
        "%d-%m-%Y",       # 03-08-2026
        "%Y-%m-%d",       # 2026-08-03 (ISO)
        "%Y/%m/%d",       # 2026/08/03 (Bancolombia)
        "%d/%m/%y",       # 03/08/26 (corto)
        "%d-%m-%y",       # 03-08-26 (corto)
        "%d de %B de %Y",  # 3 de agosto de 2026
        "%d %B %Y",        # 3 agosto 2026
    )
    meses_es = {
        "enero": "January", "febrero": "February", "marzo": "March",
        "abril": "April", "mayo": "May", "junio": "June",
        "julio": "July", "agosto": "August", "septiembre": "September",
        "setiembre": "September", "octubre": "October", "noviembre": "November",
        "diciembre": "December",
    }
    texto_norm = texto.lower()
    for es, en in meses_es.items():
        texto_norm = texto_norm.replace(es, en)
    for fmt in formatos:
        try:
            return datetime.strptime(texto_norm, fmt)
        except ValueError:
            continue
    return None


def _parsear_hora(texto: str) -> Optional["time"]:
    """Extrae una hora en formato HH:MM o HH:MM:SS de un texto."""
    if not texto:
        return None
    from datetime import time as time_cls
    # Buscar HH:MM o HH:MM:SS
    m = re.search(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b", texto)
    if not m:
        return None
    try:
        h = int(m.group(1))
        mi = int(m.group(2))
        s = int(m.group(3)) if m.group(3) else 0
        if 0 <= h < 24 and 0 <= mi < 60:
            return time_cls(h, mi, s)
    except (ValueError, TypeError):
        return None
    return None

def es_correo_bancolombia(remitente: str, asunto: str = "") -> bool:
    """Verifica si un correo parece provenir de Bancolombia."""
    remitente = (remitente or "").lower()
    # Dominios comunes observados en correos de notificacion de Bancolombia:
    # - bancolombia.com
    # - alertasbancolombia.com.co
    # - notificaciones@bancolombia.com
    # - alertasynotificaciones@an.notificacionesbancolombia.com
    # - cualquier subdominio que contenga la palabra bancolombia
    dominios_clave = [
        "bancolombia",                 # cubre bancolombia.com.co, bancolombia.com, etc.
        "alertasbancolombia",
        "notificacionesbancolombia",
        "notificacionesbancarias",
        "alertasynotificaciones",
    ]
    if any(d in remitente for d in dominios_clave):
        return True
    asunto_l = (asunto or "").lower()
    if "bancolombia" in asunto_l and any(
        k in asunto_l for k in [
            "movimiento", "transacci", "compra", "pago",
            "transfer", "consign", "debito", "débito", "abono",
            "retiro", "notificac",
        ]
    ):
        return True
    return False

# --- Parsers individuales ----------------------------------------------------

def _parsear_formato_estandar(texto: str) -> Optional[MovimientoParseado]:
    """Parser generico basado en patrones comunes de Bancolombia."""
    texto_lower = texto.lower()

    # Detectar tipo con prioridad: egreso si hay palabras fuertes
    # Las keywords "fuertes" son especificas y rara vez aparecen en otro contexto.
    tipo = None

    ingreso_fuerte = [
        "transferencia recibida", "consignacion", "consignación",
        "recibiste una transferencia", "te fue acreditado",
        "le fue acreditado", "le fue consignado",
        "fue abonada", "dinero recibido",
    ]
    egreso_fuerte = [
        "transferencia enviada", "transferiste ", "transferiste$",
        "pago realizado", "pagas", "pagaste", "se debito", "se debitó",
        "te cobraron", "desembolso", "compra pse", "retiro de cajero",
        "pse ", "pago a ", "pagó",
    ]
    ingreso_debil = [
        "abono", "deposito", "depósito", "recibiste", "te enviaron",
        "recibio", "recibió", "ingreso", "ingresó", "acreditacion",
        "acreditación", "movimiento entrante", "consignacion",
        "consignación", "recibiste una transferencia",
    ]
    egreso_debil = [
        "debito", "débito", "retiro", "pago", "compra", "compras",
        "transaccion", "transacción", "consumo",
        "transferencia exitosa", "salida de dinero", "pagaste",
        "pagas", "pagó", "cobro", "cobros", "factura", "facturas",
        "compra pse", "compra realizada", "transferiste",
    ]

    # Primero: palabras fuertes (mas especificas)
    tiene_ingreso_fuerte = any(k in texto_lower for k in ingreso_fuerte)
    tiene_egreso_fuerte = any(k in texto_lower for k in egreso_fuerte)

    if tiene_egreso_fuerte and not tiene_ingreso_fuerte:
        tipo = "EGRESO"
    elif tiene_ingreso_fuerte and not tiene_egreso_fuerte:
        tipo = "INGRESO"
    elif tiene_egreso_fuerte and tiene_ingreso_fuerte:
        # Conflicto. Decidir por contexto mas fuerte.
        # Si hay "transferiste", "pago realizado", es casi seguro EGRESO
        tipo = "EGRESO"
    else:
        # Sin palabras fuertes: contar coincidencias debiles
        ingresos_score = sum(1 for k in ingreso_debil if k in texto_lower)
        egresos_score = sum(1 for k in egreso_debil if k in texto_lower)
        if ingresos_score > egresos_score:
            tipo = "INGRESO"
        elif egresos_score > ingresos_score:
            tipo = "EGRESO"
        else:
            return None

    if tipo is None:
        return None

    # Valor: signo negativo si egreso. Acepta con o sin $ al inicio.
    # Patron 1: con $ -> "$1.500,00"
    # Patron 2: sin $ pero precedido por palabra clave -> "por 1.500,00", "transferiste 1.500,00"
    KEYWORDS_VALOR = (
        r"(?:por\s+|transferiste\s+|transfirio\s+|recibiste\s+|"
        r"pagaste\s+|pagas\s+|pagó\s+|"
        r"transferencia\s+(?:de\s+|por\s+)?|"
        r"pago\s+(?:de\s+|por\s+)?|"
        r"compra\s+(?:de\s+|por\s+)?|"
        r"consignacion\s+(?:de\s+|por\s+)?|"
        r"consignación\s+(?:de\s+|por\s+)?|"
        r"abono\s+(?:de\s+|por\s+)?|"
        r"retiro\s+(?:de\s+|por\s+)?|"
        r"debito\s+(?:de\s+|por\s+)?|"
        r"débito\s+(?:de\s+|por\s+)?|"
        r"valor\s+(?:de\s+)?|"
        r"monto\s+(?:de\s+)?|"
        r"total\s+(?:de\s+)?|"
        r"pse\s+)"
    )
    patron_con_dolar = r"\$\s*([\d]+(?:[.,][\d]+)*)"
    patron_sin_dolar = KEYWORDS_VALOR + r"([\d]+(?:[.,][\d]+)*)"
    candidatos = []
    # Primero buscar con $ (mas confiable)
    for match in re.finditer(patron_con_dolar, texto):
        texto_valor = match.group(1)
        if not texto_valor:
            continue
        valor = _normalizar_valor(texto_valor)
        if valor is None or valor <= 0:
            continue
        contexto = texto_lower[max(0, match.start() - 40):match.start()]
        if any(k in contexto for k in [
            "valor", "monto", "total", "por ", "transferencia", "transferiste",
            "transfirio", "transfirió", "pago", "pagas", "pagaste", "pagó",
            "transferiste", "transfirió", "transferencia", "transferiste",
            "compra", "consignacion", "consignación", "abono", "retiro",
            "$", "transaccion", "transacción", "consumo", "debito",
            "débito", "pesos", "cop", "qr", "movimiento",
        ]):
            candidatos.append((match.start(), valor))

    # Si no hay con $, buscar sin $ pero con palabra clave antes
    if not candidatos:
        for match in re.finditer(patron_sin_dolar, texto_lower):
            texto_valor = match.group(1)
            if not texto_valor:
                continue
            valor = _normalizar_valor(texto_valor)
            if valor is None or valor <= 0:
                continue
            candidatos.append((match.start(), valor))

    if not candidatos:
        return None
    _, valor = candidatos[0]

    # Fecha: buscar cerca del valor para evitar capturar fechas de URLs/logos
    fecha = None
    # Quitar URLs de todo el texto (mejor para fecha y hora)
    texto_sin_urls = re.sub(r'https?://\S+', '', texto_lower)

    if valor is not None:
        # Buscar fecha cerca del valor
        idx_valor = texto_sin_urls.find(str(valor).replace(",", ".").replace(".", "").split("0")[0] if valor else "")
        # Buscar fecha dentro de los 200 caracteres DESPUES del valor
        ventana = texto_sin_urls[max(0, idx_valor):idx_valor + 200] if idx_valor >= 0 else texto_sin_urls
        for patron in [
            r"(\d{1,2}/\d{1,2}/\d{4})",     # DD/MM/YYYY
            r"(\d{4}/\d{1,2}/\d{1,2})",     # YYYY/MM/DD
            r"(\d{1,2}-\d{1,2}-\d{4})",     # DD-MM-YYYY
            r"(\d{1,2}/\d{1,2}/\d{2})",     # DD/MM/YY (corto)
            r"(\d{1,2}-\d{1,2}-\d{2})",     # DD-MM-YY (corto)
        ]:
            m = re.search(patron, ventana)
            if m:
                fecha = _parsear_fecha(m.group(1))
                if fecha:
                    break

    # Si no encontramos cerca del valor, buscar en todo el texto
    if fecha is None:
        for patron in [
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{4}/\d{1,2}/\d{1,2})",
            r"(\d{1,2}-\d{1,2}-\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{1,2}/\d{1,2}/\d{2})",
            r"(\d{1,2}-\d{1,2}-\d{2})",
        ]:
            m = re.search(patron, texto_sin_urls)
            if m:
                fecha = _parsear_fecha(m.group(1))
                if fecha:
                    break

    # Extraer hora: buscar cerca de la fecha
    hora = None
    if fecha is not None:
        # Buscar la fecha en texto_sin_urls y extraer hora cerca
        fecha_str = fecha.strftime("%d/%m/%Y")
        idx_fecha = texto_sin_urls.find(fecha_str)
        if idx_fecha >= 0:
            ventana_hora = texto_sin_urls[idx_fecha:idx_fecha + 100]
        else:
            ventana_hora = texto_sin_urls
        m_hora = re.search(
            r"(?:a las?)?\s*(\d{1,2}:\d{2}(?::\d{2})?)",
            ventana_hora,
        )
        if m_hora:
            hora = _parsear_hora(m_hora.group(1))

    if fecha is None:
        return None

    # Concepto: linea posterior al tipo
    concepto = ""
    m_concepto = re.search(
        r"(?:concepto|descripci[oó]n|motivo)\s*[:\-]?\s*(.+?)(?:\n|$)",
        texto, re.IGNORECASE,
    )
    if m_concepto:
        concepto = m_concepto.group(1).strip()[:200]
    if not concepto:
        # buscar despues de "transferencia" o "transferiste"
        m_concepto2 = re.search(
            r"(?:transferencia|transferiste|consignaci[oó]n|pago|compra|recibiste)\s+"
            r"(?:de\s+|por\s+)?\$?[\d.,]+",
            texto, re.IGNORECASE,
        )
        if m_concepto2:
            concepto = m_concepto2.group(0).strip()[:200]
    if not concepto:
        # Capturar la linea completa que tiene el valor como concepto
        m_linea = re.search(
            r"(?:transferiste|transferencia|consignacion|consignación|pago|compra|recibiste)\s+\$?[\d.,]+[^.\n]{0,100}",
            texto, re.IGNORECASE,
        )
        if m_linea:
            concepto = m_linea.group(0).strip()[:200]

    # Permitir concepto vacio (no retornar None solo por esto)
    concepto = concepto.strip()

    # Referencia (opcional)
    referencia = ""
    PALABRAS_INVALIDAS_REF = {
        "errer", "error", "none", "null", "n/a", "sindatos", "vacio",
        "transferencia", "transferencias", "compra", "compras", "pagos", "pago",
    }
    m_ref = re.search(
        r"(?:referencia|ref\.?|aprobado|aprobaci[oó]n|comprobante|n[úu]mero de operaci[óo]n)\s*[:\-]?\s*([A-Z0-9\-]{6,})",
        texto,
        re.IGNORECASE,
    )
    if m_ref:
        candidato = m_ref.group(1).strip()[:120]
        if candidato.lower() not in PALABRAS_INVALIDAS_REF and not candidato.lower().startswith("transfer"):
            referencia = candidato

    # Tercero
    tercero = ""
    # Patron 1: ingresos "$X de NOMBRE en tu cuenta"
    m_tercero_ingreso = re.search(
        r"\$\s*[\d.,]+\s+de\s+([A-Z][A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,80}?)\s+en tu cuenta",
        texto,
    )
    if m_tercero_ingreso:
        tercero = m_tercero_ingreso.group(1).strip()[:200]
    else:
        # Patron 1b: ingresos variante "Recibiste una transferencia de NOMBRE"
        m_tercero_ingreso2 = re.search(
            r"(?:transferencia|consignaci[oó]n|transferiste|pago)\s+(?:de|por)\s+\$?[\d.,]+\s+de\s+"
            r"([A-Z][A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,80}?)"
            r"(?:\s+en\s+tu|\s+por|\s+hoy|\s+ayer|\s+el|\.|\n|$)",
            texto,
            re.IGNORECASE,
        )
        if m_tercero_ingreso2:
            candidato = m_tercero_ingreso2.group(1).strip()
            palabras_invalidas = {
                "tu", "tuya", "el", "la", "los", "las", "un", "una", "bancolombia",
                "transferencia", "transferiste", "este", "esta", "estos",
            }
            if candidato.lower().split()[0] not in palabras_invalidas:
                tercero = candidato[:200]

        if not tercero:
            # Patron 2: generico "a NOMBRE" o "de NOMBRE" (egresos a personas)
            m_tercero = re.search(
                r"(?:a|de|desde|para)\s+([A-Z][A-Za-zÁÉÍÓÚáéíóúÑñ ]{2,80}?)"
                r"(?:\s+por|\s+el|\s+\.|\s+en tu|\s+desde tu|\s+a la|\s+al|\n|$)",
                texto,
            )
            if m_tercero:
                candidato = m_tercero.group(1).strip()
                palabras_invalidas = {
                    "tu", "tuya", "el", "la", "los", "las", "un", "una", "bancolombia",
                    "transferencia", "transferiste", "este", "esta", "estos",
                    "cuenta", "producto", "nequi", "daviplata",
                }
                primera = candidato.lower().split()[0] if candidato else ""
                if primera not in palabras_invalidas and len(candidato) >= 3:
                    tercero = candidato[:200]

    # Cuenta origen (formato: "desde tu cuenta *1234" o "de la cuenta 1234")
    cuenta = ""
    m_cta_origen = re.search(
        r"(?:desde tu cuenta|de tu cuenta|cuenta origen|producto)\s*[:\-]?\s*([\*\d]{4,})",
        texto,
        re.IGNORECASE,
    )
    if m_cta_origen:
        cuenta = m_cta_origen.group(1).strip()[:80]
    if not cuenta:
        m_cta = re.search(r"(?:cuenta|producto)\s*[:\-]?\s*([\*\d]{4,})", texto, re.IGNORECASE)
        if m_cta:
            cuenta = m_cta.group(1).strip()[:80]

    # Cuenta destino (formato: "a la cuenta *1234567", "al producto X", "para el producto X")
    cuenta_destino = ""
    # 1) Patron principal: "a la cuenta XXXX" / "al producto XXXX"
    m_cta_dest = re.search(
        r"(?:a\s+la\s+cuenta|al\s+producto|para\s+el\s+producto|a\s+la\s+cuenta)\s+([\*\d]{4,})",
        texto,
        re.IGNORECASE,
    )
    if m_cta_dest:
        cuenta_destino = m_cta_dest.group(1).strip()[:80]
    if not cuenta_destino:
        # 2) Variantes: "cuenta destino", "hacia la cuenta", "para la cuenta"
        m_cta_dest2 = re.search(
            r"(?:cuenta\s+destino|hacia\s+la\s+cuenta|para\s+la\s+cuenta|al\s+cuenta)\s+"
            r"([\*\d]{4,})",
            texto,
            re.IGNORECASE,
        )
        if m_cta_dest2:
            cuenta_destino = m_cta_dest2.group(1).strip()[:80]
    if not cuenta_destino:
        # 3) Formato "transferiste a cuenta XXXX" sin "la"
        m_cta_dest3 = re.search(
            r"\btransferist[ae]\s+(?:a|por)\s+cuenta\s+([\*\d]{4,})",
            texto,
            re.IGNORECASE,
        )
        if m_cta_dest3:
            cuenta_destino = m_cta_dest3.group(1).strip()[:80]
    if not cuenta_destino:
        # 4) QR / Nequi / DaviPlata "a la cuenta 8615" sin asterisco
        m_cta_dest4 = re.search(
            r"\b(?:a|para|hacia)\s+cuenta\s+([\d]{4,})",
            texto,
            re.IGNORECASE,
        )
        if m_cta_dest4:
            cuenta_destino = m_cta_dest4.group(1).strip()[:80]

    # Saldo despues
    saldo_despues = None
    m_saldo = re.search(r"saldo\s+(?:actual|disponible|final|total)\s*[:\-]?\s*\$?\s*([\d.,]+)", texto, re.IGNORECASE)
    if m_saldo:
        saldo_despues = _normalizar_valor(m_saldo.group(1))

    try:
        resultado = MovimientoParseado(
            tipo=tipo,
            valor=valor,
            fecha=fecha,
            concepto=concepto,
            referencia=referencia,
            cuenta=cuenta,
            cuenta_destino=cuenta_destino,
            tercero=tercero,
            hora=hora,
            saldo_despues=saldo_despues,
            parser_usado="estandar",
        )
        return resultado
    except Exception:
        return None

# Registro de parsers (extensible)
PARSERS_REGISTRADOS = [_parsear_formato_estandar]

def parsear(remitente: str, asunto: str, cuerpo: str) -> Optional[MovimientoParseado]:
    """Intenta parsear un correo. Devuelve None si no reconoce el formato."""
    if not es_correo_bancolombia(remitente, asunto):
        return None
    texto_completo = f"{asunto or ''}\n\n{cuerpo or ''}"
    for parser in PARSERS_REGISTRADOS:
        try:
            resultado = parser(texto_completo)
        except Exception:
            continue
        if resultado is not None:
            return resultado
    return None
