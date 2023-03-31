# pyfirefly
python library for reverse engineered Adobe Firefly API

## Installing
```
pip install pyfirefly
```

## Example Usage
#### Text to Image
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
    async with aiofiles.open(f'{num}.{result.ext}', mode='wb+') as f:
        await f.write(result.image)


async def demo(prompt, num):
    a = await pyfirefly.Firefly(token)
    img = ImageOptions(image_styles = a.image_styles)
    img.add_styles(['Photo', 'Blurry background', 'Origami'])

    tasks = [create_save_image(a, prompt, img.options, i) for i in range(num)]

    await asyncio.gather(*tasks)


asyncio.run(demo('flying cats', 10))
```

#### Glyph to Image
The following example will request for 10 images of a glyph.webp image that has "bundle of colorful electric wires" as the fill effect. [example webp image](https://github.com/discordtehe/pyfirefly/blob/main/glyph.webp)
```py
import asyncio
import aiohttp
import aiofiles

import pyfirefly
from pyfirefly.utils import ImageOptions

token = 'ey...'  # replace with your bearer token

async def create_save_image(a, glyph, img_options, num):
    result = await a.glyph_to_image(glyph, **img_options)
    async with aiofiles.open(f'{num}.{result.ext}', mode='wb+') as f:
        await f.write(result.image)


async def demo(input_fn, num):
    async with aiofiles.open('./glyph.webp', mode='rb') as f:
        glyph = await f.read()

    a = await pyfirefly.Firefly(token)
    img = ImageOptions(text_presets = a.text_presets)
    img.set_text_preset('wires')

    tasks = [create_save_image(a, glyph, img.options, i) for i in range(num)]

    await asyncio.gather(*tasks)


asyncio.run(demo('glyph.webp', 10))
```
