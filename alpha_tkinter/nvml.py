from pynvml import *

nvmlInit()
count = nvmlDeviceGetCount()
for i in range(count):
    handle = nvmlDeviceGetHandleByIndex(i)
    name = nvmlDeviceGetName(handle)
    print(f"GPU {i}: {name()}")
nvmlShutdown()
