import cv2
import numpy as np
import rasterio

# 打开GeoTIFF文件
with rasterio.open('raw_1200_rd_rf_or1021.tif') as src:
    # 读取数据
    data = src.read()
    # 打印数据形状（例如，如果是RGB图像，则为高度x宽度x通道数）
    print(data.shape)
    
    # 获取元数据
    meta = src.meta
    print(meta)
    
    # 获取坐标参考系统信息
    crs = src.crs
    print(crs)
    
    # 获取变换参数（用于将像素坐标转换为地理坐标）
    transform = src.transform
    print(transform)

