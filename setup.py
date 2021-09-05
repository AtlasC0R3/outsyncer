from setuptools import setup
from outsyncer import __version__

with open('requirements.txt', 'r', encoding='utf-8') as f:
    install_requires = [line for line in f.read().splitlines() if len(line) > 0]

with open('README.md') as f:
    readme = f.read()

setup(name='outsyncer',
      version=__version__,
      description='A CLI app to sort song files/directories and synchronize music to devices',
      long_description=readme,
      long_description_content_type="text/markdown",
      url='https://github.com/AtlasC0R3/outsyncer',
      author='atlas_core',
      license='GPL-3.0',
      install_requires=install_requires,
      packages=['outsyncer'],
      python_requires=">=3.9",
      zip_safe=True)
