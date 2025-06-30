import cv2
import torch
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

try:
    # --- 1. 加载模型和变换 ---
    # 从 PyTorch Hub 加载 MiDaS 模型和相应的变换
    # 'DPT_Large' 是一个性能很好的模型
    model_type = "DPT_Large"
    midas = torch.hub.load("MiDaS", model_type, source="local", path=".")

    # 将模型移动到可用的设备（GPU或CPU）
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    midas.to(device)
    midas.eval()

    # 加载与所选模型匹配的变换
    midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    transform = midas_transforms.dpt_transform if model_type == "DPT_Large" or model_type == "DPT_Hybrid" else midas_transforms.small_transform

    # --- 2. 加载并预处理图像 ---
    # 定义输入和输出文件名
    input_filename = "your_image.jpg"
    output_filename = "depth.png"
    
    # 使用 OpenCV 加载图像
    img = cv2.imread(input_filename)
    if img is None:
        raise FileNotFoundError(f"错误：无法找到或打开图像文件 '{input_filename}'。请确保文件存在于正确的路径。")

    # 将 OpenCV 的 BGR 格式转换为 RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 应用 MiDaS 变换将图像转换为模型所需的张量格式
    input_batch = transform(img).to(device)

    # --- 3. 模型推理 ---
    with torch.no_grad():
        prediction = midas(input_batch)

        # 将预测结果调整为输入图像的尺寸
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    # 将预测结果（深度图）移动到 CPU 并转换为 NumPy 数组
    depth_map = prediction.cpu().numpy()

    # --- 4. 显示并保存结果 ---
    print(f"深度图已生成，正在显示结果...")

    # 使用 Matplotlib 显示深度图
    plt.figure(figsize=(10, 10))
    plt.imshow(depth_map, cmap="plasma") # 'plasma' 或 'inferno' 是很好的颜色映射
    plt.title("Generated Depth Map")
    plt.colorbar(label="Depth")
    plt.axis('off')
    plt.show()

    # 使用 Matplotlib 保存深度图为 .png 文件
    # cmap='plasma' 使得保存的图像与显示的图像颜色一致
    plt.imsave(output_filename, depth_map, cmap='plasma')
    
    print(f"深度图已成功保存为 '{output_filename}'")

except FileNotFoundError as e:
    print(e)
except Exception as e:
    print(f"发生未知错误: {e}")
    print("请确保您已安装所有必需的库: pip install torch torchvision opencv-python matplotlib timm")