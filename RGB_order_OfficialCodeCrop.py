import cv2
import numpy as np
from PIL import Image


def fillHoles(img):
    # Copy the thresholded image.
    h, w = img.shape
    canvas = np.zeros((h + 2, w + 2), np.uint8)
    canvas[1:h + 1, 1:w + 1] = img.copy()
    mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(canvas, mask, (0, 0), 1)
    canvas = canvas[1:h + 1, 1:w + 1].astype(np.bool)
    im_out = ~canvas | img.astype(np.uint8)
    del canvas, mask
    return im_out

def find_apples(img_bw):
    cnts, _ = cv2.findContours(img_bw.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None, None
    else:
        cnt = max(cnts, key=cv2.contourArea)

        out = np.zeros(img_bw.shape, np.uint8)
        bou = cv2.convexHull(cnt, False)
        cv2.drawContours(out, [bou], -1, 255, cv2.FILLED)

        BB = np.asarray(cv2.boundingRect(cnt))
        if BB[3] > BB[2]:
            BB[0] = int(BB[0] - ((BB[3] - BB[2]) / 2))
            BB[2] = int(BB[3])
        else:
            BB[1] = int(BB[1] - ((BB[2] - BB[3]) / 2))
            BB[3] = int(BB[2])
        BB[BB < 0] = 0
        del cnts, cnt, bou
        return out, BB

def apple_segment(I):
    GAD1 = cv2.GaussianBlur(I, ksize=(0, 0), sigmaX=2, borderType=cv2.BORDER_REPLICATE)
    R = np.asarray(GAD1[:,:, 0], dtype=np.float).copy()
    G = np.asarray(GAD1[:,:, 1], dtype=np.float).copy()
    B = np.asarray(GAD1[:,:, 2], dtype=np.float).copy()

    RG = R - G
    RG = np.maximum(RG, 0)
    RG = RG * 255 / np.max(RG)
    RG[RG < 20] = 0
    RG[RG >= 20] = 255
    RG = np.asarray(RG, dtype=np.uint8)
    for i in range (5):
        RG = cv2.medianBlur(RG, 3)

    RB = R - B
    RB[RB >= 40] = 255
    RB[RB < 40] = 0
    RB = np.asarray(RB, dtype=np.uint8)
    for i in range (5):
        RB = cv2.medianBlur(RB, 3)

    Common = RB.copy() | RG.copy()
    del GAD1, R, G ,B, RG, RB

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*5-1, 2*5-1))
    Common = cv2.morphologyEx(Common, cv2.MORPH_CLOSE, se)
    Common = fillHoles(Common.copy())
    Common = cv2.morphologyEx(Common, cv2.MORPH_OPEN, se)
    out, BB = find_apples(Common)
    del Common, se

    return out, BB

def apple_detect(I):
    h_old, w_old, c =  I.shape
    ratio = round(np.log2(max(h_old, w_old) / 512))
    GAD1 = I.copy()
    for i in range (ratio):
        GAD1 = cv2.pyrDown(GAD1)
    GAD = GAD1.copy()

    h_new, w_new, c = GAD.shape

    GAD = cv2.GaussianBlur(GAD.copy(), ksize=(0, 0), sigmaX=2, borderType=cv2.BORDER_REPLICATE)
    R = np.asarray(GAD[:,:, 0], dtype=np.float).copy()
    G = np.asarray(GAD[:,:, 1], dtype=np.float).copy()
    B = np.asarray(GAD[:,:, 2], dtype=np.float).copy()

    #Red apple
    RG = R - G
    red_apple = np.logical_and((RG > 5), (B < 60))

    #But some apple may green
    Rg = np.multiply(R, np.logical_not(red_apple) * 1.0)
    Gg = np.multiply(G, np.logical_not(red_apple) * 1.0)
    Bg = np.multiply(B, np.logical_not(red_apple) * 1.0)
    del R, G, B

    RgBg = Rg - Bg
    GgBg = Gg - Bg
    blue_apple = np.logical_and(np.logical_and(RgBg >= 0, GgBg > 0), np.divide(RgBg, GgBg + 0.0000001) >= 1)

    apple = np.logical_or(red_apple, blue_apple)
    del Rg, Gg, Bg, RgBg, GgBg, blue_apple, red_apple, RG

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closeBW_rg = cv2.morphologyEx(np.asarray(apple*1.0, dtype = np.uint8), cv2.MORPH_OPEN, se)
    apple = fillHoles(closeBW_rg.copy())
    apple, BB = find_apples(apple)

    if apple is not None:
        out = np.repeat(apple[:, :, np.newaxis], 3, axis=2)
        cropOut = np.multiply(GAD1, out / 255.0).astype('uint8')
        del GAD1, se, closeBW_rg, GAD

        apple, BB = apple_segment(cropOut)
        if apple is not None:
            dichtam = [np.power(2, ratio) * (BB[0] - h_new/2) + h_old/2,
                       np.power(2, ratio) * (BB[1] - w_new/2) + w_old/2,
                       np.power(2, ratio) * (BB[0] + BB[2] - h_new/2) + h_old/2,
                       np.power(2, ratio) * (BB[1] + BB[3] - w_new/2) + w_old/2]
            dichtam = np.asarray(dichtam, dtype=np.int)

            crop = I[dichtam[1]:dichtam[3], dichtam[0]:dichtam[2], :]
            if (dichtam[3] - dichtam[1]) < 250 and (dichtam[2] - dichtam[0]) < 250:
                return None
            else:
                return crop.astype('uint8')
        else:
            return None
    else:
        return None

if __name__ == '__main__':
    #R, G, B order
    I = Image.open('sample4.tiff')
    I_numpy = np.array(I)
    c = apple_detect(I_numpy)

    if c is not None:
        pil_image = Image.fromarray(c)
        pil_image.show()
    else:
        print('Apple is not detected!')

    # If this code can detect an apple, return an RGB image (numpy array). Please normalize this image into [-1, 1]
    #     before feeding to the CNN model. (Ex: x /= 127.5; x -= 1)
    # Else, return None