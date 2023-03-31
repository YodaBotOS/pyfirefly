import random

ASPECT_RATIOS = {
	'square': {
		'width': 1024,
		'height': 1024
	},
	'landscape': {
		'width': 1408,
		'height': 1024
	},
	'portrait': {
		'width': 1024,
		'height': 1408
	},
	'widescreen': {
		'width': 1792,
		'height': 1024
	}
}

class ImageOptions:
	'''
	Image options creator function.
	
	Parameters
	----------
	image_styles: list, optional
		List of image styles.
	text_presets: list, optional
		List of text presets.

	Notes
	-----
	access resulting options with img.options
	'''
	__slots__ = ['image_styles', 'text_presets', 'options', 'ids', 'titles', 'groups']
	def __init__(self, **kwargs):
		image_styles = kwargs.get('image_styles', [])
		text_presets = kwargs.get('text_presets', [])

		self.image_styles = {'data': image_styles}
		self.image_styles['ids'] = [i['id'] for i in image_styles]
		self.image_styles['titles'] = [i['title'].lower() for i in image_styles]
		self.image_styles['groups'] = set([i['group'].lower() for i in image_styles])

		self.text_presets = {'data': text_presets}
		self.text_presets['ids'] = [i['value'] for i in text_presets]
		self.text_presets['titles'] = [i['label'].lower() for i in text_presets]

		self.options = {}

	def _is_valid_style(self, style: str) -> bool:
		style = style.lower()
		return style in self.image_styles['ids'] or style in self.image_styles['titles']

	def _is_valid_preset(self, preset: str) -> bool:
		preset = preset.lower()
		return preset in self.text_presets['ids'] or preset in self.text_presets['titles']

	def _get_style_data(self, style: str) -> dict:
		style = style.lower()
		if style in self.image_styles['ids']:
			return self.image_styles['data'][self.image_styles['ids'].index(style)]
		elif style in self.image_styles['titles']:
			return self.image_styles['data'][self.image_styles['titles'].index(style)]
		else:
			raise Exception('Invalid style.')

	def _get_preset_data(self, preset: str) -> dict:
		preset = preset.lower()
		if preset in self.text_presets['ids']:
			return self.text_presets['data'][self.text_presets['ids'].index(preset)]
		elif preset in self.text_presets['titles']:
			return self.text_presets['data'][self.text_presets['titles'].index(preset)]
		else:
			raise Exception('Invalid text preset.')

	def set_aspect_ratio(self, aspect_ratio: str) -> None:
		'''
		Sets the aspect ratio of the image.

		Parameters
		----------
		aspect_ratio: str
			The aspect ratio to set. Can be one of ['square', 'landscape', 'portrait', 'widescreen']
		'''
		aspect_ratio = aspect_ratio.lower()
		if aspect_ratio not in ASPECT_RATIOS:
			raise Exception('Invalid aspect ratio.')
		
		ratio = ASPECT_RATIOS[aspect_ratio]
		self.set_height(ratio['height'])
		self.set_width(ratio['width'])

	def set_height(self, height: int) -> None:
		'''
		Sets the height of the image.
		'''
		self.options['height'] = height

	def set_width(self, width: int) -> None:
		'''
		Sets the width of the image.
		'''
		self.options['width'] = width

	def set_steps(self, steps: int) -> None:
		'''
		Sets the number of inference steps.
		'''
		self.options['steps'] = steps

	def set_fix_face(self, fix_face: bool) -> None:
		'''
		Sets whether to fix the face or not.
		'''
		self.options['fix_face'] = fix_face

	def set_style(self, style: str) -> None:
		'''
		Sets the style of the image.
		'''
		if not self._is_valid_style(style):
			raise Exception('Invalid style.')
		
		data = self._get_style_data(style)
		self.set_style_prompt(data['style_prompt'])
		self.set_anchor_prompt(data['anchor_prompt'])
	
	def set_style_prompt(self, style_prompt: str) -> None:
		'''
		Sets the style prompt.
		'''
		self.options['style_prompt'] = style_prompt

	def set_anchor_prompt(self, anchor_prompt: str) -> None:
		'''
		Sets the anchor prompt.
		'''
		self.options['anchor_prompt'] = anchor_prompt

	def add_styles(self, styles: list[str]) -> None:
		'''
		Adds multiple styles to the image.
		'''
		for s in styles:
			self.add_style(s)

	def add_style(self, style: str) -> None:
		'''
		Adds a style to the image.
		'''
		if not self._is_valid_style(style):
			raise Exception('Invalid style.')
		
		data = self._get_style_data(style)
		self.add_style_prompt(data['style_prompt'])
		self.add_anchor_prompt(data['anchor_prompt'])

	def add_style_prompt(self, style_prompt: str) -> None:
		'''
		Adds a style prompt to the image.
		'''
		if 'style_prompt' not in self.options:
			self.options['style_prompt'] = ''
			prefix = ''
		else:
			prefix = ', '
		
		self.options['style_prompt'] += prefix + style_prompt

	def add_anchor_prompt(self, anchor_prompt: str) -> None:
		'''
		Adds an anchor prompt to the image.
		'''
		if 'anchor_prompt' not in self.options:
			self.options['anchor_prompt'] = ''
			prefix = ''
		else:
			prefix = ', '
		
		self.options['anchor_prompt'] += prefix + anchor_prompt
	
	def set_pad_ratio(self, pad_ratio: float) -> None:
		'''
		Sets the pad ratio of the image.
		'''
		self.options['pad_ratio'] = pad_ratio
	
	def set_strength(self, strength: float) -> None:
		'''
		Sets the strength of the image. Between 0.0 and 1.0, higher values cause more variations but potentially inconsistent outcomes. Default is 0.5. See https://github.com/CompVis/stable-diffusion/blob/main/README.md for more info.
		'''
		self.options['strength'] = strength

	def set_seed(self, seed: str) -> None:
		'''
		Sets the seed of the image.
		'''
		self.options['seed'] = seed

	def set_description(self, description: str) -> None:
		'''
		Sets the description of the image. Used for text-effects.
		'''
		self.options['description'] = description

	def set_text_preset(self, preset: str, auto_set_seed: bool = True) -> None:
		'''
		Sets the text preset of the image. Used for text-effects.

		Parameters
		----------
		preset: str
			The text preset
		auto_set_seed: bool, optional
			Whether to automatically set the seed to a random seed suggestion. Default is True.
		'''
		if not self._is_valid_preset(preset):
			raise Exception('Invalid text preset.')
		
		data = self._get_preset_data(preset)
		self.set_description(data['prompt'])
		if auto_set_seed:
			self.set_seed(random.choice(data['seedSuggestions']))