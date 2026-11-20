# Taller 3 - Informática: Gestión y Análisis de Signos Vitales con MongoDB Atlas

Aplicación de consola desarrollada en **Python 3.9** para el registro, validación, manejo de archivos y análisis de signos vitales en la nube mediante **MongoDB Atlas**.
#Estructura del Proyecto:
- `main.py`: Punto de entrada de la aplicación y menú interactivo por consola.
- `datos_y_archivos.py`: Lógica de generación e ingreso de registros, validación mediante expresiones regulares y exportación/importación en formatos `TXT`, `CSV` y `JSON`.
- `mongo_atlas.py`: Configuración de conexión a MongoDB Atlas (`taller3_bioingenieria` / `signos_vitales`), sincronización de documentos y ejecución de consultas clínicas (incluyendo búsqueda por ID).

#Requisitos Previos

- **Python 3.9** o superior.
- Dependencia de conexión a MongoDB:
  ```bash
  pip install pymongo

  
