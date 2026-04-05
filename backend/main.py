# main.py
import os
import io
import numpy as np
import matplotlib.pyplot as plt
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Tuple
import logging
import random

# ¡NUEVO! Importamos el middleware de CORS
from fastapi.middleware.cors import CORSMiddleware
# main.py

from datetime import datetime, timedelta 
from alg_nsga2 import preparar_datos_para_algoritmo, alg_NSGA2, crear_matriz_de_distancias_y_tiempos

logging.basicConfig(level=logging.INFO)

class Node(BaseModel):
    id: str
    lat: float
    lng: float
    demanda: int = 0

class OptimizeRequest(BaseModel):
    nodes: List[Node]
    vehicleCapacity: int
    timeWindow: Tuple[str, str]
    numVehicles: int 
    serviceTime: int  # Nuevo campo para el tiempo de servicio en minutos
    vehicleMPG: float  # Nuevo campo para el rendimiento del vehículo en millas por

app = FastAPI(
    title="API de Optimización de Rutas",
    description="Usa un algoritmo genético NSGA-II para optimizar rutas de recolección."
)

# --- CONFIGURACIÓN DE CORS ---
# Definimos qué orígenes permitimos. El asterisco "*" significa "cualquiera".
# Esto es perfecto para desarrollo local.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permitir todas las cabeceras
)
# --- FIN DE LA CONFIGURACIÓN DE CORS ---


@app.get("/")
def read_root():
    return {"status": "API de optimización funcionando"}



# REEMPLAZA ESTA FUNCIÓN COMPLETA EN main.py



