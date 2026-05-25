from heartrate_monitor import HeartRateMonitor
import time

# Imprimir un mensaje indicando que el sensor está iniciando
print('sensor starting...')

# Establecer la duración durante la cual se leerán los datos del sensor (en segundos)
duration = 30

# Inicializar el objeto HeartRateMonitor
# Establecer print_raw en False para evitar imprimir datos crudos
# Establecer print_result en True para imprimir los resultados calculados
hrm = HeartRateMonitor(print_raw=False, print_result=True)

# Iniciar el sensor de frecuencia cardíaca
hrm.start_sensor()

try:
    time.sleep(duration)
except KeyboardInterrupt:
    print('keyboard interrupt detected, exiting...')

# Detener el sensor después de que haya transcurrido la duración
hrm.stop_sensor()

# Imprimir un mensaje indicando que el sensor se ha detenido
print('sensor stopped!')