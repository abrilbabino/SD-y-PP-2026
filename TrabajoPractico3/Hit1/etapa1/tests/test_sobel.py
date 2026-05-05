import numpy as np
import pytest
import cv2
from TrabajoPractico3.Hit1.etapa1.sobel import apply_sobel_gray


def test_apply_sobel_gray_shape():
    # Crear una imagen negra de 100x100
    img = np.zeros((100, 100), dtype=np.uint8)
    # Poner un cuadrado blanco en el centro
    img[25:75, 25:75] = 255
    
    result = apply_sobel_gray(img, ksize=3)
    
    assert result.shape == (100, 100)
    assert result.dtype == np.uint8

def test_apply_sobel_gray_constant():
    # Imagen constante no debe tener gradientes
    img = np.full((100, 100), 128, dtype=np.uint8)
    result = apply_sobel_gray(img, ksize=3)
    
    # El resultado debería ser todo 0 (o muy cercano si hay ruido de punto flotante)
    assert np.all(result == 0)

def test_apply_sobel_gray_gradient():
    # Imagen con un degradado claro
    img = np.zeros((100, 100), dtype=np.uint8)
    for i in range(100):
        img[:, i] = i * 2
        
    result = apply_sobel_gray(img, ksize=3)
    # Debe haber valores detectados
    assert np.any(result > 0)
