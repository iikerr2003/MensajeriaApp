from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional, Union


class BaseLogger:
    """Clase base reutilizable para añadir capacidades de logging a otros módulos.

    Proporciona un objeto :class:`logging.Logger` configurado en ``self.logger`` y
    utilidades para ajustar nivel, formato y handlers sin modificar la configuración
    global mediante :func:`logging.basicConfig`.

    Ejemplo
    -------
    >>> class ServicioMensajes(BaseLogger):
    ...     def __init__(self):
    ...         super().__init__(name="servicio.mensajes", log_to_console=True)
    ...
    ...     def enviar(self, texto: str):
    ...         self.logger.info("Enviando %s", texto)
    >>> servicio = ServicioMensajes()
    >>> servicio.enviar("Hola")
    """

    DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        name: Optional[str] = None,
        level: int = logging.INFO,
        *,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        handlers: Optional[Iterable[logging.Handler]] = None,
        log_to_console: bool = True,
        propagate: bool = False,
    ) -> None:
        self.logger = logging.getLogger(name or self.__class__.__name__)
        self.logger.propagate = propagate
        self._formatter = logging.Formatter(fmt or self.DEFAULT_FORMAT, datefmt or self.DEFAULT_DATEFMT)

        self.set_level(level)

        if handlers:
            self._replace_handlers(handlers)
        else:
            self._ensure_default_handler(log_to_console)

    def _replace_handlers(self, handlers: Iterable[logging.Handler]) -> None:
        self._clear_handlers()
        for handler in handlers:
            if handler.formatter is None:
                handler.setFormatter(self._formatter)
            if handler.level == logging.NOTSET:
                handler.setLevel(self.logger.level)
            self.logger.addHandler(handler)

    def _ensure_default_handler(self, log_to_console: bool) -> None:
        if self.logger.handlers:
            return

        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self._formatter)
            console_handler.setLevel(self.logger.level)
            self.logger.addHandler(console_handler)

    def _clear_handlers(self) -> None:
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)

    def set_level(self, level: int) -> None:
        """Actualiza el nivel del logger y de todos sus handlers asociados."""

        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def add_console_handler(
        self,
        *,
        level: Optional[int] = None,
        formatter: Optional[logging.Formatter] = None,
        stream=None,
    ) -> logging.Handler:
        """Añade un handler de consola opcionalmente personalizado."""

        handler = logging.StreamHandler(stream=stream)
        handler.setLevel(level or self.logger.level)
        handler.setFormatter(formatter or self._formatter)
        self.logger.addHandler(handler)
        return handler

    def add_file_handler(
        self,
        file_path: Union[str, Path],
        *,
        level: Optional[int] = None,
        formatter: Optional[logging.Formatter] = None,
        mode: str = "a",
        encoding: str = "utf-8",
        delay: bool = False,
    ) -> logging.Handler:
        """Añade un handler que escribe a archivo, creando directorios si hace falta."""

        resolved_path = Path(file_path).expanduser().resolve()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(resolved_path, mode=mode, encoding=encoding, delay=delay)
        handler.setLevel(level or self.logger.level)
        handler.setFormatter(formatter or self._formatter)
        self.logger.addHandler(handler)
        return handler

    def get_child_logger(self, suffix: str) -> logging.Logger:
        """Devuelve un logger hijo reutilizando la configuración actual."""

        return self.logger.getChild(suffix)

    @property
    def log(self) -> logging.Logger:
        """Atajo para acceder al logger interno."""

        return self.logger
