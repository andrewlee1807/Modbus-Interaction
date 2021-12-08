from pypylon import pylon
import platform
import time

t = time.time()

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
converter = pylon.ImageFormatConverter()
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
converter.OutputPixelFormat = pylon.PixelType_RGB8packed
cam_on_off = True
file_num = 0
while camera.IsGrabbing() and cam_on_off:
    file_num += 1
    t1= time.time()
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    if grabResult.GrabSucceeded():
        image = converter.Convert(grabResult)
        img = image.GetArray()

        pylonImage = pylon.PylonImage()
        pylonImage.AttachGrabResultBuffer(grabResult)
        filename = f"saved_pypylon_img_{file_num}.tiff"
        img_tiff = pylon.ImageFileFormat_Tiff
        pylonImage.Save(pylon.ImageFileFormat_Tiff, filename)
        
        #temp = open(f"taved_pypylon_buffer_.txt", "w")
        #temp.write(str(img_buffer))
        #temp.close()
    print(time.time()-t1)
        
    grabResult.Release()
    break
camera.StopGrabbing()


# img = pylon.PylonImage()
# tlf = pylon.TlFactory.GetInstance()

# cam = pylon.InstantCamera(tlf.CreateFirstDevice())
# cam.Open()
# cam.StartGrabbing()

# with cam.RetrieveResult(2000) as result:
#     t1 = time.time()
#     # Calling AttachGrabResultBuffer creates another reference to the
#     # grab result buffer. This prevents the buffer's reuse for grabbing.
#     img.AttachGrabResultBuffer(result)
#     filename = "saved_pypylon_img_.png" 
#     img.Save(pylon.ImageFileFormat_Png, filename)

#     # In order to make it possible to reuse the grab result for grabbing
#     # again, we have to release the image (effectively emptying the
#     # image object).
#     img.Release()
#     print(time.time() - t1)
# print(time.time() - t)
# cam.StopGrabbing()
# cam.Close()