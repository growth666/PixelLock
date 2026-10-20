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
    args = parser.parse_args()
    result = {'ok': False, 'qt': qVersion()}
    try:
        app = QApplication([])
        window = window_class()
        window.show()
        app.processEvents()
        if not window.isVisible() or window.grab().isNull():
            raise RuntimeError('Main window did not render')
        result['window_rendered'] = True
        source = [[(x * 17 + y * 31 + x * y) % 256 for x in range(256)]
                  for y in range(256)]
        result['algorithms'] = {}
        with tempfile.TemporaryDirectory(prefix='pixellock-test-') as folder:
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
        window.close()
        result['ok'] = True
    except Exception:
        result['error'] = traceback.format_exc()
    Path(args.report).write_text(json.dumps(result, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
