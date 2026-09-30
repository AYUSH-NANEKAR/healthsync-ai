import sys

from PySide6.QtWidgets import QApplication

from app.services.auth_manager import AuthManager
from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow


class ApplicationController:
    """
    Controls the application startup and authentication flow.
    """

    def __init__(self, app):
        self.app = app

        self.auth_manager = AuthManager()

        self.login_window = None
        self.main_window = None

    def start(self):
        """
        Start HealthSync AI.

        If a valid saved session exists, open the main window.
        Otherwise, show the login window.
        """

        user = self.auth_manager.restore_saved_session()

        if user is not None:
            self.show_main_window()
        else:
            self.show_login_window()

    def show_login_window(self):
        """
        Show the login window.
        """

        self.login_window = LoginWindow()

        self.login_window.login_successful.connect(
            self.handle_login_success
        )

        self.login_window.show()

    def handle_login_success(self, user):
        """
        Handle successful authentication.
        """

        self.show_main_window()

    def show_main_window(self):
        """
        Show the main HealthSync AI application window.
        """

        self.main_window = MainWindow()

        self.main_window.logout_requested.connect(
            self.handle_logout
        )

        self.main_window.show()

        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None

    def handle_logout(self):
      """
      Log out the current user and return to the login screen.
      """

      self.auth_manager.logout()

      if self.main_window is not None:
          self.main_window.close()
          self.main_window = None

      self.show_login_window()

      if self.main_window is not None:
              self.main_window.close()
              self.main_window = None

      self.show_login_window()


def main():
    app = QApplication(sys.argv)

    controller = ApplicationController(app)
    controller.start()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())