import tkinter as tk
import random
import threading
import time

# Configuración de la memoria
MEMORIA_TOTAL = 1000  # Memoria total disponible (en MB)
MEMORIA_USADA = 0  # Memoria actualmente en uso (en MB)
TAMANO_PAGINA = 10  # Tamaño de cada página en MB
NUMERO_PAGINAS = MEMORIA_TOTAL // TAMANO_PAGINA  # Cantidad total de páginas en memoria
paginas_memoria = [None] * NUMERO_PAGINAS  # Tabla de páginas para la memoria

# Lista de procesos en diferentes estados
procesos = []
procesos_nuevos = []
procesos_listos = []
procesos_bloqueados = []
procesos_terminados = []
recursos_semaforos = [threading.Semaphore(1), threading.Semaphore(1), threading.Semaphore(1)]  # Semáforos para los recursos R0, R1, R2
procesos_ocupando_recurso = [None, None, None]  # Lista para rastrear qué proceso tiene cada recurso
proceso_ejecucion = None

# Clase para representar un proceso
class Proceso:
    def __init__(self, id, memoria):
        self.id = id
        self.memoria = memoria
        self.estado = 'Nuevos'
        self.veces_bloqueado = 0  # Atributo para contar las veces que ha sido bloqueado
        self.recurso = random.randint(0, 2)  # Asigna aleatoriamente R0, R1 o R2
        self.paginas = []  # Páginas asignadas en la memoria principal
        self.tiene_recurso = False  # Indica si este proceso tiene bloqueado un recurso

    def __str__(self):
        return f"P{self.id}: ({self.memoria} MB) Recurso: R{self.recurso}"

# Función para mover un proceso de Listo a Ejecutando
def mover_a_ejecutando():
    global proceso_ejecucion
    while True:
        if not proceso_ejecucion and procesos_listos:
            proceso = procesos_listos.pop(0)
            proceso_ejecucion = proceso
            proceso.estado = 'Ejecutando'
            actualizar_interfaz()

            # Intentar bloquear el recurso necesario para este proceso
            if not proceso.tiene_recurso:
                if recursos_semaforos[proceso.recurso].acquire(blocking=False):  # Intentar adquirir el recurso
                    proceso.tiene_recurso = True
                    procesos_ocupando_recurso[proceso.recurso] = proceso.id
                    actualizar_interfaz()

            # Probabilidad del 20% de que el proceso se quede en ejecución y pase directamente a terminado
            if random.random() < 0.2:
                time.sleep(5)  # Ejecución de 5 segundos
                proceso.estado = 'Terminado'
                procesos_terminados.append(proceso)
                liberar_paginas(proceso)
                eliminar_proceso_terminado_de_memoria()
                liberar_recurso(proceso)
                actualizar_interfaz()
            else:
                # Simulación normal de ejecución
                time.sleep(2)  # Ejecución de 2 segundos
                
                # Verificar si ha sido bloqueado menos de 3 veces
                if proceso.veces_bloqueado < 3:
                    proceso.veces_bloqueado += 1
                    proceso.estado = 'Bloqueado'
                    procesos_bloqueados.append(proceso)
                else:
                    # Si ha sido bloqueado 3 veces, pasa a terminado
                    proceso.estado = 'Terminado'
                    procesos_terminados.append(proceso)
                    liberar_paginas(proceso)
                    eliminar_proceso_terminado_de_memoria()
                    liberar_recurso(proceso)
                    actualizar_interfaz()
            
            proceso_ejecucion = None
            actualizar_interfaz()
        time.sleep(2)


# Función para eliminar un proceso terminado de la memoria gráfica
# Función para eliminar un proceso terminado de la memoria gráfica
def eliminar_proceso_terminado_de_memoria():
    global MEMORIA_USADA
    for proceso in procesos_terminados:
        if proceso.paginas:  # Verifica si el proceso aún tiene páginas asignadas en memoria
            for pagina in proceso.paginas:
                paginas_memoria[pagina] = None  # Libera la página en memoria
                MEMORIA_USADA -= TAMANO_PAGINA
            proceso.paginas = []  # Vacía las páginas asignadas al proceso
            actualizar_interfaz()  # Actualiza la interfaz gráfica
            mostrar_procesos_en_memoria()  # Refresca la visualización en el canvas


