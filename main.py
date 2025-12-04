# main.py
import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from gui_ui import OdinMainWindow
from flash_thread import FlashThread
from device_scanner import DeviceScannerThread
from parser import format_log
from runner import build_flash_command
import os

class MainApp(OdinMainWindow):
    def __init__(self):
        super().__init__()

        # Conexões de Slots
        self.start_btn.clicked.connect(self.start_flash)
        self.refresh_btn.clicked.connect(self.scan_devices)

        # Variáveis de Thread
        self.flash_thread = None
        self.scanner_thread = None

        # Inicia a busca de dispositivos ao carregar
        self.scan_devices()

    def scan_devices(self):
        """Inicia a thread para listar dispositivos."""
        self.device_combo.clear()
        self.device_combo.addItem("Buscando...")
        self.device_combo.setEnabled(False)

        self.scanner_thread = DeviceScannerThread()
        self.scanner_thread.device_list_found.connect(self.update_device_list)
        self.scanner_thread.start()

    def update_device_list(self, devices: list):
        """Atualiza o ComboBox com a lista de dispositivos encontrados."""
        self.device_combo.clear()
        if devices and not devices[0].startswith("ERRO"):
            self.device_combo.addItems(devices)
            self.device_combo.setEnabled(True)
            self.status_label.setText(f"Status: {len(devices)} dispositivo(s) detectado(s).")
        else:
            self.device_combo.addItem("Nenhum dispositivo encontrado ou erro.")
            self.device_combo.setEnabled(False)
            self.status_label.setText("Status: Erro na detecção. Certifique-se de que o odin4 está configurado (udev rules).")

    def start_flash(self):
        """Inicia o processo de flash na thread."""
        self.log_text.clear()

        # 1. Coletar dados da UI
        firmware_set = {k: v.text() for k, v in self.file_fields.items() if v.text()}
        options = {
            'nand_erase': self.nand_erase_checkbox.isChecked(),
            'home_validation': self.home_validation_checkbox.isChecked(),
            'reboot': self.reboot_checkbox.isChecked(),
            'device_path': self.device_combo.currentText() if self.device_combo.isEnabled() and self.device_combo.currentText() != "Nenhum dispositivo encontrado ou erro." else None,
        }

        if not firmware_set:
             QMessageBox.warning(self, "Atenção", "Selecione pelo menos um arquivo de firmware (AP/BL/CP/CSC).")
             return

        # 2. Montar o comando
        try:
            cmd = build_flash_command(firmware_set, options)
        except Exception as e:
            self.log_text.append(f"Erro ao montar comando: {str(e)}")
            return

        # 3. Iniciar a Thread
        self.status_label.setText("Status: Iniciando Flash...")
        self.start_btn.setEnabled(False)

        self.flash_thread = FlashThread(cmd)
        self.flash_thread.log_output.connect(self.update_log)
        self.flash_thread.flash_finished.connect(self.flash_finished)
        self.flash_thread.start()

    def update_log(self, parsed_data: dict):
        """Recebe o output processado da thread e atualiza a UI."""
        try:
            log_line = format_log(parsed_data)
        except Exception:
            # fallback simples
            log_line = parsed_data.get("text", str(parsed_data))
        self.log_text.append(log_line)
        # Se você tiver uma barra de progresso, atualize-a aqui usando parsed_data.get('percentage')

    def flash_finished(self, status: str):
        """Processa o resultado final do flash."""
        self.start_btn.setEnabled(True)
        if status == "PASS":
            self.status_label.setText("Status: FLASH COMPLETO COM SUCESSO! ✅")
            QMessageBox.information(self, "Sucesso", "O processo de flash foi concluído.")
        else:
            self.status_label.setText(f"Status: FALHA NO FLASH! ❌ ({status})")
            QMessageBox.critical(self, "Falha", "Ocorreu um erro durante o processo de flash. Verifique os logs.")

        # Reinicia a busca de dispositivos para o estado normal
        self.scan_devices()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Carregar tema se existir
    qss_path = os.path.join("assets", "styles.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception:
            pass

    window = MainApp()
    window.show()
    sys.exit(app.exec())