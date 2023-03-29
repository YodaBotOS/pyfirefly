import setuptools

with open('README.md', encoding='utf-8') as f:
    description = f.read()

setuptools.setup(
    name='pyfirefly',
    version='1.0',
    license='MIT',
    author='discordtehe',
    description='python library for reverse engineered Adobe Firefly API',
    packages = ['pyfirefly'],
    url='https://github.com/discordtehe/pyfirefly',
    install_requires=['aiohttp'],
    long_description=description,
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)