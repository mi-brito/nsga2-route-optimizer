import csv
import math

def ObtenerMedia(conj):
    suma = 0
    for i in conj:
        suma += float(i)
    return suma/len(conj)

def ObtenerMediana(conj):
    n = len(conj)
    return (float(conj[n//2 - 1]) + float(conj[n//2])) / 2

ejemplar = ''
seleccionado_ejem = False
salir = False

while not(salir):
    while not(seleccionado_ejem):
        num = input(f"\nSelecciona un ejemplar, donde n (Cantidad de contenedores) y k (Cantidad de camiones):\n 1. A-n32-k5\n 2. A-n63-k10\n 3. E-n101-k14\n 4. M-n200-k17\n 5. X-n153-k22\n 6. Salir del programa\n")
        if num == '1':
            ejemplar = 'A-n32-k5'
            seleccionado_ejem = True
        elif num == '2':
            ejemplar = 'A-n63-k10'
            seleccionado_ejem = True
        elif num == '3':
            ejemplar = 'E-n101-k14'
            seleccionado_ejem = True
        elif num == '4':
            ejemplar = 'M-n200-k17'
            seleccionado_ejem = True
        elif num == '5':
            ejemplar = 'X-n153-k22'
            seleccionado_ejem = True
        elif num == '6':
            exit(0)
        else:
            num = ''

    archivo_csv = open(f'{ejemplar}.txt_resultados_NSGA2.csv', 'r')    
    lec = csv.reader(archivo_csv)
    mejores = []
    next(lec)
    for fila in lec:              
        mejores.append(fila[6])
    
    mejor = min(mejores)
    peor = max(mejores)
    media = ObtenerMedia(mejores)
    mediana = ObtenerMediana(mejores)
    suma_diferencias_cuadradas = sum((float(x) - media) ** 2 for x in mejores)
    desviacion_estandar = math.sqrt(suma_diferencias_cuadradas / len(mejores))

    print(f'Mejor = {mejor}')
    print(f'Peor = {peor}')
    print(f'Media = {media}')
    print(f'Mediana = {mediana}')
    print(f'Desviacion estandar = {desviacion_estandar}')

    seleccionado_ejem = False