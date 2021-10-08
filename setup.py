from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in shopee_open_api/__init__.py
from shopee_open_api import __version__ as version

setup(
	name="shopee_open_api",
	version=version,
	description="Connect to your Shopee Open API and manage your shops from your website",
	author="Dap Official",
	author_email="siwatjames@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
