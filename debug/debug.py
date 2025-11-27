# /debug/debug.oy
from pathlib import Path
import logging
from typing import Optional, Any

log = logging.getLogger("debug")

def save_debug_info(content_source: Any, filename: Optional[str] = "info_debug", directory: Optional[Path] = None, head: Optional[str] = None) -> Path:
    """
    Guarda en el directorio de debug el contenido de `content_source`.
    - content_source: DataFrame, callable que devuelve DataFrame/str, o cualquier objeto.
    - filename: nombre opcional (sin extensión o con). Por defecto "info_debug" -> "info_debug.txt".
    - directory: Path opcional; por defecto usa el mismo directorio donde está este archivo (debug/).
    - head: título opcional que se escribe encima del contenido (separado por una línea en blanco).
    Devuelve el Path al fichero escrito.
    """
    dir_path = Path(directory) if directory else Path(__file__).parent
    dir_path.mkdir(parents=True, exist_ok=True)

    out_name = filename if Path(filename).suffix else f"{filename}.txt"
    out_path = dir_path / out_name

    try:
        # Obtener contenido (si es callable, llamar)
        content = content_source() if callable(content_source) else content_source

        # Si es un DataFrame u objeto con to_string(), usarlo; si no, str()
        try:
            content_str = content.to_string()
        except Exception:
            content_str = str(content)

        # Añadir header/título si se proporciona
        if head:
            content_str = f"{head}\n\n{content_str}"

        out_path.write_text(content_str, encoding="utf-8")
        log.info("Info debug exportado a %s", out_path)
        return out_path
    except Exception:
        log.exception("Error exportando info debug a %s", out_path)
        raise