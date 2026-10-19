"""Pure-Python image cipher routines used by the desktop application.

The routines operate on 256 x 256 grayscale pixel matrices whose values are
in the range 0..255. Keeping this module independent from NumPy means the
desktop UI can be installed with only PySide6; the original demonstration
script remains unchanged.
"""

from __future__ import annotations

import random
from typing import Sequence

from PySide6.QtGui import QImage


IMAGE_SIZE = 256
PIXEL_MODULUS = 256
ARNOLD_PERIOD = 192

Matrix = list[list[int]]

K = ((3, 2), (1, 3))
K_INV = ((37, 146), (73, 37))


def _copy_matrix(pixels: Sequence[Sequence[int]]) -> Matrix:
    if len(pixels) != IMAGE_SIZE or any(len(row) != IMAGE_SIZE for row in pixels):
        raise ValueError(f"图像必须为 {IMAGE_SIZE}×{IMAGE_SIZE}。")
    return [[int(value) % PIXEL_MODULUS for value in row] for row in pixels]


def qimage_to_pixels(image: QImage) -> Matrix:
    """Convert a grayscale QImage into a 256 x 256 Python pixel matrix."""
    gray = image.convertToFormat(QImage.Format.Format_Grayscale8)
    if gray.width() != IMAGE_SIZE or gray.height() != IMAGE_SIZE:
        raise ValueError(f"图像必须为 {IMAGE_SIZE}×{IMAGE_SIZE}。")

    bytes_per_line = gray.bytesPerLine()
    raw = bytes(gray.constBits())
    return [
        list(raw[row * bytes_per_line : row * bytes_per_line + IMAGE_SIZE])
        for row in range(IMAGE_SIZE)
    ]


def pixels_to_qimage(pixels: Sequence[Sequence[int]]) -> QImage:
    """Convert a 256 x 256 pixel matrix to an owned grayscale QImage."""
    matrix = _copy_matrix(pixels)
    raw = bytes(value for row in matrix for value in row)
    image = QImage(
        raw,
        IMAGE_SIZE,
        IMAGE_SIZE,
        IMAGE_SIZE,
        QImage.Format.Format_Grayscale8,
    )
    return image.copy()


def _otp_key(seed: int) -> Matrix:
    rng = random.Random(int(seed))
    return [
        [rng.randrange(PIXEL_MODULUS) for _ in range(IMAGE_SIZE)]
        for _ in range(IMAGE_SIZE)
    ]


def otp_encrypt(pixels: Sequence[Sequence[int]], seed: int) -> Matrix:
    plain = _copy_matrix(pixels)
    key = _otp_key(seed)
    return [
        [(plain[row][col] + key[row][col]) % PIXEL_MODULUS for col in range(IMAGE_SIZE)]
        for row in range(IMAGE_SIZE)
    ]


def otp_decrypt(pixels: Sequence[Sequence[int]], seed: int) -> Matrix:
    cipher = _copy_matrix(pixels)
    key = _otp_key(seed)
    return [
        [(cipher[row][col] - key[row][col]) % PIXEL_MODULUS for col in range(IMAGE_SIZE)]
        for row in range(IMAGE_SIZE)
    ]


def arnold_transform(pixels: Sequence[Sequence[int]], rounds: int) -> Matrix:
    """Apply the same Arnold coordinate transform as the original script."""
    current = _copy_matrix(pixels)
    normalized_rounds = int(rounds) % ARNOLD_PERIOD
    for _ in range(normalized_rounds):
        transformed = [[0] * IMAGE_SIZE for _ in range(IMAGE_SIZE)]
        for y in range(IMAGE_SIZE):
            source_row = current[y]
            for x in range(IMAGE_SIZE):
                new_x = (2 * x + y) % IMAGE_SIZE
                new_y = (x + y) % IMAGE_SIZE
                transformed[new_y][new_x] = source_row[x]
        current = transformed
    return current


