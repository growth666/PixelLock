"""Opt-in frozen application checks: --self-test --report <json path>."""

import argparse
import json
from pathlib import Path
import tempfile
import traceback

from PySide6.QtCore import qVersion
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from crypto_algorithms import (
    encrypt_pixels, decrypt_pixels, image_error_metrics,
    pixels_to_qimage, qimage_to_pixels,
)


def run_self_test(window_class) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--report', required=True)
    parser.add_argument('--screenshots', action='store_true')
    args = parser.parse_args()
    result = {'ok': False, 'qt': qVersion()}
    try:
        app = QApplication([])
        app.setStyle('Fusion')
        window = window_class()
        window.show()
        app.processEvents()
        if not window.isVisible() or window.grab().isNull():
            raise RuntimeError('Main window did not render')
        result['window_rendered'] = True
        if window.open_button.text() != '打开图片':
            raise RuntimeError('Default Chinese UI not applied')
        if args.screenshots:
            window.grab().save(str(Path(args.report).with_suffix('.zh.png')))
        window.language_button.click()
        app.processEvents()
        if window.open_button.text() != 'OPEN IMAGE':
            raise RuntimeError('English UI not applied')
        if args.screenshots:
            window.grab().save(str(Path(args.report).with_suffix('.en.png')))
        window.language_button.click()
        source = [[(x * 17 + y * 31 + x * y) % 256 for x in range(256)]
                  for y in range(256)]
        result['algorithms'] = {}
        with tempfile.TemporaryDirectory(prefix='pixellock-test-') as folder:
            source_path = Path(folder) / 'source.png'
            if not pixels_to_qimage(source).save(str(source_path)):
                raise RuntimeError('Source PNG save failed')
            window.load_image(source_path)
            for algorithm in ('otp', 'arnold', 'hill', 'combined'):
                cipher = encrypt_pixels(source, algorithm, seed=42, rounds=6)
                path = str(Path(folder) / (algorithm + '.png'))
                if not pixels_to_qimage(cipher).save(path, 'PNG'):
                    raise RuntimeError('PNG save failed')
                loaded = qimage_to_pixels(QImage(path))
                if loaded != cipher:
                    raise RuntimeError('PNG pixels changed')
                restored = decrypt_pixels(loaded, algorithm, seed=42, rounds=6)
                error = image_error_metrics(source, restored)
                if error != (0, 0.0):
                    raise RuntimeError(f'{algorithm}: {error}')
                result['algorithms'][algorithm] = {'max_error': error[0], 'mae': error[1]}
                window.algorithm_combo.setCurrentIndex(window.algorithm_combo.findData(algorithm))
                window.encrypt_current_image()
                settings = window.cipher_settings.copy()
                before = qimage_to_pixels(window.cipher_image)
                window.language_button.click()
                if window.cipher_settings != settings or qimage_to_pixels(window.cipher_image) != before:
                    raise RuntimeError('Language switch changed cipher state')
                window.decrypt_current_image()
                if window.error_metrics != (0, 0.0):
                    raise RuntimeError('UI roundtrip failed after language switch')
                window.language_button.click()
        result['language_switch_preserves_results'] = True
        window.close()
        result['ok'] = True
    except Exception:
        result['error'] = traceback.format_exc()
    Path(args.report).write_text(json.dumps(result, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
