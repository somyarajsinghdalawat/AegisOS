import sys

from PySide6.QtWidgets import QApplication

from ui.dashboard import Dashboard


def main():

    application = QApplication(sys.argv)

    window = Dashboard()
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()