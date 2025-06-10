
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from modules.ui_main import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("AutoContent - PyDracula Edition")

        # Example: hook up 'Create Story with AI' button
        if hasattr(self.ui, 'btn_create_ai'):
            self.ui.btn_create_ai.clicked.connect(self.coming_soon_popup)

    def coming_soon_popup(self):
        QMessageBox.information(self, "Coming Soon", "AI Story Generator coming soon!")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