@app.post("/optimize")
async def optimize_route(request_data: OptimizeRequest):
    """
    Endpoint principal que recibe los datos del problema, ejecuta el algoritmo
    y devuelve un conjunto de soluciones óptimas (Frente de Pareto).
    """
    logging.info("Petición recibida en /optimize.")
    try:
        # --- 1. Extracción y Preparación de Datos ---
        cuerpo = request_data.dict()
        nodos = cuerpo.get('nodes')
        capacidad_vehiculo = cuerpo.get('vehicleCapacity')
        num_vehiculos = cuerpo.get('numVehicles')
        
        time_window = cuerpo.get('timeWindow')

        # --- NUEVO: Se formatea el timeWindow para añadir los segundos ---
        # Convierte ('08:00', '18:00') a ('08:00:00', '18:00:00')
        time_window_formateado = (time_window[0] + ':00', time_window[1] + ':00')
        
        # Se sigue usando el original para la hora de inicio que no necesita segundos
        hora_inicio_str = time_window[0]
        
        # Se obtienen los parámetros adicionales para el itinerario y cálculos ambientales.
        tiempo_servicio_min = cuerpo.get('serviceTime')
        vehicle_mpg = cuerpo.get('vehicleMPG')

        # --- Bloque de Validación ---
        # Se asegura de que los campos requeridos hayan sido enviados por el frontend.
        if tiempo_servicio_min is None:
            raise HTTPException(status_code=400, detail="El campo 'serviceTime' es obligatorio y no fue recibido.")
        if not vehicle_mpg:
            raise HTTPException(status_code=400, detail="El campo 'vehicleMPG' es obligatorio y no fue recibido.")
        
        # Convierte la hora de inicio (en formato string) a un objeto datetime para poder hacer cálculos.
        hora_inicio_dt = datetime.strptime(hora_inicio_str, '%H:%M')

        # Diccionarios auxiliares para búsquedas eficientes.
        id_a_demanda = {n['id']: n['demanda'] for n in nodos}
        id_a_indice = {n['id']: i for i, n in enumerate(nodos)}
        coord_a_id = {(n['lat'], n['lng']): n['id'] for n in nodos}

        # Prepara los datos para ser compatibles con el formato que requiere el algoritmo.
        numN, numC, capacidad, coordenadas, horario = preparar_datos_para_algoritmo(
            nodos, capacidad_vehiculo, time_window_formateado, num_vehiculos
        )

        # --- 2. Ejecución del Algoritmo Principal ---
        logging.info("Creando matrices de distancias y tiempos con Mapbox...")
        matriz_distancias, matriz_tiempos = crear_matriz_de_distancias_y_tiempos(coordenadas)
        if not matriz_distancias or not matriz_tiempos:
            raise HTTPException(status_code=500, detail="No se pudieron crear las matrices de distancias/tiempos.")
        logging.info("Matrices creadas.")

        logging.info("Ejecutando el algoritmo NSGA-II...")
        poblacion_final, historial_fitness = alg_NSGA2(numN, numC, coordenadas, horario, capacidad, matriz_distancias)
        logging.info("Algoritmo finalizado.")

        # Opcional: Generación de gráficas de resultados.
        urls_imagenes = {}
        # ... (código para generar y subir gráficas) ...

          # --- SECCIÓN DE PROCESAMIENTO DE RESULTADOS ACTUALIZADA ---
        pareto_front_json = []

        # NUEVO: Constantes para el cálculo ambiental
        METERS_TO_MILES = 0.000621371
        DIESEL_KG_CO2E_PER_GALLON = 10.22
        KG_CO2E_PER_CAR_YEAR = 4600 # Aproximación EPA
        KG_CO2E_PER_TREE_10YRS = 167 # Aproximación EPA

        for i, individuo in enumerate(poblacion_final):
            
            # --- NUEVO: Cálculo de Impacto Ambiental para la solución completa ---
            distancia_total_solucion_millas = individuo.evaluacion_trayecto * METERS_TO_MILES
            galones_consumidos = distancia_total_solucion_millas / vehicle_mpg if vehicle_mpg > 0 else 0
            kg_co2e_total = galones_consumidos * DIESEL_KG_CO2E_PER_GALLON

            impacto_ambiental = {
                "total_kg_co2e": round(kg_co2e_total, 2),
                "equivalencies": {
                    "passenger_cars_per_year": round(kg_co2e_total / KG_CO2E_PER_CAR_YEAR, 3),
                    "tree_seedlings_10_years": round(kg_co2e_total / KG_CO2E_PER_TREE_10YRS, 1)
                }
            }
            # --- FIN DEL CÁLCULO AMBIENTAL ---
            
            rutas_formateadas = []
            if hasattr(individuo, 'solucion') and individuo.solucion:
                for camion_idx, camion_data in enumerate(individuo.solucion):
                    trayecto_coords = camion_data[0]
                    nodos_secuencia = [coord_a_id.get(tuple(punto[0]), "desconocido") for punto in trayecto_coords]
                    
                    # --- NUEVO: Generación del Itinerario Detallado (steps) ---
                    itinerario_steps = []
                    tiempo_acumulado_seg = 0
                    carga_acumulada = 0
                    depot_id = nodos_secuencia[0]

                    # Añadimos el primer paso (salida del depósito)
                    itinerario_steps.append({
                        "nodeId": depot_id,
                        "arrivalTime": hora_inicio_dt.strftime('%H:%M'),
                        "departureTime": hora_inicio_dt.strftime('%H:%M'),
                        "cumulativeLoad": 0
                    })
                    
                    for j in range(len(nodos_secuencia) - 1):
                        id_origen = nodos_secuencia[j]
                        id_destino = nodos_secuencia[j+1]
                        
                        idx_origen = id_a_indice.get(id_origen)
                        idx_destino = id_a_indice.get(id_destino)
                        
                        tiempo_viaje_seg = matriz_tiempos[idx_origen][idx_destino] if idx_origen is not None and idx_destino is not None else 0
                        tiempo_acumulado_seg += tiempo_viaje_seg
                        
                        hora_llegada_dt = hora_inicio_dt + timedelta(seconds=tiempo_acumulado_seg)
                        
                        # Si no es el depósito final, se añade el tiempo de servicio
                        if j < len(nodos_secuencia) - 2:
                            tiempo_acumulado_seg += tiempo_servicio_min * 60
                        
                        hora_salida_dt = hora_inicio_dt + timedelta(seconds=tiempo_acumulado_seg)
                        
                        demanda_actual = id_a_demanda.get(id_destino, 0)
                        carga_acumulada += demanda_actual
                        
                        itinerario_steps.append({
                            "nodeId": id_destino,
                            "arrivalTime": hora_llegada_dt.strftime('%H:%M'),
                            "departureTime": hora_salida_dt.strftime('%H:%M'),
                            "cumulativeLoad": carga_acumulada
                        })
                    # --- FIN DE LA GENERACIÓN DEL ITINERARIO ---

                    # Cálculos anteriores por camión (distancia, carga, etc.)
                    # (Este bloque se puede mantener o simplificar si los datos del itinerario son suficientes)
                    
                    rutas_formateadas.append({
                        "camionId": camion_idx + 1,
                        "nodos": nodos_secuencia,
                        "path": [(p[0][0], p[0][1]) for p in trayecto_coords],
                        # Los datos anteriores siguen siendo útiles para resúmenes
                        "distanciaTotal": ..., 
                        "tiempoEstimado": ...,
                        "cargaRecolectada": ...,
                        "porcentajeCapacidad": ...,
                        "steps": itinerario_steps # AÑADIMOS EL ITINERARIO
                    })

            pareto_front_json.append({
                "id": f"sol-{i+1}", "label": chr(65 + i), 
                "distancia": individuo.evaluacion_trayecto,
                "carga_total": individuo.evaluacion_carga, 
                "tiempo": individuo.evaluacion_tiempo,
                "routes": rutas_formateadas,
                "environmentalImpact": impacto_ambiental # AÑADIMOS EL IMPACTO AMBIENTAL
            })
        
        coordenadas_nodos_dict = {nodo['id']: (nodo['lat'], nodo['lng']) for nodo in nodos}
        
        respuesta = {
            "ejemplarId": f"DOCKER-VRP-{random.randint(1000, 9999)}",
            "paretoFront": pareto_front_json,
            "coordenadas_nodos": coordenadas_nodos_dict,
            "graficas": urls_imagenes
        }
        
        return respuesta

    except Exception as e:
        logging.error(f"Ha ocurrido un error durante la ejecución: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

#Funcion para generar y subir graficas a Azure Blob Storage
def generar_y_subir_graficas(poblacion_final, historial_fitness, connection_string):
    """Genera gráficas, las sube a Azure Blob Storage y devuelve las URLs."""

    urls_imagenes = {}
    if not historial_fitness or not poblacion_final:
        return urls_imagenes

    # Usamos un nombre de contenedor único para cada ejecución para evitar conflictos
    container_name = f"resultados-optimizacion-{random.randint(10000, 99999)}"

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    try:
        blob_service_client.create_container(container_name, public_access='blob')
    except Exception as e:
        print(f"El contenedor '{container_name}' ya existe o hubo un error: {e}")

    # --- Gráfica 1: Progreso de la Optimización ---
    plt.figure(figsize=(10, 6))
    mejor_historial = [h['mejor'] for h in historial_fitness]
    promedio_historial = [h['promedio'] for h in historial_fitness]

    plt.plot(mejor_historial, label='Mejor Solución por Generación', color='blue')
    plt.plot(promedio_historial, label='Aptitud Promedio de la Población', color='green', linestyle='--')

    plt.title('Progreso de la Optimización')
    plt.xlabel('Generación')
    plt.ylabel('Aptitud (menor es mejor)')
    plt.legend()
    plt.grid(True)

    buffer1 = io.BytesIO()
    plt.savefig(buffer1, format='png')
    plt.close()
    buffer1.seek(0)

    blob_client1 = blob_service_client.get_blob_client(container=container_name, blob="progreso_optimizacion.png")
    blob_client1.upload_blob(buffer1, overwrite=True)
    urls_imagenes['progreso_optimizacion'] = blob_client1.url

    # --- Gráfica 2: Espacio de Soluciones Finales (Carga vs. Distancia) ---
    plt.figure(figsize=(10, 6))
    cargas = [ind.evaluacion_carga for ind in poblacion_final]
    distancias = [ind.evaluacion_trayecto for ind in poblacion_final]

    plt.scatter(cargas, distancias, alpha=0.6, label='Soluciones Finales')

    mejor_solucion = min(poblacion_final, key=lambda x: x.evaluacion)
    plt.scatter(mejor_solucion.evaluacion_carga, mejor_solucion.evaluacion_trayecto, color='red', s=150, zorder=5, edgecolors='black', label='Mejor Solución Encontrada')

    plt.title('Espacio de Soluciones Finales')
    plt.xlabel('Carga Total')
    plt.ylabel('Distancia Total')
    plt.legend()
    plt.grid(True)

    buffer2 = io.BytesIO()
    plt.savefig(buffer2, format='png')
    plt.close()
    buffer2.seek(0)

    blob_client2 = blob_service_client.get_blob_client(container=container_name, blob="soluciones_finales.png")
    blob_client2.upload_blob(buffer2, overwrite=True)
    urls_imagenes['soluciones_finales'] = blob_client2.url

    return urls_imagenes