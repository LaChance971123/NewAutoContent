from qt_core import *

class Ui_MainPages(object):
    def setupUi(self, parent):
        if not parent.objectName():
            parent.setObjectName("MainPages")
        self.main_layout = QVBoxLayout(parent)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(0)
        self.pages = QStackedWidget()
        self.main_layout.addWidget(self.pages)
        self._widgets = {}
        self._anim = None

    def load_pages(self, mapping: dict):
        for name, cls in mapping.items():
            widget = cls()
            self.pages.addWidget(widget)
            self._widgets[name] = widget
        self.pages.setCurrentIndex(0)

    def set_current(self, name: str):
        widget = self._widgets.get(name)
        if widget is not None:
            self.pages.setCurrentWidget(widget)
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(150)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.finished.connect(lambda: widget.setGraphicsEffect(None))
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            self._anim = anim

