# =============================================================================
# motor/horas.py
# -----------------------------------------------------------------------------
# Conversión entre horas en texto ("HH:MM") y minutos desde la medianoche.
#
# ¿Por qué convertir a minutos?
#   - Comparar dos enteros es más rápido y más simple que comparar textos.
#   - Con enteros podemos hacer búsqueda binaria sobre los horarios (R4).
#   - "07:05" -> 7 * 60 + 5 = 425.
#
# Complejidad: ambas funciones son O(1) (el texto siempre tiene ~5 caracteres).
# =============================================================================


# Tabla con los enteros 0..2879 (dos días de minutos). Devolver SIEMPRE el
# mismo objeto entero para el mismo minuto ahorra memoria: con 2.5 millones de
# horarios, en vez de 2.5 millones de enteros distintos hay solo 2.880.
_MINUTOS = list(range(48 * 60))


def a_minutos(hora):
    """Convierte "HH:MM" en minutos desde la medianoche. Ej: "07:05" -> 425."""
    # 1. Quitamos espacios accidentales al principio o al final.
    texto = hora.strip()
    # 2. Partimos el texto por los dos puntos: "07:05" -> ["07", "05"].
    partes = texto.split(":")
    # 3. Si no quedan exactamente dos partes, el formato es inválido.
    if len(partes) != 2:
        raise ValueError("Hora inválida, se esperaba HH:MM: " + str(hora))
    # 4. int() convierte cada parte en número (lanza ValueError si no lo es).
    horas = int(partes[0])
    minutos = int(partes[1])
    # 5. Validamos rangos. Aceptamos horas >= 24 porque el GTFS las usa
    #    (por ejemplo 25:10 = 1:10 a.m. del día siguiente). La conversión
    #    decide qué hacer con ellas; el motor solo no se rompe.
    if horas < 0 or minutos < 0 or minutos > 59:
        raise ValueError("Hora fuera de rango: " + str(hora))
    # 6. Fórmula: horas * 60 + minutos (reusando el entero de la tabla).
    total = horas * 60 + minutos
    if total < len(_MINUTOS):
        return _MINUTOS[total]
    return total


def a_texto(minutos):
    """Convierte minutos desde la medianoche en "HH:MM". Ej: 425 -> "07:05"."""
    # // es división entera (cuántas horas completas) y % es el residuo
    # (cuántos minutos sobran). :02d rellena con cero a la izquierda.
    return f"{minutos // 60:02d}:{minutos % 60:02d}"
