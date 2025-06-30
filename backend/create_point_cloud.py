
import numpy as np
from PIL import Image
import pandas as pd
from pyntcloud import PyntCloud

def create_colored_point_cloud(rgb_path, depth_path, output_ply_path):
    """
    Generates a colored point cloud from an RGB image and a depth map.

    Args:
        rgb_path (str): Path to the RGB image file.
        depth_path (str): Path to the depth map image file.
        output_ply_path (str): Path to save the output .ply file.
    """
    try:
        # --- 1. Load Images ---
        print(f"Loading RGB image from {rgb_path}...")
        rgb_image = Image.open(rgb_path).convert("RGB")
        
        print(f"Loading depth map from {depth_path}...")
        # The depth map is often single-channel (grayscale)
        depth_image = Image.open(depth_path)

        # Ensure images have the same dimensions
        if rgb_image.size != depth_image.size:
            print("Error: RGB and depth images must have the same dimensions.")
            # Optional: Resize depth map to match RGB image
            print(f"Resizing depth map to {rgb_image.size} to match RGB image.")
            depth_image = depth_image.resize(rgb_image.size, Image.NEAREST)

        width, height = rgb_image.size
        
        rgb_array = np.array(rgb_image)
        depth_array = np.array(depth_image)

        # If the depth map has multiple channels (e.g., from a colormap),
        # convert it to a single grayscale value. We'll use the average.
        if depth_array.ndim == 3:
            print("Depth map has multiple channels, converting to grayscale.")
            depth_array = depth_array.mean(axis=2)

        # --- 2. Create Point Cloud Data ---
        print("Creating point cloud data...")
        
        # Create a grid of (x, y) coordinates
        x_coords, y_coords = np.meshgrid(np.arange(width), np.arange(height))
        
        # Flatten arrays to get a list of points
        x = x_coords.flatten()
        y = y_coords.flatten()
        # Invert the depth values so that darker pixels (lower values) are further away
        # and scale them to create a more pronounced 3D effect.
        # The scaling factor (e.g., 256) is empirical and can be adjusted.
        z = (255 - depth_array).flatten() / 256.0 * 100 # Adjust scaling factor as needed

        # Get RGB values for each point
        r = rgb_array[:, :, 0].flatten()
        g = rgb_array[:, :, 1].flatten()
        b = rgb_array[:, :, 2].flatten()

        # --- 3. Use pyntcloud to create and save the PLY file ---
        print("Building cloud with pyntcloud...")
        
        # Create a pandas DataFrame
        points_df = pd.DataFrame({
            "x": x,
            "y": y,
            "z": z,
            "red": r,
            "green": g,
            "blue": b
        })

        # Create a PyntCloud object from the DataFrame
        cloud = PyntCloud(points_df)
        
        print(f"Saving point cloud to {output_ply_path}...")
        cloud.to_file(output_ply_path)
        
        print("Point cloud successfully created and saved.")

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_colored_point_cloud(
        rgb_path="your_image.jpg",
        depth_path="depth.png",
        output_ply_path="output.ply"
    )
