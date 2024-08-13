import re
import json

x = json.dumps([{'name': 'SegmentationTool', 'args': {'input_prompt': 'buildings', 'input_image': 'image_0'}}], indent=2)
print(x)
print(re.sub(r'image_(?P<num>[0-9]+)', '"<image_\g<num>>"', x))
x = re.sub(r'image_(P<num>[0-9]+)', '"<image_g<num>>"', x)
print(x)
