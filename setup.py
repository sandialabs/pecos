from setuptools import setup, find_packages
from distutils.core import Extension

DISTNAME = 'pecos'
VERSION = '0.1.8'
PACKAGES = ['pecos']
EXTENSIONS = []
DESCRIPTION = 'Python package for performance monitoring of time series data.'
LONG_DESCRIPTION = open('README.md').read()
AUTHOR = 'Pecos Developers'
MAINTAINER_EMAIL = 'kaklise@sandia.gov'
LICENSE = 'Revised BSD'
URL = 'https://github.com/sandialabs/pecos'

setuptools_kwargs = {
    'zip_safe': False,
    'install_requires': ['numpy >= 1.10.4',
                         'pandas >= 0.18.0',
                         'matplotlib',
                         'jinja2'],
    'scripts': [],
    'include_package_data': True
}

setup(name=DISTNAME,
      version=VERSION,
      packages=PACKAGES,
      ext_modules=EXTENSIONS,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      maintainer_email=MAINTAINER_EMAIL,
      license=LICENSE,
      url=URL,
      **setuptools_kwargs)
