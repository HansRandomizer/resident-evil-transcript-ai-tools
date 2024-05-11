# When replacing textures for RE1 using RE1MV https://lgt.createaforum.com/new-board-17/emdviewer-a-tool-to-edit-emd-files/ 
# it requires you to import 8bit color palette bitmaps. This script converts your texture in a compatible format

from PIL import Image
import os

# place images in dir and post path here... (no env file support, yet ... ) 
directory = ""

# Iterate over all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".bmp"):
        # Construct the full file path
        filepath = os.path.join(directory, filename)
        image = Image.open(filepath)
        
        # this palatte will make sure its compatible with RE1MV
        palette_image = image.convert("P", palette=Image.ADAPTIVE, colors=256)
        
        # we will overwrite the existing files
        palette_image.save(filename)
        
        print(f"Processed: {filename}")