# Función para revisar procesos bloqueados y moverlos a Listo cuando corresponda
def revisar_procesos_bloqueados():
    while True:
        for proceso in procesos_bloqueados[:]:
            if proceso.tiene_recurso:
                # Si el proceso tiene un recurso, pasa a Listo después de 3 segundos
                time.sleep(1)  # Esperar 3 segundos
                proceso.estado = 'Listo'
                procesos_bloqueados.remove(proceso)
                procesos_listos.append(proceso)
                actualizar_interfaz()
            else:
                # Si el proceso no tiene el recurso, intentar adquirirlo
                if recursos_semaforos[proceso.recurso].acquire(blocking=False):  # Intentar adquirir el recurso
                    proceso.tiene_recurso = True
                    procesos_ocupando_recurso[proceso.recurso] = proceso.id
                    proceso.estado = 'Listo'
                    procesos_bloqueados.remove(proceso)
                    procesos_listos.append(proceso)
                    actualizar_interfaz()
        time.sleep(2)

# Función de compactación de memoria
# Función de compactación de memoria ajustada
def compactar_memoria():
    # Crear una nueva lista para la memoria compactada
    memoria_compactada = [pagina for pagina in paginas_memoria if pagina is not None]
    
    # Rellenar el resto de la lista con None (espacios vacíos)
    memoria_compactada.extend([None] * (NUMERO_PAGINAS - len(memoria_compactada)))
    
    # Actualizar la lista de memoria con la versión compactada
    for i in range(NUMERO_PAGINAS):
        paginas_memoria[i] = memoria_compactada[i]
    
    # Actualizar las referencias de páginas en cada proceso en memoria
    for proceso in procesos:
        proceso.paginas = [i for i, p_id in enumerate(paginas_memoria) if p_id == proceso.id]

    # Actualizar la interfaz gráfica después de compactar
    actualizar_interfaz()

# Función para liberar las páginas asignadas a un proceso
def liberar_paginas(proceso):
    global MEMORIA_USADA
    for pagina in proceso.paginas:
        paginas_memoria[pagina] = None
        MEMORIA_USADA -= TAMANO_PAGINA
    proceso.paginas = []
    actualizar_interfaz()
    time.sleep(2)
    compactar_memoria()  # Llamar a la compactación cada vez que se libera memoria

# Función para asignar páginas a un proceso en la memoria
def asignar_paginas(proceso):
    global MEMORIA_USADA # Asegurar que la memoria está compactada antes de asignar
    paginas_necesarias = (proceso.memoria + TAMANO_PAGINA - 1) // TAMANO_PAGINA  # Redondeo hacia arriba

    if paginas_memoria.count(None) >= paginas_necesarias:
        for i in range(NUMERO_PAGINAS):
            if len(proceso.paginas) == paginas_necesarias:
                break
            if paginas_memoria[i] is None:
                paginas_memoria[i] = proceso.id
                proceso.paginas.append(i)
                MEMORIA_USADA += TAMANO_PAGINA

        return True
    else:
        return False

# Función para liberar el recurso asignado a un proceso
def liberar_recurso(proceso):
    if proceso.tiene_recurso:
        recursos_semaforos[proceso.recurso].release()
        procesos_ocupando_recurso[proceso.recurso] = None
        proceso.tiene_recurso = False
        actualizar_interfaz()

# Función para agregar un proceso
def agregar_proceso(memoria_necesaria):
    proceso = Proceso(len(procesos) + 1, memoria_necesaria)
    procesos_nuevos.append(proceso)
    proceso.estado = 'Listos'
    procesos.append(proceso)
    actualizar_interfaz()

# Función para mover procesos de Nuevos a Listos
def nuevo_a_listo():
    while True:
        for proceso in procesos_nuevos[:]:
            if asignar_paginas(proceso):
                procesos_nuevos.remove(proceso)
                procesos_listos.append(proceso)
                proceso.estado = 'Listo'
                actualizar_interfaz()
        time.sleep(3)

