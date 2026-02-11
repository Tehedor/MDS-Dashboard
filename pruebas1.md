🧩 PASO 0 — Comprueba que el archivo está en su sitio

El archivo que acabas de copiar debe estar aquí:

<tu_proyecto>/
└── utils/
    └── dataset/
        └── SubDataset.py   👈 ESTE


⚠️ El nombre tiene que ser exactamente SubDataset.py.

🧩 PASO 1 — Abre una terminal en el proyecto

Abre una terminal

Ve al directorio raíz del proyecto (donde está app.py)

Ejemplo:

cd ~/Work/tfm/tu_proyecto


Si dudas, ejecuta:

ls


Y deberías ver algo como:

app.py  utils/  layouts/  callbacks/  Datasets/

🧩 PASO 2 — Exporta la variable de entorno (OBLIGATORIO)

En esa misma terminal, ejecuta:

export EPOCH_PROCESSED_DIR=./epoch_processed


Para comprobar que se ha exportado bien:

echo $EPOCH_PROCESSED_DIR


Debe imprimir:

./epoch_processed


📌 Esto solo vale para esta terminal (está bien).

🧩 PASO 3 — Arranca Python en modo interactivo

En la misma terminal, ejecuta:

python3


Deberías ver algo así:

Python 3.10.x (default, ...)
>>> 


Ese >>> es donde vamos a escribir ahora.

🧩 PASO 4 — Importa SubDataset

Copia y pega tal cual:

from pathlib import Path
from utils.dataset.SubDataset import SubDataset


Si NO aparece ningún error, vamos bien ✅

Si aparece un error rojo, párate ahí y dímelo.

🧩 PASO 5 — Crea un SubDataset de Epoch (PRUEBA CLAVE)

Ahora copia y pega esto, cambiando SOLO la ruta del parquet:

sd = SubDataset(
    name="Epoch-Dataset-v013",
    root=Path("."),
    cfg={
        "type": "event-encoded",
        "path": "/home/tehe/Work/tfm/MLOps4OFP-APSE/executions/02_prepareeventsds/v013/02_prepareeventsds_dataset.parquet",
        "timestamp_col": "segs"
    }
)


👉 Pulsa Enter.

Si todo va bien, no pasa nada visible (esto es correcto).

🧩 PASO 6 — Carga el parquet raw (PRUEBA 1)

Ahora copia y pega:

df_raw = sd.load_df()


Luego:

df_raw.head()


Deberías ver algo parecido a:

       segs    events
0  1651363201  []
1  1651363211  []
...


Si esto pasa → PARQUET CARGADO BIEN ✅

🧩 PASO 7 — Intenta procesar Epoch (PRUEBA 2)

Ahora copia y pega:

sd.load_or_process_epoch()

Resultado ESPERADO (IMPORTANTE)

Debe salir un error como este:

NotImplementedError: Procesamiento Epoch pendiente de implementar


📌 ESTO ES BUENO
📌 Significa que:

ha intentado procesar

ha creado el directorio epoch_processed/

ha llegado justo al punto correcto

🧩 PASO 8 — Comprueba que se creó el directorio

Sal de Python:

exit()


Y en la terminal:

ls epoch_processed


Deberías ver:

Epoch-Dataset-v013/


Y dentro:

ls epoch_processed/Epoch-Dataset-v013


Si está vacío → perfecto (aún no guardamos nada).