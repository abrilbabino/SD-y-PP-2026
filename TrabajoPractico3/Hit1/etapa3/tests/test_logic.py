import numpy as np
import pytest
import cv2
from TrabajoPractico3.Hit1.etapa3.master import split_image, assemble_image, encode_image_bytes, decode_image_bytes
from TrabajoPractico3.Hit1.etapa3.worker import apply_sobel_gray

def test_split_and_assemble():
    img = np.zeros((100, 100), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), 255, -1)

    n_chunks = 4
    chunks = split_image(img, n_chunks)
    assert len(chunks) == n_chunks

    results_dict = {}
    for c in chunks:
        results_dict[c["id"]] = {
            "meta": {"y0": c["y0"], "y1": c["y1"], "y0e": c["y0e"], "y1e": c["y1e"]},
            "img": c["data"]
        }

    assembled = assemble_image(100, 100, results_dict, n_chunks)
    np.testing.assert_array_equal(assembled, img)


def test_encoding_decoding():
    img = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
    b64 = encode_image_bytes(img)
    assert isinstance(b64, str)

    decoded = decode_image_bytes(b64)
    np.testing.assert_array_equal(decoded, img)


def test_worker_processing():
    img = np.zeros((50, 50), dtype=np.uint8)
    img[20:30, :] = 255

    processed = apply_sobel_gray(img)
    assert processed.shape == (50, 50)
    assert np.any(processed > 0)
