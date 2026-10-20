"""Regression checks for language switching during an encryption session."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QLabel
from app import PixelLockWindow
from crypto_algorithms import pixels_to_qimage, qimage_to_pixels


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = PixelLockWindow()
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / 'sample.png'
        self.source = [[(x * 17 + y * 31 + x * y) % 256 for x in range(256)] for y in range(256)]
        self.assertTrue(pixels_to_qimage(self.source).save(str(self.path)))

    def tearDown(self):
        self.window.close()
        self.folder.cleanup()

    def test_switch_preserves_all_algorithms_and_results(self):
        w = self.window
        w.load_image(self.path)
        w.otp_seed_spin.setValue(12345)
        w.arnold_rounds_spin.setValue(7)
        w.combined_rounds_spin.setValue(8)
        for index in range(4):
            w.algorithm_combo.setCurrentIndex(index)
            settings = w.current_algorithm_settings().copy()
            w.encrypt_current_image()
            cipher = qimage_to_pixels(w.cipher_image)
            w.language_button.click()
            self.assertEqual(w.current_algorithm_settings(), settings)
            self.assertEqual(w.cipher_settings, settings)
            self.assertEqual(qimage_to_pixels(w.cipher_image), cipher)
            self.assertTrue(w.decrypt_button.isEnabled())
            w.decrypt_current_image()
            self.assertEqual(w.error_metrics, (0, 0.0))
            self.assertEqual(qimage_to_pixels(w.restored_image), self.source)
            w.language_button.click()
            self.assertEqual(w.error_metrics, (0, 0.0))
            self.assertEqual(qimage_to_pixels(w.restored_image), self.source)
            self.assertIn('最大误差', w.status_meta.text())
        # Actual parameter edits must still invalidate previous results.
        w.combined_rounds_spin.setValue(9)
        self.assertIsNone(w.cipher_image)
        self.assertFalse(w.decrypt_button.isEnabled())

    def test_english_labels_dialogs_status_and_clear(self):
        w = self.window
        w.toggle_language()
        self.assertEqual(w.open_button.text(), 'OPEN IMAGE')
        # No untranslated Chinese in application-owned English labels.
        for label in w.findChildren(QLabel):
            self.assertFalse(any('\u4e00' <= c <= '\u9fff' for c in label.text()), label.text())
        with patch('app.QFileDialog.getOpenFileName', return_value=(str(self.path), '')) as dialog:
            w.open_image()
            self.assertEqual(dialog.call_args.args[1], 'Open image')
        w.encrypt_current_image()
        output = Path(self.folder.name) / 'cipher.png'
        with patch('app.QFileDialog.getSaveFileName', return_value=(str(output), '')) as dialog:
            w.save_cipher_image()
            self.assertEqual(dialog.call_args.args[1], 'Save cipher PNG')
        self.assertTrue(output.exists())
        self.assertIn('PNG SAVED', w.status_label.text())
        w.toggle_language()
        self.assertIn('PNG 已保存', w.status_label.text())
        self.assertIn('cipher.png', w.status_label.text())
        w.clear_source()
        self.assertEqual(w.file_label.text(), '未选择图片')
        w.toggle_language()
        self.assertEqual(w.file_label.text(), 'No image selected')
        self.assertIn('ERROR: —', w.status_meta.text())
        self.assertFalse(w.encrypt_button.isEnabled())
        with patch('app.QMessageBox.warning') as warning:
            w.load_image(Path(self.folder.name) / 'missing.png')
            self.assertEqual(warning.call_args.args[1], 'Cannot open image')
        w.toggle_language()
        self.assertIn('读取失败', w.status_label.text())


if __name__ == '__main__':
    unittest.main()
