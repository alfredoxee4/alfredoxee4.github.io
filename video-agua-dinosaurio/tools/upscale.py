#!/usr/bin/env python3
"""Upscale x2 de las imágenes de escena con EDSR (super-resolución neuronal) + realce."""
import glob
import os
import time

import cv2
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..", "public", "img")
MODEL = os.path.join(os.path.dirname(__file__), "EDSR_x2.pb")

sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(MODEL)
sr.setModel("edsr", 2)

for path in sorted(glob.glob(os.path.join(BASE, "img*.jpg"))):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    if h >= 1900:
        print(f"skip {os.path.basename(path)} ya está a {w}x{h}")
        continue
    t0 = time.time()
    up = sr.upsample(img)
    # Realce sutil: unsharp mask + micro-saturación (look cine)
    blur = cv2.GaussianBlur(up, (0, 0), 2.2)
    up = cv2.addWeighted(up, 1.32, blur, -0.32, 0)
    hsv = cv2.cvtColor(up, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] *= 1.06
    hsv[..., 1] = np.clip(hsv[..., 1], 0, 255)
    up = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    cv2.imwrite(path, up, [cv2.IMWRITE_JPEG_QUALITY, 93])
    nh, nw = up.shape[:2]
    print(f"{os.path.basename(path)}: {w}x{h} -> {nw}x{nh} en {time.time()-t0:.1f}s")
print("UPSCALE DONE")
