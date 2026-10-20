"""PixelLock's desktop user interface for local image encryption."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from crypto_algorithms import (
    decrypt_pixels,
    encrypt_pixels,
    image_error_metrics,
    pixels_to_qimage,
    qimage_to_pixels,
)


IMAGE_SIZE = 256


STYLESHEET = """
QWidget#root {
    background: #14141f;
    color: #f2f0e8;
    font-family: "Consolas", "Microsoft YaHei UI", monospace;
    font-size: 13px;
}
QFrame#panel, QFrame#previewCard {
    background: #1d1d2b;
    border: 2px solid #39394f;
}
QLabel#brand {
    color: #a7ff5a;
    font-size: 30px;
    font-weight: 900;
    letter-spacing: 2px;
}
QLabel#subtitle, QLabel#muted, QLabel#cardHint {
    color: #a5a5bb;
}
QLabel#sectionTitle {
    color: #55e5e6;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
}
QLabel#cardTitle {
    color: #f2f0e8;
    font-size: 14px;
    font-weight: 800;
}
QLabel#badge {
    color: #14141f;
    background: #a7ff5a;
    border: 2px solid #d8ffb5;
    padding: 7px 10px;
    font-weight: 900;
}
QLabel#previewCanvas {
    color: #77778c;
    background: #101019;
    border: 2px solid #4b4b64;
    font-size: 12px;
    font-weight: 800;
}
QPushButton {
    color: #14141f;
    background: #a7ff5a;
    border: 0;
    border-bottom: 4px solid #5b9f2b;
    padding: 12px 14px;
    font-weight: 900;
    letter-spacing: 1px;
}
QPushButton:hover {
    background: #c1ff8a;
}
QPushButton:pressed {
    background: #8cdb46;
    border-bottom-width: 1px;
    padding-top: 14px;
}
QPushButton#secondaryButton {
    color: #d3d2e3;
    background: #303044;
    border: 2px solid #50506a;
}
QPushButton#secondaryButton:hover {
    background: #3b3b52;
}
QComboBox, QSpinBox {
    color: #f2f0e8;
    background: #14141f;
    border: 2px solid #50506a;
    padding: 7px 9px;
    min-height: 20px;
    font-weight: 800;
}
QComboBox::drop-down {
    border: 0;
    width: 24px;
}
QComboBox QAbstractItemView {
    color: #f2f0e8;
    background: #1d1d2b;
    border: 2px solid #50506a;
    selection-background-color: #39394f;
    outline: 0;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    border: 0;
    background: #303044;
}
QLabel#statusBar {
    color: #14141f;
    background: #55e5e6;
    padding: 9px 12px;
    font-weight: 900;
}
QLabel#statusMeta {
    color: #a7ff5a;
    font-weight: 800;
}
QFrame#separator {
    background: #39394f;
    max-height: 2px;
    min-height: 2px;
    border: 0;
}
"""


class PreviewCard(QFrame):
    """A pixel-style image preview panel."""

    def __init__(self, index: str, title: str, hint: str, placeholder: str) -> None:
        super().__init__()
        self.setObjectName("previewCard")
        self._image: QImage | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QHBoxLayout()
        self.index_label = QLabel(index)
        self.index_label.setObjectName("sectionTitle")
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        heading.addWidget(self.index_label)
        heading.addWidget(title_label)
        heading.addStretch(1)
        layout.addLayout(heading)

        self.canvas = QLabel(placeholder)
        self.canvas.setObjectName("previewCanvas")
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.setFixedSize(260, 260)
        self.canvas.setWordWrap(True)
        layout.addWidget(self.canvas, 0, Qt.AlignmentFlag.AlignHCenter)

        hint_label = QLabel(hint)
        hint_label.setObjectName("cardHint")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        layout.addStretch(1)

    def set_image(self, image: QImage) -> None:
        self._image = image.copy()
        self._refresh_pixmap()

    def clear_image(self, placeholder: str) -> None:
        self._image = None
        self.canvas.setPixmap(QPixmap())
        self.canvas.setText(placeholder)

    def _refresh_pixmap(self) -> None:
        if self._image is None:
            return
        pixmap = QPixmap.fromImage(self._image)
        self.canvas.setText("")
        self.canvas.setPixmap(
            pixmap.scaled(
                self.canvas.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        )


class PixelLockWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PIXEL LOCK | Image Cipher Lab")
        self.setMinimumSize(1260, 760)
        self.resize(1400, 850)

        self.source_path: Path | None = None
        self.grayscale_image: QImage | None = None
        self.cipher_image: QImage | None = None
        self.cipher_settings: dict[str, int | str] | None = None
        self.restored_image: QImage | None = None
        self.error_metrics: tuple[int, float] | None = None

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        page = QVBoxLayout(root)
        page.setContentsMargins(24, 20, 24, 16)
        page.setSpacing(16)

        page.addLayout(self._build_header())
        page.addWidget(self._separator())
        page.addLayout(self._build_workspace(), 1)
        page.addWidget(self._build_status_bar())

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        identity = QVBoxLayout()
        title = QLabel("PIXEL LOCK")
        title.setObjectName("brand")
        subtitle = QLabel("IMAGE CIPHER LAB  /  8-BIT DESKTOP TOOL")
        subtitle.setObjectName("subtitle")
        identity.addWidget(title)
        identity.addWidget(subtitle)
        header.addLayout(identity)
        header.addStretch(1)
        badge = QLabel("LOCAL MODE  //  256 × 256")
        badge.setObjectName("badge")
        header.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        return header

    def _build_workspace(self) -> QHBoxLayout:
        workspace = QHBoxLayout()
        workspace.setSpacing(16)
        workspace.addWidget(self._build_sidebar())

        preview_area = QVBoxLayout()
        preview_header = QHBoxLayout()
        section = QLabel("PREVIEW DECK")
        section.setObjectName("sectionTitle")
        note = QLabel("NEAREST-NEIGHBOR DISPLAY  /  8-BIT LOOK")
        note.setObjectName("muted")
        preview_header.addWidget(section)
        preview_header.addStretch(1)
        preview_header.addWidget(note)
        preview_area.addLayout(preview_header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.input_card = PreviewCard(
            "01", "INPUT", "自动缩放并转为 256×256 灰度", "NO IMAGE\nOPEN AN IMAGE TO BEGIN"
        )
        self.cipher_card = PreviewCard(
            "02", "CIPHER", "密文预览；可导出为 PNG", "CIPHER STAGE\nWAITING FOR INPUT"
        )
        self.output_card = PreviewCard(
            "03", "RESTORED", "显示还原结果与像素误差", "RESTORE STAGE\nWAITING FOR CIPHER"
        )
        cards.addWidget(self.input_card, 1)
        cards.addWidget(self.cipher_card, 1)
        cards.addWidget(self.output_card, 1)
        preview_area.addLayout(cards, 1)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.encrypt_button = QPushButton("⚡  ENCRYPT IMAGE")
        self.encrypt_button.setEnabled(False)
        self.encrypt_button.clicked.connect(self.encrypt_current_image)
        self.save_cipher_button = QPushButton("SAVE CIPHER PNG")
        self.save_cipher_button.setObjectName("secondaryButton")
        self.save_cipher_button.setEnabled(False)
        self.save_cipher_button.clicked.connect(self.save_cipher_image)
        self.decrypt_button = QPushButton("DECRYPT + CHECK")
        self.decrypt_button.setObjectName("secondaryButton")
        self.decrypt_button.setEnabled(False)
        self.decrypt_button.clicked.connect(self.decrypt_current_image)
        actions.addWidget(self.encrypt_button)
        actions.addWidget(self.save_cipher_button)
        actions.addWidget(self.decrypt_button)
        preview_area.addLayout(actions)
        workspace.addLayout(preview_area, 1)
        return workspace

    def _build_sidebar(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(268)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        section = QLabel("01  /  SOURCE IMAGE")
        section.setObjectName("sectionTitle")
        layout.addWidget(section)

        self.open_button = QPushButton("▣  OPEN IMAGE")
        self.open_button.clicked.connect(self.open_image)
        layout.addWidget(self.open_button)

        self.clear_button = QPushButton("CLEAR SOURCE")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(self.clear_source)
        self.clear_button.setEnabled(False)
        layout.addWidget(self.clear_button)

        self.file_label = QLabel("未选择图片")
        self.file_label.setObjectName("cardTitle")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        self.dimensions_label = QLabel("INPUT  —\nOUTPUT  256 × 256 / L")
        self.dimensions_label.setObjectName("muted")
        self.dimensions_label.setWordWrap(True)
        layout.addWidget(self.dimensions_label)

        layout.addWidget(self._separator())
        algorithm_title = QLabel("02  /  ALGORITHM")
        algorithm_title.setObjectName("sectionTitle")
        layout.addWidget(algorithm_title)

        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItem("一次一密 / OTP", "otp")
        self.algorithm_combo.addItem("Arnold 置乱", "arnold")
        self.algorithm_combo.addItem("Hill 扩散", "hill")
        self.algorithm_combo.addItem("组合加密", "combined")
        self.algorithm_combo.currentIndexChanged.connect(self._on_algorithm_changed)
        layout.addWidget(self.algorithm_combo)

        self.parameter_stack = QStackedWidget()
        otp_page, self.otp_seed_spin = self._make_parameter_page(
            "OTP SEED", 0, 2_147_483_647, 9, "同一密钥种子用于后续解密。"
        )
        arnold_page, self.arnold_rounds_spin = self._make_parameter_page(
            "ARNOLD ROUNDS", 1, 192, 6, "轮数范围：1–192。"
        )
        hill_page = self._make_fixed_parameter_page(
            "HILL BLOCK", "2×2 BLOCKS  /  MOD 256\n使用现有 K 与逆矩阵。"
        )
        combined_page, self.combined_rounds_spin = self._make_parameter_page(
            "ARNOLD ROUNDS", 1, 192, 6, "流程：Arnold 置乱 → Hill 扩散。"
        )
        for parameter_page in (otp_page, arnold_page, hill_page, combined_page):
            self.parameter_stack.addWidget(parameter_page)
        for spin in (self.otp_seed_spin, self.arnold_rounds_spin, self.combined_rounds_spin):
            spin.valueChanged.connect(self._on_algorithm_parameters_changed)
        layout.addWidget(self.parameter_stack)

        layout.addWidget(self._separator())
        steps_title = QLabel("WORKFLOW")
        steps_title.setObjectName("sectionTitle")
        layout.addWidget(steps_title)

        self.workflow_steps: dict[str, QLabel] = {}
        self.workflow_markers: dict[str, QLabel] = {}
        for number, label in (
            ("01", "LOAD + GRAYSCALE"),
            ("02", "SELECT ALGORITHM"),
            ("03", "ENCRYPT + EXPORT"),
            ("04", "DECRYPT + CHECK"),
        ):
            row = QHBoxLayout()
            step = QLabel(f"{number}  {label}")
            step.setObjectName("muted")
            marker = QLabel("[NEXT]")
            marker.setObjectName("muted")
            self.workflow_steps[number] = step
            self.workflow_markers[number] = marker
            row.addWidget(step)
            row.addStretch(1)
            row.addWidget(marker)
            layout.addLayout(row)

        layout.addStretch(1)
        privacy = QLabel("LOCAL PROCESSING\n图片在本地处理，不会上传。")
        privacy.setObjectName("muted")
        privacy.setWordWrap(True)
        layout.addWidget(privacy)
        self._update_workflow()
        return panel

    @staticmethod
    def _make_parameter_page(
        label: str, minimum: int, maximum: int, value: int, hint: str
    ) -> tuple[QWidget, QSpinBox]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(5)

        row = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("muted")
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setObjectName("parameterSpin")
        row.addWidget(title)
        row.addStretch(1)
        row.addWidget(spin)
        layout.addLayout(row)

        note = QLabel(hint)
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        return page, spin

    @staticmethod
    def _make_fixed_parameter_page(title: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(5)
        heading = QLabel(title)
        heading.setObjectName("muted")
        details = QLabel(description)
        details.setObjectName("cardHint")
        details.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(details)
        return page

    def _on_algorithm_changed(self, index: int) -> None:
        self.parameter_stack.setCurrentIndex(index)
        self._invalidate_cipher_if_needed()
        selected = self.algorithm_combo.currentText()
        self.status_label.setText(f"ALGORITHM SELECTED  //  {selected}")

    def _on_algorithm_parameters_changed(self, _value: int) -> None:
        self._invalidate_cipher_if_needed()
        if self.grayscale_image is not None:
            self.status_label.setText("PARAMETERS UPDATED  //  READY TO ENCRYPT")

    def _invalidate_cipher_if_needed(self) -> None:
        if self.cipher_image is None:
            return
        self.cipher_image = None
        self.cipher_settings = None
        self.restored_image = None
        self.error_metrics = None
        self.cipher_card.clear_image("CIPHER STAGE\nWAITING FOR INPUT")
        self.output_card.clear_image("RESTORE STAGE\nWAITING FOR CIPHER")
        self.save_cipher_button.setEnabled(False)
        self.decrypt_button.setEnabled(False)
        self.status_meta.setText("ERROR: —")
        self._update_workflow()

    def _update_workflow(self) -> None:
        states = {
            "01": "DONE" if self.grayscale_image is not None else "ACTIVE",
            "02": "ACTIVE",
            "03": "DONE" if self.cipher_image is not None else "NEXT",
            "04": (
                "DONE"
                if self.restored_image is not None
                else "NEXT" if self.cipher_image is not None else "LOCKED"
            ),
        }
        for number, state in states.items():
            step = self.workflow_steps[number]
            marker = self.workflow_markers[number]
            step.setObjectName("cardTitle" if state in ("ACTIVE", "DONE") else "muted")
            marker.setText(f"[{state}]")
            marker.setObjectName("statusMeta" if state in ("ACTIVE", "DONE") else "muted")
            step.style().unpolish(step)
            step.style().polish(step)
            marker.style().unpolish(marker)
            marker.style().polish(marker)

    def current_algorithm_settings(self) -> dict[str, int | str]:
        """Return the selected algorithm and its current parameters."""
        algorithm = str(self.algorithm_combo.currentData())
        settings: dict[str, int | str] = {"algorithm": algorithm}
        if algorithm == "otp":
            settings["seed"] = self.otp_seed_spin.value()
        elif algorithm == "arnold":
            settings["rounds"] = self.arnold_rounds_spin.value()
        elif algorithm == "combined":
            settings["rounds"] = self.combined_rounds_spin.value()
        return settings

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.status_label = QLabel("READY  //  请打开一张图片")
        self.status_label.setObjectName("statusBar")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.status_meta = QLabel("ERROR: —")
        self.status_meta.setObjectName("statusMeta")
        layout.addWidget(self.status_label, 1)
        layout.addWidget(self.status_meta)
        return bar

    @staticmethod
    def _separator() -> QFrame:
        line = QFrame()
        line.setObjectName("separator")
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    def open_image(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff);;所有文件 (*)",
        )
        if file_name:
            self.load_image(Path(file_name))

    def load_image(self, path: Path) -> None:
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        source = reader.read()
        if source.isNull():
            message = reader.errorString() or "无法读取该图片。"
            self.status_label.setText(f"ERROR  //  {message}")
            QMessageBox.warning(self, "图片读取失败", message)
            return

        original_width, original_height = source.width(), source.height()
        grayscale = source.convertToFormat(QImage.Format.Format_Grayscale8)
        normalized = grayscale.scaled(
            IMAGE_SIZE,
            IMAGE_SIZE,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ).copy()

        self.source_path = path
        self.grayscale_image = normalized
        self._invalidate_cipher_if_needed()
        self.input_card.set_image(normalized)
        self.file_label.setText(path.name)
        self.dimensions_label.setText(
            f"INPUT  {original_width} × {original_height}\nOUTPUT  256 × 256 / GRAYSCALE"
        )
        self.clear_button.setEnabled(True)
        self.encrypt_button.setEnabled(True)
        self.status_label.setText("IMAGE READY  //  已转换为 256×256 灰度图")
        self.status_meta.setText("ERROR: —")
        self._update_workflow()

    def encrypt_current_image(self) -> None:
        if self.grayscale_image is None:
            self.status_label.setText("ERROR  //  请先打开一张图片")
            return

        settings = self.current_algorithm_settings()
        algorithm = str(settings["algorithm"])
        try:
            source_pixels = qimage_to_pixels(self.grayscale_image)
            cipher_pixels = encrypt_pixels(
                source_pixels,
                algorithm,
                seed=int(settings.get("seed", 9)),
                rounds=int(settings.get("rounds", 6)),
            )
            cipher = pixels_to_qimage(cipher_pixels)
        except (TypeError, ValueError, RuntimeError) as error:
            self.status_label.setText(f"ENCRYPTION FAILED  //  {error}")
            QMessageBox.warning(self, "加密失败", str(error))
            return

        self.cipher_image = cipher
        self.cipher_settings = settings.copy()
        self.restored_image = None
        self.error_metrics = None
        self.cipher_card.set_image(cipher)
        self.output_card.clear_image("RESTORE STAGE\nWAITING FOR DECRYPTION")
        self.save_cipher_button.setEnabled(True)
        self.decrypt_button.setEnabled(True)
        self.status_label.setText(f"CIPHER READY  //  {self.algorithm_combo.currentText()}")
        self.status_meta.setText("ERROR: —")
        self._update_workflow()

    def save_cipher_image(self) -> None:
        if self.cipher_image is None:
            self.status_label.setText("ERROR  //  请先加密图片")
            return

        algorithm = str((self.cipher_settings or {}).get("algorithm", "cipher"))
        source_stem = self.source_path.stem if self.source_path else "image"
        suggested_name = f"{source_stem}_{algorithm}_cipher.png"
        output_directory = self.application_directory() / "image"
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "保存密文 PNG",
            str(output_directory / suggested_name),
            "PNG 图片 (*.png)",
        )
        if not file_name:
            return

        output_path = Path(file_name)
        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(".png")
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            saved = self.cipher_image.save(str(output_path), "PNG")
        except OSError as error:
            saved = False
            message = str(error)
        else:
            message = "无法写入所选路径。"

        if not saved:
            self.status_label.setText("SAVE FAILED  //  密文 PNG 保存失败")
            QMessageBox.warning(self, "保存失败", message)
            return

        self.status_label.setText(f"PNG SAVED  //  {output_path.name}")

    @staticmethod
    def application_directory() -> Path:
        """Return the directory beside the executable or source file."""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent

    def decrypt_current_image(self) -> None:
        if self.cipher_image is None or self.cipher_settings is None:
            self.status_label.setText("ERROR  //  请先加密图片")
            return
        if self.grayscale_image is None:
            self.status_label.setText("ERROR  //  原图不可用，请重新打开图片")
            return

        settings = self.cipher_settings
        algorithm = str(settings["algorithm"])
        try:
            cipher_pixels = qimage_to_pixels(self.cipher_image)
            restored_pixels = decrypt_pixels(
                cipher_pixels,
                algorithm,
                seed=int(settings.get("seed", 9)),
                rounds=int(settings.get("rounds", 6)),
            )
            original_pixels = qimage_to_pixels(self.grayscale_image)
            maximum_error, mean_error = image_error_metrics(
                original_pixels, restored_pixels
            )
            restored = pixels_to_qimage(restored_pixels)
        except (TypeError, ValueError, RuntimeError) as error:
            self.status_label.setText(f"DECRYPTION FAILED  //  {error}")
            QMessageBox.warning(self, "解密失败", str(error))
            return

        self.restored_image = restored
        self.error_metrics = (maximum_error, mean_error)
        self.output_card.set_image(restored)
        self.status_label.setText("DECRYPTED  //  还原结果已生成")
        self.status_meta.setText(f"MAX ERROR: {maximum_error}  /  MAE: {mean_error:.4f}")
        self._update_workflow()

    def clear_source(self) -> None:
        self.source_path = None
        self.grayscale_image = None
        self.cipher_image = None
        self.cipher_settings = None
        self.restored_image = None
        self.error_metrics = None
        self.input_card.clear_image("NO IMAGE\nOPEN AN IMAGE TO BEGIN")
        self.cipher_card.clear_image("CIPHER STAGE\nWAITING FOR INPUT")
        self.output_card.clear_image("RESTORE STAGE\nWAITING FOR CIPHER")
        self.file_label.setText("未选择图片")
        self.dimensions_label.setText("INPUT  —\nOUTPUT  256 × 256 / L")
        self.clear_button.setEnabled(False)
        self.encrypt_button.setEnabled(False)
        self.save_cipher_button.setEnabled(False)
        self.decrypt_button.setEnabled(False)
        self.status_label.setText("READY  //  请打开一张图片")
        self.status_meta.setText("ERROR: —")
        self._update_workflow()


def main() -> int:
    if "--self-test" in sys.argv:
        from smoke_test import run_self_test

        return run_self_test(PixelLockWindow)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = PixelLockWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