# Función para agregar un proceso manualmente
def agregar_proceso_manual():
    try:
        memoria_necesaria = int(memoria_entry.get())
        if memoria_necesaria > 0:
            agregar_proceso(memoria_necesaria)
        else:
            tk.messagebox.showerror("Error", "La memoria debe ser un número positivo.")
    except ValueError:
        tk.messagebox.showerror("Error", "Ingrese un valor numérico válido para la memoria.")
    finally:
        memoria_entry.delete(0, tk.END)  # Limpiar el campo de entrada

# Función para agregar un proceso aleatorio
def agregar_proceso_aleatorio():
    memoria_necesaria = random.randint(50, 200)
    agregar_proceso(memoria_necesaria)

# Función para actualizar la interfaz gráfica
def actualizar_interfaz():
    memoria_label.config(text=f"Memoria Usada: {MEMORIA_USADA}/{MEMORIA_TOTAL} MB")
    ejecucion_label.config(text=f"Ejecutando: {proceso_ejecucion if proceso_ejecucion else 'Ninguno'}")
 

    # Limpiar y actualizar lista de procesos
    nuevos_listbox.delete(0, tk.END)
    for p in procesos_nuevos:
        nuevos_listbox.insert(tk.END, str(p))

    listos_listbox.delete(0, tk.END)
    for p in procesos_listos:
        listos_listbox.insert(tk.END, str(p))

    bloqueados_listbox.delete(0, tk.END)
    for p in procesos_bloqueados:
        bloqueados_listbox.insert(tk.END, str(p))

    terminados_listbox.delete(0, tk.END)
    for p in procesos_terminados:
        terminados_listbox.insert(tk.END, str(p))

    # Mostrar procesos en memoria
    mostrar_procesos_en_memoria()

    # Actualizar estado de los recursos
    actualizar_estado_recursos()

# Función para mostrar visualmente el uso de la memoria
# Función para mostrar visualmente el uso de la memoria
def mostrar_procesos_en_memoria():
    canvas.delete("all")  # Limpiar el canvas

    # Calcular el ancho de cada columna dinámicamente
    ancho_columna = canvas.winfo_width() // NUMERO_PAGINAS  # Ancho de cada columna

    colores_procesos = ["lightblue", "lightgreen", "lightcoral", "lightyellow", "lightpink"]  # Lista de colores

    for i in range(NUMERO_PAGINAS):
        x0, y0 = (i * ancho_columna), 0
        x1, y1 = x0 + ancho_columna, 100

        proceso_id = paginas_memoria[i]
        if proceso_id is not None:
            color = colores_procesos[proceso_id % len(colores_procesos)]
            canvas.create_rectangle(x0, y0, x1, y1, fill=color)
        else:
            # Dibuja un espacio vacío en blanco o gris claro para indicar la ausencia de proceso
            canvas.create_rectangle(x0, y0, x1, y1, fill="white", outline="lightgray")
    
    # Lógica para asignaciones discontiguas
    procesos_dibujados = set()
    for i in range(NUMERO_PAGINAS):
        proceso_id = paginas_memoria[i]
        if proceso_id and proceso_id not in procesos_dibujados:
            procesos_dibujados.add(proceso_id)
            inicio = i
            while i < NUMERO_PAGINAS and paginas_memoria[i] == proceso_id:
                i += 1
            fin = i
            x0, x1 = (inicio * ancho_columna), (fin * ancho_columna)
            color = colores_procesos[proceso_id % len(colores_procesos)]
            canvas.create_rectangle(x0, 110, x1, 115, fill=color, outline=color)
            canvas.create_text((x0 + (x1 - x0) / 2, 112.5), text=f"P{proceso_id}", anchor='center', font=("Arial", 8))


# Función para actualizar el estado de los recursos
def actualizar_estado_recursos():
    for i, recurso in enumerate(["R0", "R1", "R2"]):
        estado = f"{recurso}: {'Libre' if procesos_ocupando_recurso[i] is None else f'Ocupado por P{procesos_ocupando_recurso[i]}'}"
        recurso_labels[i].config(text=estado)

