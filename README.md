# Modbus-Interaction

## Start the application:

```sudo python3 main.py```

## Structure

```
.
├── camera.py # test camera with console output
├── cameraview_PYTHON # test camera with UI
│   ├── camera_connector.py
│   ├── image_viewer.py
│   ├── main.py
│   ├── mainwindow_ui.py
│   ├── output.txt
│   ├── __pycache__
│   ├── pylon 설치방법
│   ├── test
│   └── ui
├── data # test example photos
│   ├── defective
│   └── ok
├── guide.txt
├── jetson_api.py
├── labels.txt
├── lib
│   └── modbus
├── main.py
├── models
│   ├── resnet18.onnx
│   └── resnet18.onnx.1.1.8001.GPU.FP16.engine
├── myconfig.py # config the function codes
├── officialCodeCrop.py # pre-processing
├── README.md
├── RGB_order_OfficialCodeCrop.py  # pre-processing
├── run.sh
├── test # test without protocal
│   ├── predict_camera.py
│   ├── predict_time.py
│   └── test.py
└── utils.py 
```
