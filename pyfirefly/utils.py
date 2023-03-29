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
	'''Image options creator for text_to_image function.'''
	__slots__ = ['image_styles', 'options', 'ids', 'titles', 'groups']
	def __init__(self, image_styles: str):
		self.image_styles = image_styles
		self.options = {}
		self.ids = [i['id'] for i in image_styles]
		self.titles = [i['title'].lower() for i in image_styles]
		self.groups = set([i['group'].lower() for i in image_styles])
	
	def get_group_styles(self, group: str) -> list[dict]:
		return [i for i in self.options if i['group'] == group]

	def _is_valid_style(self, style: str) -> bool:
		style = style.lower()
		return style in self.ids or style in self.titles

	def _get_style_data(self, style: str) -> dict:
		style = style.lower()
		if style in self.ids:
			return self.image_styles[self.ids.index(style)]
		elif style in self.titles:
			return self.image_styles[self.titles.index(style)]
		else:
			raise Exception('Invalid style.')

	def set_aspect_ratio(self, aspect_ratio: str) -> None:
		aspect_ratio = aspect_ratio.lower()
		if aspect_ratio not in ASPECT_RATIOS:
			raise Exception('Invalid aspect ratio.')
		
		ratio = ASPECT_RATIOS[aspect_ratio]
		self.set_height(ratio['height'])
		self.set_width(ratio['width'])

	def set_height(self, height: str) -> None:
		self.options['height'] = height

	def set_width(self, width: str) -> None:
		self.options['width'] = width

	def set_steps(self, steps: int) -> None:
		self.options['steps'] = steps

	def set_fix_face(self, fix_face: bool) -> None:
		self.options['fix_face'] = fix_face

	def set_style(self, style: str) -> None:
		if not self._is_valid_style(style):
			raise Exception('Invalid style.')
		
		data = self._get_style_data(style)
		self.set_style_prompt(data['style_prompt'])
		self.set_anchor_prompt(data['anchor_prompt'])
	
	def set_style_promtp(self, style_prompt: str) -> None:
		self.options['style_prompt'] = style_prompt

	def set_anchor_promtp(self, anchor_prompt: str) -> None:
		self.options['anchor_prompt'] = anchor_prompt

	def add_styles(self, styles: list[str]) -> None:
		for s in styles:
			self.add_style(s)

	def add_style(self, style: str) -> None:
		if not self._is_valid_style(style):
			raise Exception('Invalid style.')
		
		data = self._get_style_data(style)
		self.add_style_prompt(data['style_prompt'])
		self.add_anchor_prompt(data['anchor_prompt'])

	def add_style_prompt(self, style_prompt: str) -> None:
		if 'style_prompt' not in self.options:
			self.options['style_prompt'] = ''
			prefix = ''
		else:
			prefix = ', '
		
		self.options['style_prompt'] += prefix + style_prompt

	def add_anchor_prompt(self, anchor_prompt: str) -> None:
		if 'anchor_prompt' not in self.options:
			self.options['anchor_prompt'] = ''
			prefix = ''
		else:
			prefix = ', '
		
		self.options['anchor_prompt'] += prefix + anchor_prompt