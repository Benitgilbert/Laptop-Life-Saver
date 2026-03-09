import os
from PIL import Image

def convert_to_ico(png_path, ico_path):
    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found.")
        return False
    
    img = Image.open(png_path)
    # Windows icons usually support multiple sizes, but 256x256 is good for high-DPI
    img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print(f"Successfully converted {png_path} to {ico_path}")
    return True

if __name__ == "__main__":
    convert_to_ico("c:/FYP/Logo.png", "c:/FYP/agent/Logo.ico")
