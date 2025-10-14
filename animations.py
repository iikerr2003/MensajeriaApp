"""Módulo de animaciones para transiciones suaves en la interfaz de usuario."""

from PyQt6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QRect, Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


class ChatAnimations:
    """Clase para gestionar animaciones de entrada/salida de chats."""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
        """Crea una animación de aparición gradual (fade in).

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 300).

        Returns
        -------
        QPropertyAnimation
            Animación configurada y lista para iniciar.
        """
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        return animation

    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
        """Crea una animación de desaparición gradual (fade out).

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 300).

        Returns
        -------
        QPropertyAnimation
            Animación configurada y lista para iniciar.
        """
        effect = widget.graphicsEffect()
        if not effect:
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)

        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        return animation

    @staticmethod
    def slide_in_from_right(
        widget: QWidget, duration: int = 400, distance: int = 300
    ) -> QPropertyAnimation:
        """Desliza el widget desde la derecha.

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 400).
        distance : int, optional
            Distancia del deslizamiento en píxeles (default: 300).

        Returns
        -------
        QPropertyAnimation
            Animación configurada.
        """
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)

        current_geo = widget.geometry()
        start_geo = QRect(
            current_geo.x() + distance,
            current_geo.y(),
            current_geo.width(),
            current_geo.height(),
        )
        animation.setStartValue(start_geo)
        animation.setEndValue(current_geo)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        return animation

    @staticmethod
    def slide_out_to_right(
        widget: QWidget, duration: int = 400, distance: int = 300
    ) -> QPropertyAnimation:
        """Desliza el widget hacia la derecha (salida).

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 400).
        distance : int, optional
            Distancia del deslizamiento en píxeles (default: 300).

        Returns
        -------
        QPropertyAnimation
            Animación configurada.
        """
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)

        current_geo = widget.geometry()
        end_geo = QRect(
            current_geo.x() + distance,
            current_geo.y(),
            current_geo.width(),
            current_geo.height(),
        )
        animation.setStartValue(current_geo)
        animation.setEndValue(end_geo)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)

        return animation

    @staticmethod
    def combined_fade_slide_in(
        widget: QWidget, duration: int = 400, distance: int = 200
    ) -> QParallelAnimationGroup:
        """Combina fade in con slide in desde la derecha.

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 400).
        distance : int, optional
            Distancia del deslizamiento (default: 200).

        Returns
        -------
        QParallelAnimationGroup
            Grupo de animaciones paralelas.
        """
        group = QParallelAnimationGroup()

        fade_anim = ChatAnimations.fade_in(widget, duration)
        slide_anim = ChatAnimations.slide_in_from_right(widget, duration, distance)

        group.addAnimation(fade_anim)
        group.addAnimation(slide_anim)

        return group

    @staticmethod
    def combined_fade_slide_out(
        widget: QWidget, duration: int = 400, distance: int = 200
    ) -> QParallelAnimationGroup:
        """Combina fade out con slide out hacia la derecha.

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 400).
        distance : int, optional
            Distancia del deslizamiento (default: 200).

        Returns
        -------
        QParallelAnimationGroup
            Grupo de animaciones paralelas.
        """
        group = QParallelAnimationGroup()

        fade_anim = ChatAnimations.fade_out(widget, duration)
        slide_anim = ChatAnimations.slide_out_to_right(widget, duration, distance)

        group.addAnimation(fade_anim)
        group.addAnimation(slide_anim)

        return group

    @staticmethod
    def scale_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
        """Anima el widget con un efecto de zoom/escala hacia adentro.

        Parameters
        ----------
        widget : QWidget
            Widget a animar.
        duration : int, optional
            Duración en milisegundos (default: 300).

        Returns
        -------
        QPropertyAnimation
            Animación de geometría con efecto de escala.
        """
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)

        current_geo = widget.geometry()
        center_x = current_geo.center().x()
        center_y = current_geo.center().y()

        # Comenzar desde 80% del tamaño original, centrado
        start_width = int(current_geo.width() * 0.8)
        start_height = int(current_geo.height() * 0.8)
        start_geo = QRect(
            center_x - start_width // 2,
            center_y - start_height // 2,
            start_width,
            start_height,
        )

        animation.setStartValue(start_geo)
        animation.setEndValue(current_geo)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)

        return animation
