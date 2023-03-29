# pyfirefly
python library for reverse engineered Adobe Firefly API

## Example Usage
The following example will request for 10 images of "flying cats" from Adobe Firefly and save those images.
```py
import asyncio
import aiohttp
import aiofiles

import pyfirefly
from pyfirefly.utils import ImageOptions

token = 'ey..' #replace with your bearer token

async def demo(prompt, num):
	a = await pyfirefly.Firefly(token)
  
	img = ImageOptions(a.image_styles)
	img.add_styles(['Photo', 'Blurry background', 'Origami'])

	tasks = []
	for i in range(num):
		tasks.append(a.text_to_image(prompt, **img.options))
 
	result = await asyncio.gather(*tasks)
  
	for i in range(num):
		async with aiofiles.open(f'{i}.jpeg', mode='wb+') as f:
			await f.write(result[i]['filedata'])

asyncio.run(demo('flying cats', 10))
```

## Todo:
- figure out how anonymous mode words
- add glyph_to_image function
