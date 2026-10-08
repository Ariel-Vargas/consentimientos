"""
concat_csv.py
-------------
Concatena todos los archivos CSV de la carpeta 'politica' en un único archivo.
Si un usuario aparece en más de un archivo, conserva únicamente el registro
con la fecha más reciente y descarta los anteriores.

Uso:
    python concat_csv.py

Salida:
    politica_concatenado.csv  (en el mismo directorio que este script)
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

# ── Configuración ─────────────────────────────────────────────────────────────
INPUT_FOLDER    = Path(__file__).with_name("politica")
OUTPUT_FILE     = Path(__file__).with_name("politica.csv")
ENCODINGS       = ["utf-8-sig", "latin-1"]  # se prueba en orden para detectar BOM
OUTPUT_ENCODING = "utf-8-sig"         # utf-8 con BOM (compatible con Excel)

COL_USUARIO = "usuario"               # columna identificador de usuario
COL_FECHA   = "fecha"                 # columna de fecha
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"     # formato de la columna de fecha

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_fecha(valor: str) -> datetime:
    """Convierte un string de fecha al formato definido; retorna datetime.min si falla."""
    try:
        return datetime.strptime(valor.strip(), DATE_FORMAT)
    except (ValueError, AttributeError):
        return datetime.min


def normalizar_header(fieldnames):
    """Elimina el BOM (\ufeff) que puede aparecer en el primer campo."""
    return [f.lstrip("\ufeff") for f in fieldnames]


def normalizar_row(row: dict) -> dict:
    """Devuelve un nuevo dict con las claves sin BOM."""
    return {k.lstrip("\ufeff"): v for k, v in row.items()}


def abrir_csv(path: Path):
    """Abre el CSV probando encodings en orden; retorna (file_obj, encoding_usado)."""
    for enc in ENCODINGS:
        try:
            f = open(path, encoding=enc, newline="")
            f.read(1)   # forzar lectura para detectar error
            f.seek(0)
            return f, enc
        except UnicodeDecodeError:
            f.close()
    raise ValueError(f"No se pudo decodificar {path.name} con los encodings: {ENCODINGS}")


# ── Concatenar y deduplicar ────────────────────────────────────────────────────
def main():
    archivos = sorted(INPUT_FOLDER.glob("*.csv"))

    if not archivos:
        print(f"No se encontraron archivos CSV en: {INPUT_FOLDER}")
        sys.exit(1)

    print(f"Archivos encontrados en '{INPUT_FOLDER.name}':")
    for a in archivos:
        print(f"  - {a.name}  ({a.stat().st_size / 1_048_576:.1f} MB)")

    # Diccionario principal: usuario -> dict(row)
    registros: dict = {}
    header_guardado = None
    total_leidas    = 0
    duplicados      = 0

    for archivo in archivos:
        print(f"\nProcesando {archivo.name} ...", end=" ", flush=True)
        filas_archivo = 0

        with abrir_csv(archivo)[0] as fin:
            reader = csv.DictReader(fin)

            # Normalizar encabezado (quitar BOM si existe) y reasignar
            campos_normalizados = normalizar_header(reader.fieldnames or [])
            reader.fieldnames   = campos_normalizados

            # Guardar encabezado de referencia al primer archivo
            if header_guardado is None:
                header_guardado = campos_normalizados
            else:
                if campos_normalizados != header_guardado:
                    print(
                        f"\n[ADVERTENCIA] {archivo.name} tiene columnas distintas. "
                        "Se usaran las columnas del primer archivo. "
                        "Columnas faltantes quedaran en blanco."
                    )

            for row in reader:
                row = normalizar_row(row)   # quitar BOM de claves si persiste
                usuario = row.get(COL_USUARIO, "").strip()
                if not usuario:
                    continue  # omitir filas sin usuario

                fecha_actual = parse_fecha(row.get(COL_FECHA, ""))

                if usuario not in registros:
                    registros[usuario] = row
                else:
                    fecha_existente = parse_fecha(registros[usuario].get(COL_FECHA, ""))
                    if fecha_actual > fecha_existente:
                        registros[usuario] = row  # reemplazar con el más reciente
                        duplicados += 1
                    else:
                        duplicados += 1           # descartar el más antiguo (el actual)

                filas_archivo += 1

        total_leidas += filas_archivo
        print(f"{filas_archivo:,} filas")

    # ── Escribir resultado ───────────────────────────────────────────────────
    print(f"\nEscribiendo {OUTPUT_FILE.name} ...", end=" ", flush=True)

    with open(OUTPUT_FILE, "w", encoding=OUTPUT_ENCODING, newline="") as fout:
        writer = csv.DictWriter(
            fout,
            fieldnames=header_guardado,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in registros.values():
            writer.writerow(row)

    filas_escritas = len(registros)
    print(f"{filas_escritas:,} filas")

    print(f"\n[OK] Archivo generado  : {OUTPUT_FILE.resolve()}")
    print(f"     Total leidas      : {total_leidas:,}")
    print(f"     Usuarios unicos   : {filas_escritas:,}")
    print(f"     Duplicados elim.  : {duplicados:,}")
    print(f"     Columnas          : {header_guardado}")


if __name__ == "__main__":
    main()
