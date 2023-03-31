# pyfirefly
python library for reverse engineered Adobe Firefly API

## Installing
```sh
pip install pyfirefly
```

## Example Usage
The following example will request for 10 images of "flying cats" from Adobe Firefly and save those images.
```py
import asyncio
import aiohttp
import aiofiles

import pyfirefly
from pyfirefly.utils import ImageOptions

token = 'ey...'  # replace with your bearer token


async def create_save_image(a, prompt, img_options, num):
    result = await a.text_to_image(prompt, **img_options)
    async with aiofiles.open(f'{num}.jpeg', mode='wb+') as f:
        await f.write(result['filedata'])


async def demo(prompt, num):
    a = await pyfirefly.Firefly(token)
    img = ImageOptions(a.image_styles)
    img.add_styles(['Photo', 'Blurry background', 'Origami'])

    tasks = [create_save_image(a, prompt, img.options, i) for i in range(num)]

    await asyncio.gather(*tasks)


asyncio.run(demo('flying cats', 10))
```

## Todo:
- figure out how anonymous mode words
- add glyph_to_image function
