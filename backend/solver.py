# --- Imports ---
import matplotlib
matplotlib.use('Agg') # MUY IMPORTANTE: Debe estar antes de importar pyplot
import matplotlib.pyplot as plt
import numpy as np
import io
import math
import random
from datetime import datetime, time, timedelta
from collections import namedtuple

# --- Estructura de Datos ---
Individuo = namedtuple('Individuo', ['solucion', 'evaluacion', 'evaluacion_trayecto', 'evaluacion_carga', 'evaluacion_tiempo', 'dominacion', 'distancia'])

# --- Funciones de Preparación y Utilería ---
def preparar_datos_para_algoritmo(nodos, capacidad_vehiculo, ventana_tiempo):
    num_nodos = len(nodos)
    num_camiones = 2  # Considera hacerlo configurable desde el JSON
    capacidad = capacidad_vehiculo
    coordenadas = [ [(n['lat'], n['lng']), n.get('demanda', 0)] for n in nodos ]
    horario = ventana_tiempo
    return num_nodos, num_camiones, capacidad, coordenadas, horario

def distancia_euclidiana(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def dividir_horas(intervalos, horario):
    hora_inicio_dt = datetime.strptime(horario[0], "%H:%M:%S")
    hora_fin_dt = datetime.strptime(horario[1], "%H:%M:%S")
    duracion = hora_fin_dt - hora_inicio_dt
    intervalo_duracion = duracion / intervalos
    periodos = []
    inicio_intervalo = hora_inicio_dt
    for _ in range(intervalos):
        fin_intervalo = inicio_intervalo + intervalo_duracion
        periodos.append((inicio_intervalo.time(), fin_intervalo.time()))
        inicio_intervalo = fin_intervalo
    return periodos

def generar_hora_aleatoria(horario_inicio, hora_final_str):
    hora_inicio_dt = datetime.combine(datetime.today(), horario_inicio)
    hora_fin_dt = datetime.combine(datetime.today(), datetime.strptime(hora_final_str, "%H:%M:%S").time())
    if hora_fin_dt < hora_inicio_dt:
        hora_fin_dt += timedelta(days=1)
    diferencia_segundos = (hora_fin_dt - hora_inicio_dt).total_seconds()
    segundos_aleatorios = random.randint(0, int(diferencia_segundos))
    hora_aleatoria = (hora_inicio_dt + timedelta(seconds=segundos_aleatorios)).time()
    return str(hora_aleatoria)

def limpiar_lista(lista):
    return [sublista for sublista in lista if sublista]

# --- Funciones de Evaluación ---
def evaluar_recorrido(trayecto):
    distancia = 0
    num_residuos = 0
    for i in range(1, len(trayecto)):
        distancia += distancia_euclidiana(trayecto[i-1][0], trayecto[i][0])
        num_residuos += trayecto[i][1]
    return distancia, num_residuos

def evaluar_camion(camion, capacidad, penalizacion=1000):
    total_distancia, total_residuos = evaluar_recorrido(camion[0])
    evaluacion_carga = total_residuos
    if total_residuos > capacidad:
        evaluacion_carga += (total_residuos - capacidad) * penalizacion

    horario = camion[1]
    hora_de_termino_str = camion[2]
    hora_dt = time.fromisoformat(hora_de_termino_str)
    evaluacion_tiempo = 1 
    if hora_dt > horario[1]:
        hora_inicio_dt = datetime.combine(datetime.today(), horario[1])
        hora_fin_dt = datetime.combine(datetime.today(), hora_dt)
        exceso_segundos = (hora_fin_dt - hora_inicio_dt).total_seconds()
        evaluacion_tiempo += exceso_segundos * penalizacion
        
    return total_distancia, evaluacion_carga, evaluacion_tiempo

def evaluar_individuo(individuo, capacidad):
    eval_distancia_total, eval_carga_total, eval_tiempo_total = 0, 0, 0
    for camion in individuo.solucion:
        eval_dist, eval_carga, eval_tiempo = evaluar_camion(camion, capacidad)
        eval_distancia_total += eval_dist
        eval_carga_total += eval_carga
        eval_tiempo_total += eval_tiempo
    
    eval_total = eval_distancia_total + eval_carga_total + eval_tiempo_total
    
    return individuo._replace(
        evaluacion=eval_total, 
        evaluacion_trayecto=eval_distancia_total, 
        evaluacion_carga=eval_carga_total, 
        evaluacion_tiempo=eval_tiempo_total
    )

def evaluar_poblacion(poblacion, capacidad):
    return [evaluar_individuo(ind, capacidad) for ind in poblacion]

# --- Lógica Principal del Algoritmo NSGA-II ---
# (Aquí se incluirían todas las funciones de `alg_nsga2.py` como `genera_poblacion`,
# `seleccion_por_torneo`, `cruza_de_permutaciones`, `mutacion`, `ordenamiento_no_determinado`, etc.
# Por brevedad, las omito aquí, pero debes copiarlas de tu archivo `alg_nsga2.py` a esta sección)

# ... (Pega aquí el resto de las funciones del algoritmo desde `alg_nsga2.py`) ...
# Por ejemplo:
def genera_poblacion(num_nodos, num_camiones, coordenadas, horario):
    # Tu código de `genera_poblacion` va aquí
    poblacion = []    
    deposito = coordenadas[0]
    i = 0
    while i < 100:      
        coordenadas_agregadas = []  
        solucion = []    
        periodos = dividir_horas(num_camiones, horario)            
        nodos = 1
        camion = 1                              
        while camion <= num_camiones:                                     
            dimension = num_nodos-1
            datos_camion = []
            trayecto = []            
            num_contenedores = 0            
            trayecto.append(deposito)
            coordenadas_agregadas.append(deposito)                
            if dimension > 0:
                num_contenedores = random.randint(1, dimension)
            contenedores = 1
            while contenedores <= num_contenedores:
                coordenada = random.choice(coordenadas)
                if coordenada not in coordenadas_agregadas:                    
                    trayecto.append(coordenada)
                    coordenadas_agregadas.append(coordenada)
                    nodos += 1
                contenedores += 1                                                                 
            if camion == num_camiones and nodos < num_nodos:
                coordenadas_faltantes = [coordenada for coordenada in coordenadas if coordenada not in coordenadas_agregadas]
                for coordenada in coordenadas_faltantes:
                    trayecto.append(coordenada)
                    nodos += 1
            trayecto.append(deposito) 
            datos_camion.append(trayecto)
            datos_camion.append(periodos[camion-1])
            hora_que_finalizo = generar_hora_aleatoria(periodos[camion-1][0], horario[1])
            datos_camion.append(hora_que_finalizo)
            solucion.append(datos_camion)
            dimension = dimension - contenedores               
            camion += 1                                       
        individuo = Individuo(solucion, 0, 0, 0, 0, [0,None], 0)
        poblacion.append(individuo)
        i += 1    
    
    return poblacion

# Regresa dos individuos de la poblacion que seran los padres
def seleccion_por_torneo(poblacion, capacidad):
    seleccionados = []
    k = 0    
    # Seleccionamos k individuos de la poblacion
    while k < 10:
        individuo = random.choice(poblacion)
        if individuo not in seleccionados:                    
            seleccionados.append(individuo)
        k += 1
    seleccionados = sorted(seleccionados, key=lambda individuo: evaluar_individuo(individuo, capacidad).evaluacion)    
    # Obtenemos al mejor de los seleccionados
    mejor_de_seleccionados_1 = seleccionados[0]

    seleccionados = []
    k = 0    
    # Seleccionamos otros k individuos de la poblacion
    while k < 10:
        individuo = random.choice(poblacion)
        if individuo not in seleccionados:                    
            seleccionados.append(individuo)
        k += 1
    seleccionados = sorted(seleccionados, key=lambda individuo: evaluar_individuo(individuo, capacidad).evaluacion)    
    # Obtenemos al mejor de los seleccionados
    mejor_de_seleccionados_2 = seleccionados[0]
    
    return poblacion.index(mejor_de_seleccionados_1), poblacion.index(mejor_de_seleccionados_2)

# Realiza el cruce para permutaciones, con probabilidad pc => [0.6-0.9], 
# para los horarios de los hijos uno tendra el horario del primer padre y el otro del segundo,
# para los trayectos de cada camion de los hijos seran de diferentes tamaños al de los padres
def cruza_de_permutaciones(sol1, sol2, pc):    
    trayecto_de_sol1 = []
    trayecto_de_sol2 = []
    sol_hijo1 = []
    sol_hijo2 = []
    trayecto_de_h1 = []
    trayecto_de_h2 = []    
    
    # Recupera el trayecto de los camiones a los contenedores, sin contar al deposito, de la primera solucion
    for camion in sol1:
        trayecto = camion[0]
        deposito = trayecto[0]
        contenedor = 1
        while trayecto[contenedor] != deposito:
            trayecto_de_sol1.append(trayecto[contenedor])
            contenedor += 1
    # Recupera el trayecto de los camiones a los contenedores, sin contar al deposito, de la segunda solucion
    for camion in sol2:
        trayecto = camion[0]
        deposito = trayecto[0]
        contenedor = 1
        while trayecto[contenedor] != deposito:
            trayecto_de_sol2.append(trayecto[contenedor])
            contenedor += 1

    tamanio = len(trayecto_de_sol1)
    indice_comienzo = random.randrange(0, tamanio)
    indice_final = random.randrange(indice_comienzo, tamanio)
    indices_no_agregados = []
    ind = 0
    # Se agregan unas coordenadas, el hijo 1 del padre A y el hijo 2 del padre B
    while ind < tamanio:
        if ind >= indice_comienzo and ind <= indice_final:
            if np.random.rand() <= pc:
                trayecto_de_h1.append(trayecto_de_sol1[ind])
                trayecto_de_h2.append(trayecto_de_sol2[ind])
            else:
                trayecto_de_h1.append(None)
                trayecto_de_h2.append(None)
                indices_no_agregados.append(ind)
        else:            
            trayecto_de_h1.append(None)
            trayecto_de_h2.append(None)         
            indices_no_agregados.append(ind)   
        ind += 1    
    # Se agregan las coordenadas faltantes de los padres, el hijo 1 del padre B y el hijo 2 del padre A
    for indice in indices_no_agregados:
        if trayecto_de_h1[indice] == None and trayecto_de_h2[indice] == None:
            ind = 0
            while ind < len(trayecto_de_sol1):
                if trayecto_de_sol2[ind] not in trayecto_de_h1:
                    trayecto_de_h1[indice] = trayecto_de_sol2[ind]
                ind += 1
            ind = 0
            while ind < len(trayecto_de_sol1):
                if trayecto_de_sol1[ind] not in trayecto_de_h2:
                    trayecto_de_h2[indice] = trayecto_de_sol1[ind]            
                ind += 1            

    # Se crea la primer solucion de acuerdo a la definicion establecida y del trayecto que se realizo anteriormente para el hijo 1
    num_camiones = len(sol1)
    num_nodos = len(trayecto_de_h1) + 1
    sol_hijo1 = []
    camion = 1
    nodos = 1
    while camion <= num_camiones:
        dimension = len(trayecto_de_h1)-1
        datos_camion = []
        trayecto_h1 = []
        trayecto_h1.append(deposito)              
        if dimension > 0:
            num_contenedores = random.randint(1, dimension)
        contenedores = 1
        while contenedores < num_contenedores:
            contenedor = trayecto_de_h1[0]
            trayecto_h1.append(contenedor)            
            trayecto_de_h1.remove(contenedor)
            contenedores += 1                                                         
        if camion == num_camiones and nodos < num_nodos:
            contenedores_faltantes = [coordenada for coordenada in trayecto_de_h1 if coordenada not in trayecto_h1]
            for contenedor in contenedores_faltantes:
                trayecto_h1.append(contenedor)
                trayecto_de_h1.remove(contenedor)
                nodos += 1
        
        trayecto_h1.append(deposito) 
        datos_camion.append(trayecto_h1)
        datos_camion.append(sol1[camion-1][1])
        hora_que_finalizo = generar_hora_aleatoria(sol1[camion-1][1], horario[1])
        datos_camion.append(hora_que_finalizo)
        sol_hijo1.append(datos_camion)
        dimension = dimension - contenedores               
        camion += 1  
    ind1 = Individuo(sol_hijo1, 0, 0, 0, 0, [0,None], 0)

    # Se crea la segunda solucion de acuerdo a la definicion establecida y del trayecto que se realizo anteriormente para el hijo 2
    num_camiones = len(sol2)
    num_nodos = len(trayecto_de_h2) + 1
    sol_hijo2 = []
    camion = 1
    nodos = 1
    while camion <= num_camiones:
        dimension = len(trayecto_de_h2)-1
        datos_camion = []
        trayecto_h2 = []
        trayecto_h2.append(deposito)              
        if dimension > 0:
            num_contenedores = random.randint(1, dimension)
        contenedores = 1
        while contenedores < num_contenedores:
            contenedor = trayecto_de_h2[0]
            trayecto_h2.append(contenedor)            
            trayecto_de_h2.remove(contenedor)
            contenedores += 1                                                 
        
        if camion == num_camiones and nodos < num_nodos:
            contenedores_faltantes = [coordenada for coordenada in trayecto_de_h2 if coordenada not in trayecto_h2]
            for contenedor in contenedores_faltantes:
                trayecto_h2.append(contenedor)
                trayecto_de_h2.remove(contenedor)
                nodos += 1        
        trayecto_h2.append(deposito) 
        datos_camion.append(trayecto_h2)
        datos_camion.append(sol2[camion-1][1])
        hora_que_finalizo = generar_hora_aleatoria(sol2[camion-1][1], horario[1])
        datos_camion.append(hora_que_finalizo)
        sol_hijo2.append(datos_camion)
        dimension = dimension - contenedores               
        camion += 1  
    ind2 = Individuo(sol_hijo2, 0, 0, 0, 0, [0,None], 0)

    return ind1, ind2

# Realiza la mutacion de un individuo, con probabilidad pc => [0.01-0.1]
def mutacion(solucion, pm):
    trayecto_de_sol = []
    # Recupera el trayecto de los camiones a los contenedores, sin contar al deposito
    for camion in solucion:
        trayecto = camion[0]
        deposito = trayecto[0]
        contenedor = 1
        while trayecto[contenedor] != deposito:
            trayecto_de_sol.append(trayecto[contenedor])
            contenedor += 1
    
    # Se intercambia la ubicacion de dos contenedores, para establecer un recorrido diferente
    i = 0
    while i < len(trayecto_de_sol):
        if np.random.rand() <= pm:
            temp = trayecto_de_sol[i]
            pos_random = random.randint(i, len(trayecto_de_sol)-1)
            trayecto_de_sol[i] = trayecto_de_sol[pos_random]
            trayecto_de_sol[pos_random] = temp                         
        i += 1
    
    # Se actualizan los nuevos recorridos de cada camion
    deposito = solucion[0][0][0]
    camion = 0
    ind = 0
    while camion < len(solucion):
        i = 0
        while i < len(solucion[camion][0]):              
            if solucion[camion][0][i] != deposito:
                solucion[camion][0][i] = trayecto_de_sol[ind]
                ind += 1
            i += 1     
        camion += 1   
    mut = Individuo(solucion, 0, 0, 0, 0, [0,None], 0)
    
    return mut

# Elimina las sublistas vacias de una lista
def limpiar_lista(lista):    
    lista = [sublista for sublista in lista if sublista]
    return lista 

# Obtiene el promedio de una poblacion de acuerdo a la evaluacion de cada individuo
def promedio(poblacion):
    suma_aptitudes = 0
    for i in poblacion:
        suma_aptitudes += i.evaluacion
    y_promedio.append(suma_aptitudes/len(poblacion))

# Ordena la poblacion de acuerdo al ordenamiento no determinado, non-determinated sorting, regresando una lista de sublistas de indices de las 
# ubicaciones de los individuos, de donde deberan de estar ubicados
# A(x1|y1) domina a B(x2|y2) cuando:
# (x1 ≤ x2 y y1 ≤ y2) y (x1 < x2 o y1 < y2)
def ordenamiento_no_determinado(poblacion):
    # Se calcula lo dominacion de cada individuo
    i = 0    
    while i < len(poblacion):     
        dominados = []   
        j = 0
        while j < len(poblacion):              
            if poblacion[i] != poblacion[j]:
                if (poblacion[i].evaluacion_trayecto >= poblacion[j].evaluacion_trayecto and poblacion[i].evaluacion_carga >= poblacion[j].evaluacion_carga and poblacion[i].evaluacion_tiempo >= poblacion[j].evaluacion_tiempo) and (poblacion[i].evaluacion_trayecto > poblacion[j].evaluacion_trayecto or poblacion[i].evaluacion_carga > poblacion[j].evaluacion_carga or poblacion[i].evaluacion_tiempo > poblacion[j].evaluacion_tiempo):                    
                    dominados.append(j)
                    dominacion = list(poblacion[i].dominacion)
                    poblacion[i] = poblacion[i]._replace(dominacion=[dominacion[0], dominados])  
                    dominacion = list(poblacion[j].dominacion)
                    contador_dominaciones = dominacion[0]+1                    
                    poblacion[j] = poblacion[j]._replace(dominacion=[contador_dominaciones, dominacion[1]])                                        
            j += 1
        i += 1

    # Se crea el primer rango
    rango_k = []
    cont_ind = 0    
    i = 0
    while i < len(poblacion):
        dominacion = list(poblacion[i].dominacion)
        if dominacion[0] == 0:
            rango_k.append(i)
            cont_ind += 1
        i += 1
    rangos = []
    rangos.append(rango_k)

    # Se crean los demas rangos
    crea_rango = True
    iter = 0
    while crea_rango and iter < 100:            
        rango_n = []                
        i = 0
        while i < len(poblacion):            
            for j in rango_k:   
                if poblacion[i] != poblacion[j]:     
                    dominacion_j = list(poblacion[j].dominacion)                
                    if dominacion_j[1] is not None and i in dominacion_j[1]:
                        dominacion_i = list(poblacion[i].dominacion)
                        contador_dominaciones = dominacion_i[0]-1                    
                        poblacion[i] = poblacion[i]._replace(dominacion=[contador_dominaciones, dominacion_i[1]])
                        if contador_dominaciones == 0:
                            rango_n.append(i)
                            cont_ind += 1
                j += 1
            i += 1
        rangos.append(rango_n)
        if cont_ind == len(poblacion):
            break
        rango_k = rango_n 
        iter += 1   
    rangos = limpiar_lista(rangos)    

    return rangos

# Ordena la poblacion de acuerdo al ordenamiento por distancia de aglomeracion, crowding distance sorting
def ordenamiento_por_distancia_de_aglomeracion(poblacion, rangos, capacidad):
    # Por cada individuo de los rangos se obtiene la distancia de aglomeracion y se ordena cada rango de acuerdo a esa distancia
    indice_pob = 0
    for rango in rangos:
        rango_de_poblacion = []
        indice = indice_pob
        # Se recupera los individuos de un rango
        for ind in rango:
            rango_de_poblacion.append(poblacion[indice])
            indice += 1

        # Se ordena el rango de acuerdo a la evaluacion de cada individuo
        rango_de_poblacion = sorted(rango_de_poblacion, key=lambda individuo: evaluar_individuo(individuo, capacidad).evaluacion)    

        # Se calcula la distancia de aglomeracion de cada individuo del rango
        rango_de_poblacion[0] = rango_de_poblacion[0]._replace(distancia=math.inf)        
        rango_de_poblacion[len(rango_de_poblacion)-1] = rango_de_poblacion[len(rango_de_poblacion)-1]._replace(distancia=math.inf)        
        ind = 0
        while ind < len(rango_de_poblacion):
            if rango_de_poblacion[ind] is not rango_de_poblacion[0] and rango_de_poblacion[ind] is not rango_de_poblacion[len(rango_de_poblacion)-1]:
                distancia_ind = poblacion[ind].distancia
                if rango_de_poblacion[len(rango_de_poblacion)-1].evaluacion - rango_de_poblacion[0].evaluacion != 0:
                    rango_de_poblacion[ind] = rango_de_poblacion[ind]._replace(distancia=distancia_ind+(rango_de_poblacion[ind+1].evaluacion - rango_de_poblacion[ind-1].evaluacion)/(rango_de_poblacion[len(rango_de_poblacion)-1].evaluacion - rango_de_poblacion[0].evaluacion))                                
            ind += 1

        # Se ordena el rango de acuerdo a la distancia de aglomeracion de cada individuo
        rango_de_poblacion = sorted(rango_de_poblacion, key=lambda individuo: individuo.distancia, reverse=True)

        # Se actualiza el nuevo orden de ese rango en la poblacion
        for individuo in rango_de_poblacion:
            poblacion[indice_pob] = individuo
            indice_pob += 1
    
    return poblacion

# Obtiene el mejor individuo de cierto rango
def obtiene_mejor_individuo_del_rango(rango):    
    mejor_individuo = Individuo(None, math.inf, 0, 0, 0, [0,None], 0)    
    iter = 0
    for individuo in rango:
        if iter == 0:
            mejor_individuo = individuo
        elif individuo.evaluacion < mejor_individuo.evaluacion:
            mejor_individuo = individuo
        iter += 1
    return mejor_individuo

# Obtiene el peor individuo de cierto rango
def obtiene_peor_individuo_del_rango(rango):    
    peor_individuo = Individuo(None, 0, 0, 0, 0, [0,None], 0)    
    iter = 0
    for individuo in rango:
        if iter == 0:
            peor_individuo = individuo
        elif individuo.evaluacion > peor_individuo.evaluacion:
            peor_individuo = individuo
        iter += 1
    return peor_individuo

# Aplica el algoritmo NSGA-II de acuerdo a los datos que se reciben
def alg_NSGA2(num_nodos, num_camiones, coordenadas, horario, capacidad):    
    mejor_solucion = Individuo(None, 0, 0, 0, 0, [0,None], 0)
    peor_solucion = Individuo(None, 0, 0, 0, 0, [0,None], 0)            

    # Inicializa poblacion
    poblacion = genera_poblacion(int(num_nodos), int(num_camiones), coordenadas, horario)    

    gen = 0
    while gen < 100:
        mejor_solucion_actual = Individuo(None, 0, 0, 0, 0, [0,None], 0)
        peor_solucion_actual = Individuo(None, 0, 0, 0, 0, [0,None], 0)
        print(f'Generación = {gen+1}')
        # Se agregan individuos a la poblacion
        iter = 0
        while iter < 50:
            # Evaluacion de la poblacion
            evaluar_poblacion(poblacion, int(capacidad))            
            # Seleccion por torneo de padres    
            padre1, padre2 = seleccion_por_torneo(poblacion, int(capacidad))
            # Cruza de permutaciones
            hijo1, hijo2 = cruza_de_permutaciones(poblacion[padre1].solucion, poblacion[padre2].solucion, random.uniform(0.6, 0.9))
            # Mutacion de los hijos
            hijo1 = mutacion(hijo1.solucion, random.uniform(0.01, 0.1))
            hijo2 = mutacion(hijo2.solucion, random.uniform(0.01, 0.1))
            # Se agregan los hijos a la poblacion
            poblacion.append(hijo1)
            poblacion.append(hijo2)
            iter += 1  
        tamanio_poblacion = len(poblacion)

        # Evaluacion de la poblacion
        evaluar_poblacion(poblacion, int(capacidad))        
        # Aplica ordenamiento no determinado a la poblacion
        orden_indices = ordenamiento_no_determinado(poblacion)                  
        copia_poblacion = poblacion
        ind = 0
        # Ordena la poblacion de acuerdo a la lista de indices que se obtuvo
        for rango in orden_indices:
            for indice in rango:
                poblacion[ind] = copia_poblacion[indice]
                ind += 1        
        # Aplica ordenamiento por distancia de aglomeracion a la poblacion
        poblacion = ordenamiento_por_distancia_de_aglomeracion(poblacion, orden_indices, capacidad)    
        # Se eliminan los ultimos elementos de la poblacion
        copia_poblacion = poblacion.copy()
        ind = 0
        while ind < tamanio_poblacion:
            if ind >= tamanio_poblacion/2:
                poblacion.remove(copia_poblacion[ind])            
            ind += 1
        
        mejores_de_rangos = []
        peores_de_rangos = []
        inicio = 0
        # Se obtiene el mejor y el peor de cada rango
        for rango in orden_indices:
            mejor = obtiene_mejor_individuo_del_rango(poblacion[inicio:inicio+len(rango)-1])            
            mejores_de_rangos.append(mejor)
            peor = obtiene_peor_individuo_del_rango(poblacion[inicio:inicio+len(rango)-1])            
            peores_de_rangos.append(peor)
            inicio = len(rango)-1          

        # Se busca el mejor de la generacion
        for individuo in mejores_de_rangos:
            if gen == 1:
                mejor_solucion = individuo               
            if mejor_solucion_actual.evaluacion == 0:
                mejor_solucion_actual = individuo                 
            if individuo.evaluacion < mejor_solucion_actual.evaluacion:
                mejor_solucion_actual = individuo
        y_mejor_actual.append(mejor_solucion_actual.evaluacion)

        # Se actualiza la mejor solucion encontrada
        if mejor_solucion_actual.evaluacion < mejor_solucion.evaluacion:
            mejor_solucion = mejor_solucion_actual
        y_mejor.append(mejor_solucion.evaluacion)

        # Se busca el peor de la generacion
        for individuo in peores_de_rangos:
            if gen == 1:
                peor_solucion = individuo               
            if peor_solucion_actual.evaluacion == 0:
                peor_solucion_actual = individuo        
            if individuo.evaluacion > peor_solucion_actual.evaluacion:
                peor_solucion_actual = individuo
        y_peor_actual.append(peor_solucion_actual.evaluacion)

        # Se actualiza la peor solucion encontrada
        if peor_solucion_actual.evaluacion > peor_solucion.evaluacion:
            peor_solucion = peor_solucion_actual
        y_peor.append(peor_solucion.evaluacion)

        # Se obtiene el promedio de la evaluacion de los individuos de la poblacion
        promedio(poblacion)
        gen += 1

    # Recupera las evaluaciones de cada individuo de la poblacion final
    for individuo in poblacion:
        trayectos_soluciones.append(individuo.evaluacion_trayecto)
        cargas_soluciones.append(individuo.evaluacion_carga)
        tiempos_soluciones.append(individuo.evaluacion_tiempo)

    # Se agrega las evaluaciones de la mejor solucion que se haya encontrado durante todo el proceso
    if mejor_solucion != mejor_solucion_actual:
        trayectos_soluciones.append(mejor_solucion.evaluacion_trayecto)
        cargas_soluciones.append(mejor_solucion.evaluacion_carga)
        tiempos_soluciones.append(mejor_solucion.evaluacion_tiempo)

    return mejor_solucion

# Función para generar un nombre de archivo único
def obtener_nombre(base_name, extension, nombre_archivo):
    ruta = './output'      
    os.makedirs(ruta,exist_ok=True)  
    carpeta_rem = f'{nombre_archivo}-Graficas' 
    ruta_carpeta = os.path.join(ruta, carpeta_rem)
    counter = 1
    filename = f"{base_name}{extension}"
    while os.path.exists(f'{ruta_carpeta}/{filename}'):
        filename = f"{base_name}_{counter}{extension}"
        counter += 1
    return filename

def alg_NSGA2(num_nodos, num_camiones, coordenadas, horario, capacidad):
    # Esta función debería contener el bucle principal del algoritmo
    # que estaba en tu `alg_NSGA2.py` y devolver la población final.
    # Asegúrate de que no use variables globales para guardar el estado.
    poblacion = genera_poblacion(int(num_nodos), int(num_camiones), coordenadas, horario)
    
    # Bucle de generaciones (simplificado)
    gen = 0
    while gen < 100:
        # Aquí iría la lógica de selección, cruza, mutación, etc.
        evaluar_poblacion(poblacion, int(capacidad))
        # ... más lógica
        gen += 1
        
    return poblacion

# --- Generación de Gráficas y Punto de Entrada ---
def generar_graficas_y_subir(final_population, blob_service_client, container_name):
    urls = {}
    # ... (Tu código de `generar_graficas_y_subir` va aquí) ...
    return urls

def run_nsga2(input_data):
    """Punto de entrada principal para ejecutar el algoritmo."""
    nodos = input_data.get('nodes')
    capacidad_vehiculo = input_data.get('vehicleCapacity')
    ventana_tiempo = input_data.get('timeWindow')

    num_nodos, num_camiones, capacidad, coordenadas, horario = preparar_datos_para_algoritmo(nodos, capacidad_vehiculo, ventana_tiempo)
    
    # Ejecutar el algoritmo
    poblacion_final = alg_NSGA2(num_nodos, num_camiones, coordenadas, horario, capacidad)

    # Serializar la población para la respuesta JSON
    pareto_front_json = []
    for i, individuo in enumerate(poblacion_final):
        rutas_serializadas = []
        if hasattr(individuo, 'solucion') and individuo.solucion:
            for camion in individuo.solucion:
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

    coordenadas_nodos_dict = {nodo['id']: (nodo['lat'], nodo['lng']) for nodo in nodos}

    # Aquí podrías añadir la lógica para subir las gráficas si es necesario
    urls_imagenes = {}
    # if 'blob_connection_string' in input_data:
    #     blob_service_client = BlobServiceClient.from_connection_string(...)
    #     urls_imagenes = generar_graficas_y_subir(...)

    result = {
        "ejemplarId": f"AZURE-VRP-001",
        "paretoFront": pareto_front_json,
        "coordenadas_nodos": coordenadas_nodos_dict,
        "insightImages": urls_imagenes
    }
    return result