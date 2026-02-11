# utils/cache_config.py
import atexit
import logging
import signal
from flask_caching import Cache

def init_cache(app):
    cache = Cache(app.server, config={
        "CACHE_TYPE": "SimpleCache",   # en memoria
        "CACHE_DEFAULT_TIMEOUT": 86400 # 24h
    })
    return cache

# --- Función para limpiar la caché ---
# def limpiar_cache(cache = None):
#     try:
#         cache.clear()
#         logging.info("🧹 Caché limpiada correctamente.")
#     except Exception as e:
#         logging.warning(f"No se pudo limpiar la caché: {e}")
def limpiar_cache(cache=None):
    if cache is None:
        logging.info("🧹 Caché no inicializada; se omite limpieza.")
        return
    try:
        cache.clear()
        logging.info("🧹 Caché limpiada correctamente.")
    except Exception as e:
        logging.warning(f"No se pudo limpiar la caché: {e}")

# --- Manejar Ctrl+C o SIGTERM ---
def handle_exit_signal(signum, frame):
    logging.info("🛑 Señal de cierre detectada. Limpiando caché...")
    limpiar_cache()
    exit(0)



def cache_config(cache):
    # cache = init_cache(app)

    # Registrar manejadores de señal para limpiar caché al salir
    signal.signal(signal.SIGINT, handle_exit_signal)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit_signal) # Terminación

    # Registrar limpieza de caché al salir normalmente
    atexit.register(limpiar_cache, cache)

    # return cache