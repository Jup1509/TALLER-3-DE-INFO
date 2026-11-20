from datos_y_archivos import (
    GestorSistemaArchivos,
    generar_registros_aleatorios,
    ordenar_por_fc,
    validar_registro,
)
from mongo_atlas import ClienteMongoAtlas


def ingresar_datos(gestor_archivos, registros):
    print("\n--- Ingresar Nuevo Registro Biomédico ---")
    nuevo = {
        "id": input("ID (formato ID-001): ").strip(),
        "fr": input("Edad / FR (formato 18 Años): ").strip(),
        "fc": input("Frecuencia cardíaca (formato 090ppm): ").strip(),
        "spo2": input("SpO2 (formato 95%): ").strip(),
    }

    es_valido, errores = validar_registro(nuevo)
    if not es_valido:
        print("El registro NO cumple los formatos requeridos:")
        for err in errores:
            print("  * {}".format(err))
        gestor_archivos.registrar_log("Ingreso rechazado por validación: {}".format(nuevo))
        return registros

    registros.append(nuevo)
    registros_ordenados = ordenar_por_fc(registros)
    gestor_archivos.registrar_log("Registro '{}' validado, agregado y reordenado por FC.".format(nuevo["id"]))
    print("Registro válido agregado y ordenado por frecuencia cardíaca.")
    return registros_ordenados


def exportar_importar_archivos(gestor_archivos, registros):
    print("\n--- Exportar / Importar Archivos (TXT, CSV, JSON) ---")
    print("1. Exportar registros ordenados a TXT, CSV y JSON")
    print("2. Importar registros desde un archivo JSON")
    opcion = input("Elige una opción: ").strip()

    if opcion == "1":
        ruta_txt = gestor_archivos.guardar_txt(registros)
        ruta_csv = gestor_archivos.guardar_csv(registros)
        ruta_json = gestor_archivos.exportar_json(registros)
        print("Archivos guardados y organizados:")
        print("  * TXT : {}".format(ruta_txt))
        print("  * CSV : {}".format(ruta_csv))
        print("  * JSON: {}".format(ruta_json))
    elif opcion == "2":
        ruta_ingresada = input("Ruta o nombre del archivo JSON (ej. data/json/registros_ordenados.json): ").strip()
        try:
            datos_importados = gestor_archivos.importar_json(ruta_ingresada)
            validos = []
            for item in datos_importados:
                ok, _ = validar_registro(item)
                if ok:
                    validos.append(item)
            registros_actualizados = ordenar_por_fc(validos)
            print("Se importaron {} registros válidos y ordenados.".format(len(registros_actualizados)))
            return registros_actualizados
        except Exception as e:
            print("Error al importar archivo: {}".format(e))
    else:
        print("Opción inválida.")

    return registros


def validar_todos_los_datos(gestor_archivos, registros):
    print("\n--- Validación de Datos con Expresiones Regulares ---")
    total_validos = 0
    total_invalidos = 0

    for r in registros:
        ok, errores = validar_registro(r)
        if ok:
            total_validos += 1
        else:
            total_invalidos += 1
            print("Inválido -> {}: {}".format(r, ", ".join(errores)))

    gestor_archivos.registrar_log(
        "Validación ejecutada: {} válidos, {} inválidos.".format(total_validos, total_invalidos)
    )
    print("Resultado: {} registros válidos | {} registros inválidos.".format(total_validos, total_invalidos))


