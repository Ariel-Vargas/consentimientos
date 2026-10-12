"""
concat_csv.py
-------------
Concatena y deduplica archivos CSV por usuario y tipo de consentimiento.
Conserva únicamente el registro con la fecha más reciente para cada combinación
de (usuario, tipo_consentimiento).

Uso:
    python concat_csv.py <carpeta_o_archivo> <archivo_salida>

Ejemplos:
    python concat_csv.py politica politica.csv
    python concat_csv.py consentimiento consent.csv
    python concat_csv.py  (solicita los parámetros interactivamente si no se pasan)

Salida:
    El archivo resultante se guarda en la carpeta leída y se copia/reemplaza
    en la carpeta principal del proyecto (Dash consentimientos).
"""

import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ── Configuración global ──────────────────────────────────────────────────────
ROOT_DIR        = Path(__file__).resolve().parent
ENCODINGS       = ["utf-8-sig", "latin-1"]  # se prueba en orden para detectar encoding/BOM
OUTPUT_ENCODING = "utf-8-sig"               # utf-8 con BOM (compatible con Excel)

COL_USUARIO = "usuario"               # columna identificador de usuario
COL_TIPO    = "tipo_consentimiento"   # columna tipo de consentimiento
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
    parser = argparse.ArgumentParser(
        description="Concatena y deduplica archivos CSV por usuario y tipo de consentimiento."
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        default=None,
        help="Carpeta o archivo CSV a leer (ej: 'politica', 'consentimiento', o 'politica/pol.csv')",
    )
    parser.add_argument(
        "salida",
        nargs="?",
        default=None,
        help="Nombre del archivo de salida (ej: 'politica.csv' o 'consent.csv')",
    )
    parser.add_argument("-i", "--input", dest="input_opt", default=None, help="Carpeta o archivo de entrada")
    parser.add_argument("-o", "--output", dest="output_opt", default=None, help="Nombre del archivo de salida")

    args = parser.parse_args()

    entrada = args.input_opt or args.entrada
    if not entrada:
        entrada = input("Ingrese la carpeta o archivo a leer (ej: politica): ").strip()
        if not entrada:
            entrada = "politica"

    salida = args.output_opt or args.salida
    if not salida:
        default_salida = f"{Path(entrada).stem}.csv"
        salida = input(f"Ingrese el nombre del archivo de salida [{default_salida}]: ").strip()
        if not salida:
            salida = default_salida

    # Asegurar extensión .csv
    if not salida.lower().endswith(".csv"):
        salida += ".csv"
    output_name = Path(salida).name

    # Resolver ruta de entrada (relativa a ROOT_DIR o cwd)
    ruta_entrada = Path(entrada)
    if not ruta_entrada.is_absolute():
        if (ROOT_DIR / ruta_entrada).exists():
            ruta_entrada = (ROOT_DIR / ruta_entrada).resolve()
        elif (Path.cwd() / ruta_entrada).exists():
            ruta_entrada = (Path.cwd() / ruta_entrada).resolve()
        else:
            ruta_entrada = (ROOT_DIR / ruta_entrada).resolve()

    if not ruta_entrada.exists():
        print(f"\n[ERROR] No existe la ruta de entrada: {ruta_entrada}")
        sys.exit(1)

    if ruta_entrada.is_dir():
        carpeta_origen = ruta_entrada
        archivos = sorted(carpeta_origen.glob("*.csv"))
    else:
        carpeta_origen = ruta_entrada.parent
        archivos = [ruta_entrada]

    if not archivos:
        print(f"\n[ERROR] No se encontraron archivos CSV en: {ruta_entrada}")
        sys.exit(1)

    print(f"\nArchivos a procesar en '{carpeta_origen.name}':")
    for a in archivos:
        print(f"  - {a.name}  ({a.stat().st_size / 1_048_576:.1f} MB)")

    # Diccionario principal: (usuario, tipo_consentimiento) -> dict(row)
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

                tipo = (row.get(COL_TIPO) or row.get("tipo_connsentimiento") or "").strip()
                clave = (usuario, tipo)

                fecha_actual = parse_fecha(row.get(COL_FECHA, ""))

                if clave not in registros:
                    registros[clave] = row
                else:
                    fecha_existente = parse_fecha(registros[clave].get(COL_FECHA, ""))
                    if fecha_actual > fecha_existente:
                        registros[clave] = row  # reemplazar con el más reciente
                        duplicados += 1
                    else:
                        duplicados += 1           # descartar el más antiguo (el actual)

                filas_archivo += 1

        total_leidas += filas_archivo
        print(f"{filas_archivo:,} filas")

    # ── Rutas de guardado ─────────────────────────────────────────────────────
    destino_origen = (carpeta_origen / output_name).resolve()
    destino_raiz   = (ROOT_DIR / output_name).resolve()

    print(f"\nEscribiendo {output_name} ...", end=" ", flush=True)

    # 1. Guardar en la carpeta correspondiente donde fue leído
    with open(destino_origen, "w", encoding=OUTPUT_ENCODING, newline="") as fout:
        writer = csv.DictWriter(
            fout,
            fieldnames=header_guardado,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in registros.values():
            writer.writerow(row)

    # 2. Copiar/reemplazar en la carpeta principal 'Dash consentimientos'
    if destino_raiz != destino_origen:
        shutil.copy2(destino_origen, destino_raiz)

    filas_escritas = len(registros)
    usuarios_unicos = len(set(u for u, _ in registros.keys()))
    print(f"{filas_escritas:,} filas")

    print(f"\n[OK] Guardado en carpeta de origen  : {destino_origen}")
    if destino_raiz != destino_origen:
        print(f"[OK] Guardado en carpeta principal  : {destino_raiz}")
    print(f"     Total filas leidas             : {total_leidas:,}")
    print(f"     Registros unicos (usr + tipo)  : {filas_escritas:,}")
    print(f"     Usuarios unicos                : {usuarios_unicos:,}")
    print(f"     Duplicados descartados         : {duplicados:,}")
    print(f"     Columnas                       : {header_guardado}")


if __name__ == "__main__":
    main()
