"""Sample file for image segmentation tool"""
import GeoAwareGPT
quit()
import GeoAwareGPT.tools
import GeoAwareGPT.tools.image_segment
from PIL import Image
import time
import GeoAwareGPT
from GeoAwareGPT.tools.image_segment import SegmentationTool
import asyncio
# from GeoAwareGPT.tools.image_segment.segment import SegmentationTool - equivalent
# Loading image
img_path = input('Enter image path: ')
t0 = time.time()
img = Image.open(img_path)
# Loading prompt
prompt = 'tree'
t1 = time.time()

# Running model
tool: GeoAwareGPT.schema.BaseTool = SegmentationTool()
t2 = time.time()
img = asyncio.run(tool.run(input_image=img, input_prompt=prompt)).image
# Results in an error due to matplotlib being called with the wrong backend, 
# but doesn't cause any issues
# img = GeoAwareGPT.tools.image_segment.segment.segment_image_with_prompt(img, prompt)
# ^Alternative, but unnecessary way to run
t3 = time.time()

img.show()
img.save('test_image_segment.png')
print(f'Data Loading Time: {t1 - t0}')
print(f'Model Initialisation: {t2 - t1}')
print(f'Running time: {t3 - t2}')