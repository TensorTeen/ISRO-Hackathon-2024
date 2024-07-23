"""Segmentation tool. 

Running this module on its own only runs in test mode (testing schema only)

Classes:
    SegmentationTool: Derives from BaseTool for calling
"""

from typing import Optional
from io import BytesIO
from PIL import Image
import asyncio

from samgeo.text_sam import LangSAM

from .logger import Logger, Recovery # Disabled by default
from ...schema.schema import BaseTool
log = Logger().log

bbox_threshold = 0.24
text_threshold = 0.24

def open_image(image: str|Image.Image) -> Image.Image:
    if not (isinstance(image, str) or isinstance(image, Image.Image)):
        raise TypeError(f"""Image should be a string or PIL image, not {type(image)}.
{type(image).mro() = }""")
    img = Image.open(image).convert('RGB') if isinstance(image, str) else image.convert('RGB')
    try:
        img.load()
    except OSError as e:
        raise ValueError('Image seems to be truncated or is not loading.\
                         \nPIL is refusing to load the image') from e
    except Exception as e:
        raise RuntimeError('Error when loading image.') from e
    return img

def segment_image_with_prompt(image: str|Image.Image, prompt: str, 
                              output: Optional[str|BytesIO] = None, 
                              show_boxes: bool = True, 
                              title: str = 'Image Segmentation: {}',
                              recovery_if_error: bool = True,
                              test=False
                              ) -> Image.Image:
    """
    Segment the image

    Args:
        image (str|PIL.Image.Image): Filepath or PIL image (not required to be tiff)  
        prompt: Text prompt  
        output (Optional[str|BytesIO]): Path to save a file (otherwise, it will be 
            displayed in the notebook) An image will be returned anyway  
        show_boxes (bool): whether bounding boxes or only segmentation  
        title (str): matplotlib plot title  
        recovery_if_error (bool): Careful - can cause large delay/file size if \
            prediction fails. Makes a pickle of the output of `sam.predict()`  
        test (bool): Decides if only testing model schema (input/output)

    Returns:
        Whatever sam.predict returns: masks, boxes, phrase, logits
    """
    if test:
        from time import sleep
        # print('Testing schema only...')
        sleep(3)
        return open_image(image)
    if not output:
        output = BytesIO()
    image = open_image(image)
    sam = LangSAM()
    out = sam.predict(image, prompt, 
                      box_threshold=bbox_threshold, 
                      text_threshold=text_threshold,
                      return_results=True)
    with Recovery(out) as recovery:
        sam.show_anns(
            cmap="Greens",
            add_boxes=show_boxes,
            box_color="red", # seems to be ignored if not showing boxes
            title=None, # We don't actually want this
            blend=True, # False simply hides the original image - makes no sense
            output=output
        )
        # Raises an exception, which is ignored
        output_image = Image.open(output)
        output_image.load()
    return output_image


class SegmentationTool(BaseTool):
    """
    Tool for image segmentation using segment-geospatial library

    Attributes:
        test (bool): Decides if this module is being run in test mode
    
    """
    def __init__(self, test_schema=False):
        """
        Constructor for SegmentationTool

        Args:
            test_schema (bool): In case you just want to check schema
        """
        name = 'SegmentationTool'
        description = f'Placeholder:{segment_image_with_prompt.__doc__}'
        version = '0.1'
        super().__init__(name, description, version)
        self.test = test_schema
        if self.test:
            import warnings
            warnings.warn('Running in testing mode - simply an identity \
                           function with a 3 second wait', 
                           category=UserWarning)

    async def run(self, input_prompt: str, input_image: Image.Image|str) -> Image.Image:
        """
        Segment an image based on a text prompt. 

        Args:
            input_prompt (str): The input text. 
                Should preferably be a single word, as the model struggles with logic
            input_image (PIL.Image.Image|str): An input image or a file path (to an image)

        Returns:
            PIL.Image.Image: The segmented image
        
        Raises:
            Runtime Error: If the input image can't be loaded by PIL
        """
        # str is for testing
        result = await asyncio.to_thread(segment_image_with_prompt, input_image, input_prompt, recovery_if_error=False, test=self.test)
        # works
        return result
    
async def main() -> None:
    """Runs module in test mode. Run the proper test in tests to see how to call the model properly"""
    import asyncio
    import time
    model = SegmentationTool(True)
    path = input('Enter path to image: ')
    task_1 = asyncio.create_task((model.run('buildings', path)))
    print('Started running image segmentation tool 1')
    task_2 = asyncio.create_task((model.run('buildings', path)))
    print('Started running image segmentation tool 2')
    remaining = [asyncio.create_task((model.run('buildings', path))) for i in range(50)]
    time.sleep(3)
    t0 = time.time()
    await asyncio.gather(task_1, task_2, *remaining)
    print(f'Time Taken to run 52 3-second sleeps = {time.time() - t0}')
    # Time Taken to run 52 3-second sleeps = 16 (~ 16 +- 0.2)
if __name__ == '__main__':
    # python -m GeoAwareGPT.tools.image_segment.segment
    import asyncio
    import time
    asyncio.run(main())
    asyncio.run(main())
    print('Finished')
    