def menu_mongodb(gestor_archivos, registros):
    print("\n--- Conexión y Consultas en MongoDB Atlas ---")
    uri_input = input("Pega tu URI de MongoDB Atlas (URI USADO: mongodb+srv://juanpablovillota_db_user:0SHBP2d8RCC4ATgt@cluster0.uxmzddx.mongodb.net/): ").strip()
    cliente_mongo = ClienteMongoAtlas(uri=uri_input if uri_input else None)

    try:
        cliente_mongo.conectar()
        gestor_archivos.registrar_log("Conexión exitosa a MongoDB Atlas (colección signos_vitales).")
        print("Conectado correctamente a MongoDB Atlas.")

        print("1. Insertar registros validados en 'signos_vitales'")
        print("2. Consultar promedio de FC y SpO2 < 94 + exportar a 'resultados mongo.json'")
        print("3. Consultar un registro por ID")
        sub = input("Elige una opción: ").strip()

        if sub == "1":
            validos = [r for r in registros if validar_registro(r)[0]]
            insertados = cliente_mongo.insertar_validados(validos)
            gestor_archivos.registrar_log("Insertados {} documentos en 'signos_vitales'.".format(insertados))
            print("Se insertaron {} documentos en la colección 'signos_vitales'.".format(insertados))
        elif sub == "2":
            promedio = cliente_mongo.promedio_frecuencia_cardiaca()
            bajos = cliente_mongo.documentos_spo2_menor_94()
            archivo_exportado = cliente_mongo.exportar_consultas_json("resultados mongo.json")
            gestor_archivos.registrar_log(
                "Consultas ejecutadas (promedio FC={}, SpO2<94={}) y exportadas a '{}'.".format(
                    promedio, len(bajos), archivo_exportado
                )
            )
            print("Promedio de frecuencia cardíaca: {} ppm".format(promedio))
            print("Documentos con SpO2 menor a 94: {}".format(len(bajos)))
            print("Consultas exportadas en: {}".format(archivo_exportado))
        elif sub == "3":
            id_consulta = input("Ingresa el ID a consultar (ej. ID-001): ").strip()
            encontrado = cliente_mongo.consultar_por_id(id_consulta)
            gestor_archivos.registrar_log("Consulta por ID '{}' ejecutada.".format(id_consulta))
            if encontrado:
                print("Registro encontrado:", encontrado)
            else:
                print("No se encontró ningún registro con ID '{}'.".format(id_consulta))
        else:
            print("Subopción inválida.")

    except Exception as e:
        print("Error en MongoDB: {}".format(e))
        gestor_archivos.registrar_log("Error en operación MongoDB: {}".format(e))
    finally:
        cliente_mongo.cerrar()


def main():
    gestor_archivos = GestorSistemaArchivos()
    registros = ordenar_por_fc(generar_registros_aleatorios(50))
    gestor_archivos.registrar_log("Inicio del sistema: generados y ordenados 50 registros aleatorios.")
    print("Listo: se generaron y ordenaron {} registros biomédicos por frecuencia cardíaca.".format(len(registros)))

    while True:
        print("\n================ MENÚ PRINCIPAL - TALLER 3 ================")
        print("1. Ingresar datos")
        print("2. Exportar / Importar archivos (TXT, CSV, JSON)")
        print("3. Validar datos (Expresiones regulares)")
        print("4. Conectarse a MongoDB y ejecutar consultas (incluye por ID)")
        print("5. Regenerar 50 registros aleatorios ordenados por FC")
        print("0. Salir")

        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            registros = ingresar_datos(gestor_archivos, registros)
        elif opcion == "2":
            registros = exportar_importar_archivos(gestor_archivos, registros)
        elif opcion == "3":
            validar_todos_los_datos(gestor_archivos, registros)
        elif opcion == "4":
            menu_mongodb(gestor_archivos, registros)
        elif opcion == "5":
            registros = ordenar_por_fc(generar_registros_aleatorios(50))
            gestor_archivos.registrar_log("Se regeneraron 50 registros aleatorios ordenados por FC.")
            print("Se generaron 50 nuevos registros ordenados por frecuencia cardíaca.")
        elif opcion == "0":
            gestor_archivos.registrar_log("Salida del sistema.")
            print("Programa finalizado.")
            break
        else:
            print("Opción no válida, intenta de nuevo.")


if __name__ == "__main__":
    main()
