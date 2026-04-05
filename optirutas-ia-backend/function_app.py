import azure.functions as func
import logging
import json
import os
import sys
from azure.storage.blob import BlobServiceClient

# Agregar el directorio raíz al path para importar el algoritmo
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from alg_nsga2 import alg_NSGA2, preparar_datos_para_algoritmo, generar_graficas_y_subir

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Configuración de Azure Storage
CADENA_CONEXION_AZURE = os.environ.get("AzureWebJobsStorage")
NOMBRE_CONTENEDOR = "insight-images"

@app.route(route="optimize")
def optimizar(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Función HTTP de optimización procesando la solicitud.')

    try:
        # 1. Obtener los datos del frontend
        cuerpo = req.get_json()
        nodos = cuerpo.get('nodes')
        capacidad_vehiculo = cuerpo.get('vehicleCapacity')
        ventana_tiempo = cuerpo.get('timeWindow')

        # 2. Preparar los datos para el algoritmo
        numN, numC, capacidad, coordenadas, horario = preparar_datos_para_algoritmo(
            nodos, capacidad_vehiculo, ventana_tiempo
        )

        # 3. Ejecutar el algoritmo NSGA-II
        poblacion_final = alg_NSGA2(numN, numC, coordenadas, horario, capacidad)

        # 4. Generar gráficas y subirlas a Azure Blob Storage
        cliente_blob = BlobServiceClient.from_connection_string(CADENA_CONEXION_AZURE)
        urls_imagenes = generar_graficas_y_subir(poblacion_final, cliente_blob, NOMBRE_CONTENEDOR)

        # 5. Formatear la respuesta para el frontend
        pareto_front_json = []
        coordenadas_nodos_dict = {nodo['id']: (nodo['lat'], nodo['lng']) for nodo in nodos}

        # Si poblacion_final es una lista de Individuos, recórrela. Si es solo uno, conviértelo en lista.
        if not isinstance(poblacion_final, list):
            poblacion_final = [poblacion_final]

        for i, individuo in enumerate(poblacion_final):
            # Serialización básica de rutas: lista de trayectos de cada camión
            rutas_serializadas = []
            if hasattr(individuo, 'solucion') and individuo.solucion:
                for camion in individuo.solucion:
                    # Cada camión: lista de coordenadas (x, y)
                    trayecto = camion[0]
                    rutas_serializadas.append([(p[0][0], p[0][1]) for p in trayecto])

            pareto_front_json.append({
                "id": f"sol-{i+1}",
                "label": chr(65 + i),
                "distancia": individuo.evaluacion_trayecto,
                "carga_total": individuo.evaluacion_carga,
                "tiempo": individuo.evaluacion_tiempo,
                "routes_serializadas": rutas_serializadas
            })

        respuesta = {
            "ejemplarId": f"AZURE-VRP-{req.headers.get('x-ms-request-id', '')}",
            "paretoFront": pareto_front_json,
            "coordenadas_nodos": coordenadas_nodos_dict,
            "insightImages": urls_imagenes
        }

        return func.HttpResponse(
            json.dumps(respuesta),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Ocurrió un error: {e}")
        return func.HttpResponse(
            f"Error al procesar la solicitud: {str(e)}",
            status_code=500
        )