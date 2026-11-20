import json
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from datos_y_archivos import obtener_fc_entero, obtener_spo2_entero


class ClienteMongoAtlas:
    def __init__(
        self,
        uri=None,
        nombre_bd="taller3_bioingenieria",
        nombre_coleccion="signos_vitales",
    ):
        self.uri = (uri or os.getenv("MONGODB_URI", "")).strip()
        self.nombre_bd = nombre_bd
        self.nombre_coleccion = nombre_coleccion
        self.cliente = None
        self.coleccion = None

    def conectar(self):
        if not self.uri:
            raise ValueError("Debes ingresar o configurar la URI de conexión de MongoDB Atlas.")
        try:
            self.cliente = MongoClient(self.uri, serverSelectionTimeoutMS=6000)
            self.cliente.admin.command("ping")
            bd = self.cliente[self.nombre_bd]
            self.coleccion = bd[self.nombre_coleccion]
            return True
        except PyMongoError as e:
            raise ConnectionError("No fue posible conectar a MongoDB Atlas: {}".format(e))

    def insertar_validados(self, registros_validados):
        if self.coleccion is None:
            self.conectar()
        if not registros_validados:
            return 0
        documentos = [dict(r) for r in registros_validados]
        resultado = self.coleccion.insert_many(documentos)
        return len(resultado.inserted_ids)

    def promedio_frecuencia_cardiaca(self):
        if self.coleccion is None:
            self.conectar()
        docs = list(self.coleccion.find({}, {"_id": 0, "fc": 1}))
        if not docs:
            return 0.0
        valores = [obtener_fc_entero(d) for d in docs if "fc" in d]
        return round(sum(valores) / len(valores), 2) if valores else 0.0

    def documentos_spo2_menor_94(self):
        if self.coleccion is None:
            self.conectar()
        docs = list(self.coleccion.find({}, {"_id": 0}))
        return [d for d in docs if obtener_spo2_entero(d) < 94]

    def consultar_por_id(self, id_buscado):
        if self.coleccion is None:
            self.conectar()
        return self.coleccion.find_one({"id": id_buscado.strip()}, {"_id": 0})

    def exportar_consultas_json(self, ruta_archivo="resultados mongo.json"):
        destino = Path(ruta_archivo)
        destino.parent.mkdir(parents=True, exist_ok=True)

        promedio_fc = self.promedio_frecuencia_cardiaca()
        spo2_bajos = self.documentos_spo2_menor_94()

        contenido = {
            "promedio_frecuencia_cardiaca": promedio_fc,
            "total_spo2_menor_94": len(spo2_bajos),
            "registros_spo2_menor_94": spo2_bajos,
        }

        with open(destino, mode="w", encoding="utf-8") as f:
            json.dump(contenido, f, indent=4, ensure_ascii=False)

        return destino

    def cerrar(self):
        if self.cliente is not None:
            self.cliente.close()
