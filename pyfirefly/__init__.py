import aiohttp
import asyncio
import json
import random
import time
import uuid
from typing import (
    Awaitable,
    Optional
)

from .exceptions import (
	ImageGenerationDenied,
	Unauthorized,
	SessionExpired
)

class _Latin1BodyPartReader(aiohttp.multipart.BodyPartReader):
    async def text(self) -> Awaitable[str]:
        data = await self.read(decode=True)
        return data.decode('latin1')

class _Latin1MultipartReader(aiohttp.multipart.MultipartReader):
    async def next(self) -> Optional[_Latin1BodyPartReader]:
        part_reader = await super().next()
        if part_reader is not None:
            part_reader.__class__ = _Latin1BodyPartReader
        return part_reader

class Result:
	'''
	Represents a result from the Adobe Firefly API.

	Parameters
	----------
	image: bytes
		The image data.
	ext: str
		The image extension.
	metadata: dict
		The metadata.
	img_options: dict
		The image options that were used to generate the image.
	'''
	__slots__ = ['image', 'ext', 'metadata', 'img_options']
	def __init__(self, image: bytes, metadata: dict, ext: str, img_options: dict):
		self.image = image
		self.ext = ext
		self.metadata = metadata
		self.img_options = img_options

class Firefly:
	'''
	Reverse engineered Adobe Firefly API.

	Parameters
	----------
	auth: str
		The authorization bearer token to use.
	build: str, optional
		The build to use. Can be one of 'dev', 'stage', or 'prod'. Defaults to 'prod'.
	anonymous: bool, optional
		Whether to use anonymous mode. Not supported yet.
	fetch_image_assets: bool, optional
		Whether to fetch image assets. Defaults to True.
	fetch_text_assets: bool, optional
		Whether to fetch text assets. Defaults to True.
    '''
	__slots__ = ['headers', 'base', 'engine', 'session', 'image_styles', 'text_presets', 'text_fonts']

	URLS = {
		'default': {
			'dev': 'https://senseicore-stage-ue1.adobe.io/services/',
			'stage': 'https://senseicore-stage-ue1.adobe.io/services/',
			'prod': 'https://sensei-ue1.adobe.io/services/'
		},
		'anonymous': {
			'dev': 'https://senseicore-stage-ue1.adobe.io/anonymous/',
			'stage': 'https://senseicore-stage-ue1.adobe.io/anonymous/',
			'prod': 'https://sensei-ue1.adobe.io/anonymous/'
		}
	}

	DIFFUSION_ENGINES = {
		'dev': 'Classification:diffusion-service:Service-943088ea714543dd8289374cd1e92bb6',
		'stage': 'Classification:diffusion-service:Service-7367c21c82b946e7adb3995315de18a8',
		'prod': 'Classification:diffusion-service:Service-c742bc2eaae1491987dc00daff32fc07'
	}

	ASSET_BASE_URL = "https://clio-assets.adobe.com/clio-playground/"

	#https://stackoverflow.com/a/45364670
	async def __new__(cls, *args, **kwargs):
		instance = super().__new__(cls)
		await instance.__init__(*args, **kwargs)
		return instance

	async def __init__(self, auth: str, build: str='prod', anonymous: bool=False, fetch_image_assets: bool=True, fetch_text_assets: bool=True):
		if anonymous:
			raise NotImplementedError('Anonymous mode not supported yet.')
		
		self.headers = {
			'Origin': 'https://firefly.adobe.com',
			'Accept': 'multipart/form-data',
			'Authorization': 'Bearer '+auth.strip(),
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
			'x-api-key': 'clio-playground-web'
		}

		dif_type = 'anonymous' if anonymous else 'default'
		prod_url = Firefly.URLS[dif_type]['prod']
		self.base = Firefly.URLS[dif_type].get(build, prod_url)

		prod_engine = Firefly.DIFFUSION_ENGINES['prod']
		self.engine = Firefly.DIFFUSION_ENGINES.get(build, prod_engine)

		self.session = {
			'id': None,
			'expires_at': 0
		}

		asset_tasks = []
		if fetch_image_assets:
			asset_tasks.append(Firefly._get_image_styles())
		if fetch_text_assets:
			asset_tasks.append(Firefly._get_text_presets())
			asset_tasks.append(Firefly._get_text_fonts())
		
		if asset_tasks:
			assets = await asyncio.gather(*asset_tasks)
			for a in assets:
				if 'styles' in a:
					self.image_styles = a['styles']
				elif 'presets' in a:
					self.text_presets = a['presets']
				elif 'fonts' in a:
					self.text_fonts = a['fonts']

		await self.create_session()

	@property
	def has_time_left(self) -> bool:
		'''
		Whether the session has time left.
		'''
		return time.time() - self.session['expires_at'] <= 0

	@staticmethod
	async def _get_image_styles() -> list[dict]:
		'''
		Gets the image styles.
		'''
		url = f'{Firefly.ASSET_BASE_URL}image-styles/v4/en-US/content.json'
		headers = {
			'Origin': 'https://firefly.adobe.com',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
		}
		async with aiohttp.ClientSession(headers=headers) as s:
			async with s.get(url) as resp:
				data = await resp.json()
				return data

	@staticmethod
	async def _get_text_presets() -> list[dict]:
		'''
		Gets the text presets.
		'''
		url = f'{Firefly.ASSET_BASE_URL}text-presets/v3/en-US/content.json'
		headers = {
			'Origin': 'https://firefly.adobe.com',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
		}
		async with aiohttp.ClientSession(headers=headers) as s:
			async with s.get(url) as resp:
				data = await resp.json()
				return data

	@staticmethod
	async def _get_text_fonts() -> list[dict]:
		'''
		Gets the text fonts.
		'''
		url = f'{Firefly.ASSET_BASE_URL}text-fonts/v2/en-US/content.json'
		headers = {
			'Origin': 'https://firefly.adobe.com',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
		}
		async with aiohttp.ClientSession(headers=headers) as s:
			async with s.get(url) as resp:
				data = await resp.json()
				return data

	@staticmethod
	def _check_gen_status(metadata: dict) -> None:
		values = metadata['values']
		if values.get('gi_GEN_STATUS'):
			status = values['gi_GEN_STATUS']['value']
		else:
			status = values['gt_GEN_STATUS']['value']
		if bool(1 & status):
			raise ImageGenerationDenied('Denied')
		elif bool(2 & status):
			raise ImageGenerationDenied('BlockedClassNSFW')
		elif bool(4 & status):
			raise ImageGenerationDenied('BlockedClassArtist')
		elif bool(8 & status):
			raise ImageGenerationDenied('DeniedSilent')
		elif bool(16 & status):
			raise ImageGenerationDenied('NotEnglish')
		elif bool(32 & status):
			raise ImageGenerationDenied('PostProcessingNSFW')

	async def create_session(self, duration:int = 3600) -> str:
		'''
		Creates a session.

		Parameters
		----------
		duration: The duration of the session in seconds.

		Returns
		-------
		The session ID string.
		'''
		url = f'{self.base}session/create'

		formdata = aiohttp.FormData()
		formdata.add_field('contentAnalyzerRequests', json.dumps({'session_ttl':duration}), content_type='form-data')

		async with aiohttp.ClientSession(headers=self.headers) as s:
			async with s.post(url, data=formdata) as resp:
				if resp.status == 401:
					raise Unauthorized('Bearer auth token is invalid.')
				self.session['id'] = resp.headers.get('x-session-id', '')
				if self.session['id']:
					self.session['expires_at'] = time.time() + duration
				return self.session['id']

	async def text_to_image(self, prompt: str, **kwargs) -> Result:
		'''
		Generates an image from a text prompt.

		Parameters
		----------
		prompt: str
			The text prompt.
		seed: int, optional
			The seed for the image generation. Default is random.
		style_prompt: str, optional
			The style prompt for the image generation. Default is None.
		anchor_prompt: str, optional
			The anchor prompt for the image generation. Default is None.
		steps: int, optional
			The number of inference steps. Default is 40.
		width: int,	optional
			The width of the image. Default is 1024.
		height: int, optional
			The height of the image. Default is 1024.
		fix_face: bool, optional
			Whether to fix the face. Default is True.
		
		Returns
		-------
		pyfirefly.Result

		Raises
		------
		pyfirefly.SessionExpired, pyfirefly.Unauthorized, pyfirefly.ImageGenerationDenied
		'''
		if not self.has_time_left:
			raise SessionExpired('Create a new session using `await create_session()`. You can check for time left using `has_time_left`.')

		url = f'{self.base}v2/predict'

		seed = kwargs.get('seed', random.randint(0, 100000))

		style_prompt = kwargs.get('style_prompt')
		anchor_prompt = kwargs.get('anchor_prompt')
		advanced_options = { 'num_inference_steps': kwargs.get('steps', 40) }
		if style_prompt:
			advanced_options['style_prompt'] = style_prompt
		if anchor_prompt:
			advanced_options['anchor_prompt'] = anchor_prompt
		
		settings = {
			'sensei:name': 'SelectionParse v2',
			'sensei:invocation_mode': 'synchronous',
			'sensei:invocation_batch': False,
			'sensei:in_response': False,
			'sensei:engines': [
				{
					'sensei:execution_info': {
						'sensei:engine': self.engine
					},
					'sensei:inputs': {},
					'sensei:outputs': {
						'spl:response': {
							'dc:format': 'application/json',
							'sensei:multipart_field_name': 'spl:response',
						},
						'gt_GEN_IMAGE': {
							'dc:format': 'image/jpeg',
							'sensei:multipart_field_name': 'outfile',
						},
					},
					'sensei:params': {
						'spl:request': {
							'graph': {'uri': 'urn:graph:Text2Image_v2'},
							'params': [
								{'name': 'gi_SEED', 'type': 'scalar', 'value': seed},
								{'name': 'gi_NUM_STEPS', 'type': 'scalar', 'value': kwargs.get('steps', 40)},
								{'name': 'gi_OUTPUT_WIDTH', 'type': 'scalar', 'value': kwargs.get('width', 1024)},
								{'name': 'gi_OUTPUT_HEIGHT', 'type': 'scalar', 'value': kwargs.get('height', 1024)},
								{
									'name': 'gi_ADVANCED',
									'type': 'string',
									'value': json.dumps(advanced_options),
								},
								{'name': 'gi_LANGUAGE', 'type': 'string', 'value': 'en-US'},
								{'name': 'gi_USE_FACE_FIX', 'type': 'boolean', 'value': kwargs.get('fix_face', True)},
							],
							'inputs': {
								'gi_PROMPT': {
									'id': str(uuid.uuid4()),
									'type': 'string',
									'value': prompt,
								}
							},
							'outputs': {
								'gt_GEN_IMAGE': {
									'id': str(uuid.uuid4()),
									'type': 'image',
									'expectedMimeType': 'image/jpeg',
								},
								'gt_GEN_STATUS': {
									'id': str(uuid.uuid4()),
									'type': 'scalar',
								},
							},
						}
					},
				}
			],
		}

		formdata = aiohttp.FormData()
		formdata.add_field('contentAnalyzerRequests', json.dumps(settings), content_type='form-data')

		new_headers = dict(self.headers)
		new_headers['x-session-id'] = self.session['id']
		new_headers['x-transaction-id'] = str(uuid.uuid4())
		new_headers['prefer'] = 'respond-sync, wait=100'

		async with aiohttp.ClientSession(headers=new_headers) as s:
			async with s.post(url, headers=new_headers, data=formdata) as resp:
				if resp.status == 401:
					raise Unauthorized('Unauthorized. Bearer auth token is invalid.')
				reader = _Latin1MultipartReader(resp.headers, resp.content)
				metadata = None
				image = None
				while True:
					part = await reader.next()
					if part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/json':
						metadata = await part.json()
					elif part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'image/jpeg':
						image = await part.read(decode=False)
					if metadata and image:
						break

				# Check if the image generation was successful
				Firefly._check_gen_status(metadata)

				gen_options = {
					'seed': seed,
					'style_prompt': kwargs.get('style_prompt'),
					'anchor_prompt': kwargs.get('anchor_prompt'),
					'steps': kwargs.get('steps', 40),
					'width': kwargs.get('width', 1024),
					'height': kwargs.get('height', 1024),
					'fix_face': kwargs.get('fix_face', True)
				}
				return Result(image, metadata, 'jpeg', gen_options)

	async def glyph_to_image(self, glyph: bytes, **kwargs) -> Result:
		'''
		Generates an image from a glyph (webp image data) and prompt.

		Parameters
		----------
		glyph: bytes
			The glyph to use. Must be a webp image (bytes). The non-transparent pixels will be filled in by Adobe Firefly.
		description: str
			Describe the text/fill effects you want to generate.
		seed: int, optional
			The seed for the image generation. Default is random.
		steps: int, optional
			The number of inference steps. Default is 30.
		width: int, optional
			The width of the image. Default is 1024.
		height: int, optional
			The height of the image. Default is 1024.
		pad_ratio: float, optional
			The padding ratio. Default is 0.5.
		strength: float, optional
			between 0.0 and 1.0, higher values cause more variations but potentially inconsistent outcomes. Default is 0.5. See https://github.com/CompVis/stable-diffusion/blob/main/README.md for more info.

		Returns
		-------
		pyfirefly.Result
		
		Raises
		------
		pyfirefly.SessionExpired, pyfirefly.Unauthorized, pyfirefly.ImageGenerationDenied
		'''
		if not self.has_time_left:
			raise SessionExpired('Create a new session using `await create_session()`. You can check for time left using `has_time_left`.')

		if not kwargs.get('description'):
			raise ValueError('You must provide a description.')

		url = f'{self.base}v2/predict'

		seed = kwargs.get('seed', random.randint(0, 100000))
		advanced_options = { 'num_inference_steps': kwargs.get('steps', 30) }

		settings = {
			"sensei:name": "SelectionParse v2",
			"sensei:invocation_mode": "synchronous",
			"sensei:invocation_batch": False,
			"sensei:in_response": False,
			"sensei:engines": [
				{
					"sensei:execution_info": {
						"sensei:engine": self.engine
					},
					"sensei:inputs": {
						"gi_GLYPHMASK": {
							"dc:format": "image/webp",
							"sensei:multipart_field_name": "gi_GLYPHMASK",
						}
					},
					"sensei:outputs": {
						"spl:response": {
							"dc:format": "application/json",
							"sensei:multipart_field_name": "spl:response",
						},
						"gi_GEN_IMAGE": {
							"dc:format": "image/webp",
							"sensei:multipart_field_name": "outfile",
						},
					},
					"sensei:params": {
						"spl:request": {
							"graph": {"uri": "urn:graph:Glyph2Image_v2"},
							"params": [
								{"name": "gi_SEED", "type": "scalar", "value": seed},
								{"name": "gi_NUM_STEPS", "type": "scalar", "value": kwargs.get('steps', 30) },
								{"name": "gi_OUTPUT_WIDTH", "type": "scalar", "value": kwargs.get('width', 1024) },
								{"name": "gi_OUTPUT_HEIGHT", "type": "scalar", "value": kwargs.get('height', 1024) },
								{
									"name": "gi_ADVANCED",
									"type": "string",
									"value": json.dumps(advanced_options),
								},
								{"name": "gi_LANGUAGE", "type": "string", "value": "en-us"},
								{"name": "gi_PAD_RATIO", "type": "scalar", "value": kwargs.get('pad_ratio', -1)},
								{"name": "gi_STRENGTH", "type": "scalar", "value": kwargs.get('strength', 0.5) },
							],
							"inputs": {
								"gi_PROMPT": {
									"id": str(uuid.uuid4()),
									"type": "string",
									"value": kwargs.get('description'),
								},
								"gi_GLYPHMASK": {
									"id": str(uuid.uuid4()),
									"type": "image",
									"mimeType": "image/webp",
								},
							},
							"outputs": {
								"gi_GEN_IMAGE": {
									"id": str(uuid.uuid4()),
									"type": "image",
									"expectedMimeType": "image/webp",
								},
								"gi_GEN_STATUS": {
									"id": str(uuid.uuid4()),
									"type": "scalar",
								},
							},
						}
					},
				}
			],
		}

		formdata = aiohttp.FormData()
		formdata.add_field('contentAnalyzerRequests', json.dumps(settings), content_type='form-data')
		formdata.add_field('gi_GLYPHMASK', glyph, filename='blob', content_type='image/webp')

		new_headers = dict(self.headers)
		new_headers['x-session-id'] = self.session['id']
		new_headers['x-transaction-id'] = str(uuid.uuid4())
		new_headers['prefer'] = 'respond-sync, wait=100'

		async with aiohttp.ClientSession(headers=new_headers) as s:
			async with s.post(url, headers=new_headers, data=formdata) as resp:
				if resp.status == 401:
					raise Unauthorized('Unauthorized. Bearer auth token is invalid.')
				reader = _Latin1MultipartReader(resp.headers, resp.content)
				metadata = None
				image = None
				while True:
					part = await reader.next()
					if part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/json':
						metadata = await part.json()
					elif part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'image/webp':
						image = await part.read(decode=False)
					if metadata and image:
						break

				# Check if the image generation was successful
				Firefly._check_gen_status(metadata)

				gen_options = {
					'description': kwargs.get('description'),
					'seed': seed,
					'steps': kwargs.get('steps', 30),
					'width': kwargs.get('width', 1024),
					'height': kwargs.get('height', 1024),
					'pad_ratio': kwargs.get('pad_ratio', -1),
					'strength': kwargs.get('strength', 0.5)
				}
				return Result(image, metadata, 'webp', gen_options)