# Configuración de la interfaz gráfica
ventana = tk.Tk()
ventana.title("Simulación de Procesos y Memoria")

frame_principal = tk.Frame(ventana)
frame_principal.pack(padx=10, pady=10)

# Widgets de memoria y procesos
memoria_label = tk.Label(frame_principal, text=f"Memoria Usada: {MEMORIA_USADA}/{MEMORIA_TOTAL} MB", font=("Arial", 14))
memoria_label.pack()

canvas_frame = tk.Frame(frame_principal)
canvas_frame.pack(pady=10)

canvas = tk.Canvas(canvas_frame, width=500, height=125, bg="white")
canvas.pack()

# Estado de ejecución y mensajes
ejecucion_label = tk.Label(frame_principal, text=f"Ejecutando: Ninguno", font=("Arial", 14))
ejecucion_label.pack(pady=(10, 5))  # Espacio adicional debajo para centrar mejor

# Control Frame para agregar procesos manualmente y aleatorios, ahora debajo del proceso en ejecución
control_frame = tk.Frame(frame_principal)
control_frame.pack(pady=10)

memoria_entry = tk.Entry(control_frame)
memoria_entry.pack(side=tk.LEFT, padx=(0, 5))

agregar_btn = tk.Button(control_frame, text="Agregar Proceso", command=agregar_proceso_manual)
agregar_btn.pack(side=tk.LEFT, padx=(5, 0))

agregar_aleatorio_btn = tk.Button(control_frame, text="Agregar Proceso Aleatorio", command=agregar_proceso_aleatorio)
agregar_aleatorio_btn.pack(side=tk.LEFT, padx=(5, 0))

# Crear un contenedor para los listboxes de los estados de los procesos y centrarlo
estados_frame = tk.Frame(frame_principal)
estados_frame.pack(pady=10)

# Configuración de listas para los estados de los procesos
nuevos_frame = tk.Frame(estados_frame)
nuevos_frame.grid(row=0, column=0, padx=10)
nuevos_label = tk.Label(nuevos_frame, text="Nuevos")
nuevos_label.pack()
nuevos_listbox = tk.Listbox(nuevos_frame, width=30, height=10)
nuevos_listbox.pack()

listos_frame = tk.Frame(estados_frame)
listos_frame.grid(row=0, column=1, padx=10)
listos_label = tk.Label(listos_frame, text="Listos")
listos_label.pack()
listos_listbox = tk.Listbox(listos_frame, width=30, height=10)
listos_listbox.pack()

bloqueados_frame = tk.Frame(estados_frame)
bloqueados_frame.grid(row=0, column=2, padx=10)
bloqueados_label = tk.Label(bloqueados_frame, text="Bloqueados")
bloqueados_label.pack()
bloqueados_listbox = tk.Listbox(bloqueados_frame, width=30, height=10)
bloqueados_listbox.pack()

terminados_frame = tk.Frame(estados_frame)
terminados_frame.grid(row=0, column=3, padx=10)
terminados_label = tk.Label(terminados_frame, text="Terminados")
terminados_label.pack()
terminados_listbox = tk.Listbox(terminados_frame, width=30, height=10)
terminados_listbox.pack()

# Crear un frame para el estado de los recursos, a la derecha de "Terminados"
recursos_frame = tk.Frame(estados_frame)
recursos_frame.grid(row=0, column=4, padx=10)

recursos_label = tk.Label(recursos_frame, text="Estado de Recursos", font=("Arial", 12))
recursos_label.pack()

# Labels para mostrar el estado de cada recurso
recurso_labels = []
for i in range(3):
    label = tk.Label(recursos_frame, text=f"R{i}: Libre")
    label.pack()
    recurso_labels.append(label)

mensaje_error = tk.Label(ventana, text="", fg="red")
mensaje_error.pack()

# Iniciar los hilos para simular los procesos
threading.Thread(target=nuevo_a_listo, daemon=True).start()
threading.Thread(target=revisar_procesos_bloqueados, daemon=True).start()
threading.Thread(target=mover_a_ejecutando, daemon=True).start()

# Ejecutar la ventana de la interfaz gráfica
ventana.mainloop()
