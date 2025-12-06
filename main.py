# main.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from gui_ui import OdinMainWindow
from flash_thread import FlashThread
from device_scanner import DeviceScannerThread
from parser import format_log
from runner import build_flash_command

# --- FUNÇÃO ESSENCIAL PARA O PYINSTALLER ---
def resource_path(relative_path):
    """ Obtém o caminho absoluto para recursos, funcione em dev e no PyInstaller """
    try:
        # PyInstaller cria uma pasta temporária em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# -------------------------------------------

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

        # ATENÇÃO: Se o DeviceScannerThread chama o executável odin4,
        # ele também precisa saber o caminho correto (veja nota abaixo do código).
        self.scanner_thread = DeviceScannerThread()
        self.scanner_thread.device_list_found.connect(self.update_device_list)
        self.scanner_thread.start()

    def update_device_list(self, devices: list):
        """Atualiza o ComboBox com a lista de dispositivos encontrados."""
        self.device_combo.clear()
        # Verificação de segurança para evitar crash se devices for None
        if devices and len(devices) > 0 and not devices[0].startswith("ERRO"):
            self.device_combo.addItems(devices)
            self.device_combo.setEnabled(True)
            self.status_label.setText(f"Status: {len(devices)} dispositivo(s) detectado(s).")
        else:
            self.device_combo.addItem("Nenhum dispositivo encontrado ou erro.")
            self.device_combo.setEnabled(False)
            self.status_label.setText("Status: Erro na detecção ou nenhum dispositivo.")

    def start_flash(self):
        """Inicia o processo de flash na thread."""
        self.log_text.clear()

        # 1. Coletar dados da UI
        firmware_set = {k: v.text() for k, v in self.file_fields.items() if v.text()}
        options = {
            'nand_erase': self.nand_erase_checkbox.isChecked(),
            'home_validation': self.home_validation_checkbox.isChecked(),
            'reboot': self.reboot_checkbox.isChecked(),
            'device_path': self.device_combo.currentText() if self.device_combo.isEnabled() and "Nenhum" not in self.device_combo.currentText() else None,
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
            log_line = parsed_data.get("text", str(parsed_data))
        self.log_text.append(log_line)

    def flash_finished(self, status: str):
        """Processa o resultado final do flash."""
        self.start_btn.setEnabled(True)
        if status == "PASS":
            self.status_label.setText("Status: FLASH COMPLETO COM SUCESSO! ✅")
            QMessageBox.information(self, "Sucesso", "O processo de flash foi concluído.")
        else:
            self.status_label.setText(f"Status: FALHA NO FLASH! ❌ ({status})")
            QMessageBox.critical(self, "Falha", "Ocorreu um erro durante o processo de flash. Verifique os logs.")

        self.scan_devices()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- CORREÇÃO AQUI: Usar resource_path para o estilo ---
    qss_path = resource_path(os.path.join("assets", "styles.qss"))
    
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"Erro ao carregar estilo: {e}")
    else:
        print(f"Arquivo de estilo não encontrado em: {qss_path}")

    window = MainApp()
    window.show()
    sys.exit(app.exec())
