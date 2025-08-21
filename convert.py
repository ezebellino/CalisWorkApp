from PIL import Image

img = Image.open("img/CalisWork.png")
img.save("img/CalisWork.ico", format="ICO", sizes=[(256, 256)])