def arnold_encrypt(pixels: Sequence[Sequence[int]], rounds: int) -> Matrix:
    if not 0 <= int(rounds) <= ARNOLD_PERIOD:
        raise ValueError(f"Arnold 轮数必须在 0–{ARNOLD_PERIOD} 之间。")
    return arnold_transform(pixels, int(rounds))


def arnold_decrypt(pixels: Sequence[Sequence[int]], rounds: int) -> Matrix:
    if not 0 <= int(rounds) <= ARNOLD_PERIOD:
        raise ValueError(f"Arnold 轮数必须在 0–{ARNOLD_PERIOD} 之间。")
    return arnold_transform(pixels, ARNOLD_PERIOD - int(rounds))


def _bilateral_matrix_transform(
    pixels: Sequence[Sequence[int]], matrix: tuple[tuple[int, int], tuple[int, int]]
) -> Matrix:
    source = _copy_matrix(pixels)
    a, b = matrix[0]
    c, d = matrix[1]
    output = [[0] * IMAGE_SIZE for _ in range(IMAGE_SIZE)]
    for row in range(0, IMAGE_SIZE, 2):
        for col in range(0, IMAGE_SIZE, 2):
            p00 = source[row][col]
            p01 = source[row][col + 1]
            p10 = source[row + 1][col]
            p11 = source[row + 1][col + 1]

            left00 = a * p00 + b * p10
            left01 = a * p01 + b * p11
            left10 = c * p00 + d * p10
            left11 = c * p01 + d * p11

            output[row][col] = (left00 * a + left01 * c) % PIXEL_MODULUS
            output[row][col + 1] = (left00 * b + left01 * d) % PIXEL_MODULUS
            output[row + 1][col] = (left10 * a + left11 * c) % PIXEL_MODULUS
            output[row + 1][col + 1] = (left10 * b + left11 * d) % PIXEL_MODULUS
    return output


def hill_encrypt(pixels: Sequence[Sequence[int]]) -> Matrix:
    return _bilateral_matrix_transform(pixels, K)


def hill_decrypt(pixels: Sequence[Sequence[int]]) -> Matrix:
    return _bilateral_matrix_transform(pixels, K_INV)


def encrypt_pixels(
    pixels: Sequence[Sequence[int]],
    algorithm: str,
    *,
    seed: int = 9,
    rounds: int = 6,
) -> Matrix:
    """Encrypt pixels using one of the four UI algorithm identifiers."""
    if algorithm == "otp":
        return otp_encrypt(pixels, seed)
    if algorithm == "arnold":
        return arnold_encrypt(pixels, rounds)
    if algorithm == "hill":
        return hill_encrypt(pixels)
    if algorithm == "combined":
        return hill_encrypt(arnold_encrypt(pixels, rounds))
    raise ValueError(f"未知算法：{algorithm}")


def decrypt_pixels(
    pixels: Sequence[Sequence[int]],
    algorithm: str,
    *,
    seed: int = 9,
    rounds: int = 6,
) -> Matrix:
    """Decrypt pixels using the inverse of ``encrypt_pixels``."""
    if algorithm == "otp":
        return otp_decrypt(pixels, seed)
    if algorithm == "arnold":
        return arnold_decrypt(pixels, rounds)
    if algorithm == "hill":
        return hill_decrypt(pixels)
    if algorithm == "combined":
        return arnold_decrypt(hill_decrypt(pixels), rounds)
    raise ValueError(f"未知算法：{algorithm}")


def image_error_metrics(
    left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]
) -> tuple[int, float]:
    """Return maximum absolute error and mean absolute error for two images."""
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("待比较图像的尺寸不一致。")
    errors = [
        abs(int(a) - int(b))
        for row_a, row_b in zip(left, right)
        for a, b in zip(row_a, row_b)
    ]
    return max(errors, default=0), sum(errors) / len(errors) if errors else 0.0


def max_abs_error(left: Sequence[Sequence[int]], right: Sequence[Sequence[int]]) -> int:
    """Return the maximum absolute pixel error."""
    return image_error_metrics(left, right)[0]
