import csv
import io
import json
import os
import random
import re
import shutil
from datetime import datetime
from pathlib import Path

PATRONES = {
    "id": re.compile(r"^ID-\d{3}$"),
    "fr": re.compile(r"^\d{1,3} Años$"),
    "fc": re.compile(r"^\d{3}ppm$"),
    "spo2": re.compile(r"^(100|\d{1,2})%$"),
}


def validar_registro(registro):
    errores = []
    campos_requeridos = ("id", "fr", "fc", "spo2")

    for campo in campos_requeridos:
        if campo not in registro:
            errores.append(f"Falta el campo '{campo}'.")
            continue
        valor = str(registro[campo]).strip()
        if not PATRONES[campo].match(valor):
            errores.append(f"Campo '{campo}' con valor '{valor}' no cumple el formato esperado.")

    return len(errores) == 0, errores


def obtener_fc_entero(registro):
    fc_texto = str(registro.get("fc", "000ppm")).replace("ppm", "").strip()
    return int(fc_texto)


def obtener_spo2_entero(registro):
    spo2_texto = str(registro.get("spo2", "0%")).replace("%", "").strip()
    return int(spo2_texto)


def generar_registros_aleatorios(cantidad=50):
    if cantidad < 50:
        cantidad = 50

    registros = []
    for i in range(1, cantidad + 1):
        registro = {
            "id": f"ID-{i:03d}",
            "fr": f"{random.randint(1, 95)} Años",
            "fc": f"{random.randint(50, 170):03d}ppm",
            "spo2": f"{random.randint(85, 100)}%",
        }
        valido, _ = validar_registro(registro)
        if valido:
            registros.append(registro)

    return registros


def ordenar_por_fc(registros, descendente=False):
    return sorted(registros, key=obtener_fc_entero, reverse=descendente)


class GestorSistemaArchivos:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.carpeta_txt = self.base_dir / "data" / "txt"
        self.carpeta_csv = self.base_dir / "data" / "csv"
        self.carpeta_json = self.base_dir / "data" / "json"
        self.archivo_log = self.base_dir / "log.txt"
        self.crear_estructura_carpetas()

    def crear_estructura_carpetas(self):
        try:
            for carpeta in (self.carpeta_txt, self.carpeta_csv, self.carpeta_json):
                carpeta.mkdir(parents=True, exist_ok=True)
                if not os.path.exists(carpeta):
                    raise OSError(f"No se pudo verificar la carpeta {carpeta}")
            self.registrar_log("Estructura de carpetas /data/txt, /data/csv y /data/json verificada.")
        except Exception as e:
            print(f"[Error creando carpetas]: {e}")

    def registrar_log(self, accion):
        marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{marca_tiempo}] {accion}\n"
        try:
            with io.open(self.archivo_log, mode="a", encoding="utf-8") as archivo:
                archivo.write(linea)
        except OSError as e:
            print(f"[Error escribiendo en log.txt]: {e}")

    def organizar_archivo(self, ruta_origen):
        origen = Path(ruta_origen)
        if not origen.exists() or not origen.is_file():
            self.registrar_log(f"Error de ruta al organizar: '{origen}' no existe.")
            raise FileNotFoundError(f"El archivo no existe en la ruta: {origen}")

        extension = origen.suffix.lower()
        if extension == ".txt":
            destino = self.carpeta_txt / origen.name
        elif extension == ".csv":
            destino = self.carpeta_csv / origen.name
        elif extension == ".json":
            destino = self.carpeta_json / origen.name
        else:
            raise ValueError(f"Extensión no soportada para organizar: {extension}")

        try:
            if origen.resolve() != destino.resolve():
                shutil.move(str(origen), str(destino))
            self.registrar_log(f"Archivo organizado en '{destino}'.")
            return destino
        except Exception as e:
            self.registrar_log(f"Error al mover archivo '{origen}' a '{destino}': {e}")
            raise

    def guardar_txt(self, registros, nombre_archivo="registros_ordenados.txt"):
        temporal = self.base_dir / nombre_archivo
        try:
            buffer = io.StringIO()
            for r in registros:
                buffer.write(f"{r['id']} | {r['fr']} | {r['fc']} | {r['spo2']}\n")

            with io.open(temporal, mode="w", encoding="utf-8") as f:
                f.write(buffer.getvalue())

            ruta_final = self.organizar_archivo(temporal)
            self.registrar_log(f"Guardado TXT ({len(registros)} registros) en '{ruta_final}'.")
            return ruta_final
        except Exception as e:
            self.registrar_log(f"Error al guardar TXT: {e}")
            raise

    def guardar_csv(self, registros, nombre_archivo="registros_ordenados.csv"):
        temporal = self.base_dir / nombre_archivo
        encabezados = ["id", "fr", "fc", "spo2"]
        try:
            with open(temporal, mode="w", newline="", encoding="utf-8") as f:
                escritor = csv.DictWriter(f, fieldnames=encabezados)
                escritor.writeheader()
                escritor.writerows(registros)

            ruta_final = self.organizar_archivo(temporal)
            self.registrar_log(f"Guardado CSV ({len(registros)} registros) en '{ruta_final}'.")
            return ruta_final
        except Exception as e:
            self.registrar_log(f"Error al guardar CSV: {e}")
            raise

    def exportar_json(self, registros, nombre_archivo="registros_ordenados.json"):
        temporal = self.base_dir / nombre_archivo
        try:
            with open(temporal, mode="w", encoding="utf-8") as f:
                json.dump(registros, f, indent=4, ensure_ascii=False)

            ruta_final = self.organizar_archivo(temporal)
            self.registrar_log(f"Exportado JSON ({len(registros)} registros) en '{ruta_final}'.")
            return ruta_final
        except Exception as e:
            self.registrar_log(f"Error al exportar JSON: {e}")
            raise

    def importar_json(self, ruta_archivo):
        ruta = Path(ruta_archivo)
        if not ruta.is_absolute():
            if not ruta.exists() and (self.carpeta_json / ruta.name).exists():
                ruta = self.carpeta_json / ruta.name

        if not ruta.exists() or not ruta.is_file():
            self.registrar_log(f"Error al importar JSON: ruta '{ruta}' no encontrada.")
            raise FileNotFoundError(f"No se encontró el archivo JSON en: {ruta}")

        try:
            with open(ruta, mode="r", encoding="utf-8") as f:
                datos = json.load(f)
            if not isinstance(datos, list):
                raise ValueError("El archivo JSON debe contener una lista de registros.")
            self.registrar_log(f"Importado JSON ({len(datos)} registros) desde '{ruta}'.")
            return datos
        except Exception as e:
            self.registrar_log(f"Error al leer JSON desde '{ruta}': {e}")
            raise