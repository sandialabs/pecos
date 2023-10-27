from setuptools import setup, find_packages
from distutils.core import Extension
import os
import re

DISTNAME = 'pecos'
PACKAGES = ['pecos']
EXTENSIONS = []
DESCRIPTION = 'Python package for performance monitoring of time series data.'
AUTHOR = 'Pecos Developers'
MAINTAINER_EMAIL = 'kaklise@sandia.gov'
LICENSE = 'Revised BSD'
URL = 'https://github.com/sandialabs/pecos'

setuptools_kwargs = {
    'zip_safe': False,
    'install_requires': ['numpy >= 1.10.4',
                         'pandas >= 0.18.0',
                         'matplotlib',
                         'jinja2',
                         'pytest'],
    'scripts': [],
    'include_package_data': True
}

# use README file as the long description
file_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(file_dir, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()
    
# get version from __init__.py
with open(os.path.join(file_dir, 'pecos', '__init__.py')) as f:
    version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        VERSION = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")
        
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
