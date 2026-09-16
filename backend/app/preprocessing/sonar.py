import cv2, numpy as np
def preprocess(image: np.ndarray, enabled: bool=True) -> np.ndarray:
    if not enabled: return image
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    denoised = cv2.medianBlur(gray, 3)
    clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8)).apply(denoised)
    return cv2.normalize(clahe, None, 0, 255, cv2.NORM_MINMAX)
