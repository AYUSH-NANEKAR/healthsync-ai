import sys

from PySide6.QtWidgets import QApplication

from app.services.auth_manager import AuthManager
from app.services.ble.integration import BLEIntegrationService
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

        self.ble_service = None

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
        Show the main HealthSync AI application
        and start the BLE integration.
        """

        user_id = self.auth_manager.current_user["id"]

        self.start_ble_service(user_id)

        self.main_window = MainWindow(
            user_id=user_id,
            ble_service=self.ble_service,
        )

        self.main_window.logout_requested.connect(
            self.handle_logout
        )

        self.main_window.show()

        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None

        self.ble_service.start()

    def start_ble_service(self, user_id: int):
        """
        Create the BLE integration service for the
        authenticated user.
        """

        self.ble_service = BLEIntegrationService(
            user_id=user_id
        )

        self.ble_service.status_changed.connect(
            self.handle_ble_status
        )

        self.ble_service.telemetry_received.connect(
            self.handle_telemetry
        )

        self.ble_service.error_occurred.connect(
            self.handle_ble_error
        )

    def handle_ble_status(self, status: str):
        """
        Handle BLE status updates.
        """

        print(f"[BLE] {status}")

    def handle_telemetry(self, telemetry):
        """
        Handle telemetry received from the BLE pipeline.

        Database persistence already happens inside
        HealthService.

        Dashboard and My Health will consume the complete
        telemetry object later.
        """

        print(
            "[TELEMETRY] "
            f"HR={telemetry.heart_rate}, "
            f"SpO2={telemetry.spo2}, "
            f"Temp={telemetry.temperature}, "
            f"Steps={telemetry.steps}, "
            f"Battery={telemetry.battery}"
        )

    def handle_ble_error(self, error: str):
        """
        Handle BLE integration errors.
        """

        print(f"[BLE ERROR] {error}")

    def handle_logout(self):
        """
        Log out the current user and return to the login screen.
        """

        if self.ble_service is not None:
            self.ble_service.stop()
            self.ble_service = None

        self.auth_manager.logout()

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