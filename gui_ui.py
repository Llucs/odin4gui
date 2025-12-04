# gui_ui.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLineEdit, QCheckBox, QLabel, QGroupBox,
    QComboBox, QFileDialog, QTabWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


class OdinMainWindow(QMainWindow):
    """
    Janela principal do aplicativo. Fornece os widgets que o main.py espera:
      - start_btn
      - refresh_btn
      - device_combo
      - file_fields (dict: BL, AP, CP, CSC)
      - nand_erase_checkbox
      - home_validation_checkbox
      - reboot_checkbox
      - log_text
      - status_label
    """

    REPO_URL = "https://github.com/Llucs/odin4gui/"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Odin4GUI - Linux Flash Tool")
        self.setMinimumSize(920, 640)

        # Central widget e abas
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Páginas
        self.flash_page = QWidget()
        self.about_page = QWidget()
        self.tabs.addTab(self.flash_page, "Flash")
        self.tabs.addTab(self.about_page, "Sobre")

        # Constroi páginas internas
        self._build_flash_page()
        self._build_about_page()

    # -------------------------
    # Construção da aba Flash
    # -------------------------
    def _build_flash_page(self):
        layout = QVBoxLayout(self.flash_page)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Grupo Arquivos
        file_group = QGroupBox("Arquivos de Firmware")
        file_group_layout = QVBoxLayout()
        file_group_layout.setSpacing(8)

        self.file_fields = {
            "BL": QLineEdit(),
            "AP": QLineEdit(),
            "CP": QLineEdit(),
            "CSC": QLineEdit(),
        }

        for key, field in self.file_fields.items():
            row = QHBoxLayout()
            lbl = QLabel(f"{key}:")
            lbl.setFixedWidth(36)
            row.addWidget(lbl)
            field.setPlaceholderText(f"Selecionar arquivo {key}...")
            row.addWidget(field)
            btn = QPushButton("...")
            btn.setFixedWidth(44)
            btn.clicked.connect(lambda _, k=key: self.select_file(k))
            row.addWidget(btn)
            file_group_layout.addLayout(row)

        file_group.setLayout(file_group_layout)
        layout.addWidget(file_group)

        # Opções + Dispositivo (lado a lado)
        control_row = QHBoxLayout()
        control_row.setSpacing(12)

        # Opções
        opt_group = QGroupBox("Opções")
        opt_layout = QVBoxLayout()
        opt_layout.setSpacing(8)
        self.nand_erase_checkbox = QCheckBox("NAND Erase (Full Wipe)")
        self.home_validation_checkbox = QCheckBox("Home Binary Validation (-V)")
        self.reboot_checkbox = QCheckBox("Auto Reboot")
        opt_layout.addWidget(self.nand_erase_checkbox)
        opt_layout.addWidget(self.home_validation_checkbox)
        opt_layout.addWidget(self.reboot_checkbox)
        opt_layout.addStretch()
        opt_group.setLayout(opt_layout)
        control_row.addWidget(opt_group, 2)

        # Dispositivo
        dev_group = QGroupBox("Dispositivo")
        dev_layout = QVBoxLayout()
        dev_layout.setSpacing(8)
        self.device_combo = QComboBox()
        self.device_combo.addItem("Detectando dispositivos...")
        self.device_combo.setEnabled(False)
        self.refresh_btn = QPushButton("Atualizar Lista")
        dev_layout.addWidget(self.device_combo)
        dev_layout.addWidget(self.refresh_btn)
        dev_group.setLayout(dev_layout)
        control_row.addWidget(dev_group, 1)

        layout.addLayout(control_row)

        # Botão principal iniciar
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 6, 0, 6)
        btn_row.addStretch(1)
        self.start_btn = QPushButton("INICIAR FLASH")
        self.start_btn.setObjectName("primaryButton")  # para QSS
        self.start_btn.setFixedHeight(56)
        btn_row.addWidget(self.start_btn, 0)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # Logs
        log_group = QGroupBox("Logs / Saída do Odin4")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setAcceptRichText(False)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)

        # Status
        status_row = QHBoxLayout()
        self.status_label = QLabel("Status: Pronto.")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

    # -------------------------
    # Construção da aba Sobre
    # -------------------------
    def _build_about_page(self):
        layout = QVBoxLayout(self.about_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("<h2>Odin4GUI</h2>")
        subtitle = QLabel("Native Linux GUI for the Odin4 flashing engine")
        subtitle.setStyleSheet("color: #B3B3B3;")
        info = QLabel(
            "Criado por <b>Llucs</b><br>"
            "Versão: <b>1.1.0</b><br><br>"
            "Engine original: Odin4 (Adrilaw)<br>"
            "Use com cuidado: o processo de flashing pode danificar dispositivos."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #D6D6D6;")

        # Botão para abrir repositório
        repo_btn = QPushButton("Abrir repositório no GitHub")
        repo_btn.setFixedHeight(42)
        repo_btn.clicked.connect(self._open_repository)
        repo_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addWidget(info)
        layout.addSpacing(10)
        layout.addWidget(repo_btn)
        layout.addStretch()

    # -------------------------
    # Helpers
    # -------------------------
    def select_file(self, key: str):
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"Selecionar arquivo {key}",
            "",
            "Firmware Files (*.tar *.tar.md5);;All Files (*)"
        )
        if path:
            # mantém comportamento esperado (setText)
            if key in self.file_fields:
                self.file_fields[key].setText(path)

    def append_log(self, text: str):
        """Appender simples para logs (útil se você quiser chamar diretamente)."""
        self.log_text.append(text)
        # mantém scroll no fim
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def _open_repository(self):
        QDesktopServices.openUrl(QUrl(self.REPO_URL))