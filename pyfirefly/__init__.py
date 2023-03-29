import aiohttp
import asyncio
import json
import random
import time
import uuid

class Firefly:
	'''
	Reverse engineered Adobe Firefly API.

	:param auth: The authorization bearer token to use.
	:param build: The build to use. Can be one of 'dev', 'stage', or 'prod'.
	:param anonymous: Whether to use anonymous mode. Not supported yet.
	:param fetch_image_assets: Whether to fetch image assets.
	:param fetch_text_assets: Whether to fetch text assets.

	Example usage:
	```py
	import aiofiles
	import aiohttp
	import asyncio
	import pyfirefly

	async def demo(prompt, num = 4):
		a = await pyfirefly.Firefly(token)

		tasks = []
		for i in range(num):
			tasks.append(a.text_to_image(prompt))
		result = await asyncio.gather(*tasks)

		for i in range(num):
			async with aiofiles.open(f'{i}.jpeg', mode='wb+') as f:
				await f.write(result[i]['filedata'])
	
	asyncio.run(demo('flying pigs'))
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
			raise Exception('Anonymous mode not supported yet.')
		
		self.headers = {
			'Origin': 'https://firefly.adobe.com',
			'Accept': 'multipart/form-data',
			'Authorization': 'Bearer '+auth,
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
			asset_tasks.append(Firefly.get_image_styles())
		if fetch_text_assets:
			asset_tasks.append(Firefly.get_text_presets())
			asset_tasks.append(Firefly.get_text_fonts())
		
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
	async def get_image_styles() -> list[dict]:
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
	async def get_text_presets() -> list[dict]:
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
	async def get_text_fonts() -> list[dict]:
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

	async def create_session(self, duration:int = 3600) -> str:
		'''
		Creates a session.

		:param duration: The duration of the session in seconds.

		:return: The session ID string.
		'''
		url = f'{self.base}session/create'

		formdata = aiohttp.FormData()
		formdata.add_field('contentAnalyzerRequests', json.dumps({'session_ttl':duration}), content_type='form-data')

		async with aiohttp.ClientSession(headers=self.headers) as s:
			async with s.post(url, data=formdata) as resp:
				if resp.status == 401:
					raise Exception('Unauthorized. Bearer auth token is invalid.')
				self.session['id'] = resp.headers.get('x-session-id', '')
				if self.session['id']:
					self.session['expires_at'] = time.time() + duration
				return self.session['id']

	async def text_to_image(self, prompt: str, **kwargs) -> dict:
		'''
		Generates an image from a text prompt.

		:param prompt: The text prompt.
		:param kwargs: Additional arguments. Can be generated using the utils.ImageOptions class
			:seed: The seed for the image generation. Default is random.
			:style_prompt: The style prompt for the image generation. Default is None.
			:anchor_prompt: The anchor prompt for the image generation. Default is None.
			:steps: The number of inference steps. Default is 40.
			:width: The width of the image. Default is 1024.
			:height: The height of the image. Default is 1024.
			:fix_face: Whether to fix the face. Default is True.
		
		:return: The image data.
			:metadata: The metadata of the response.
			:filedata: The image bytes.
		'''
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

		if not self.has_time_left:
			raise Exception('Session expired. Create one using `await self.create_session()`')

		new_headers = dict(self.headers)
		new_headers['x-session-id'] = self.session['id']
		new_headers['x-transaction-id'] = str(uuid.uuid4())
		new_headers['prefer'] = 'respond-sync, wait=100'

		async with aiohttp.ClientSession(headers=new_headers) as s:
			async with s.post(url, headers=new_headers, data=formdata) as resp:
				if resp.status == 401:
					raise Exception('Unauthorized. Bearer auth token is invalid.')
				reader = aiohttp.MultipartReader.from_response(resp)
				metadata = None
				filedata = None
				while True:
					part = await reader.next()
					if part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'application/json':
						metadata = await part.json()
					elif part.headers[aiohttp.hdrs.CONTENT_TYPE] == 'image/jpeg':
						filedata = await part.read(decode=False)
					if metadata and filedata:
						break
				return {
					'metadata': metadata,
					'filedata': filedata
				}