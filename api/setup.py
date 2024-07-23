# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pathlib
import re
from collections import defaultdict

import setuptools


def parse_reqs(filename='requirements.txt'):
  reqs = []
  reqs_extra = defaultdict(list)
  section = None
  for req in pathlib.Path(filename).read_text().split('\n'):
    req = req.strip()
    if not req:
      continue
    if req.startswith('## '):
      section = req[2:].strip()
      continue
    if req.startswith('#'):
      continue
    if section:
      reqs_extra[section].append(req)
    else:
      reqs.append(req)
  return reqs, dict(reqs_extra)


def parse_version(filename):
  text = (pathlib.Path(__file__).parent / filename).read_text()
  version = re.search(r"__version__ = '(.*)'", text).group(1)
  return version


setuptools.setup(
    name='expa',
    version=parse_version('expa/__init__.py'),
    author='Jurgis Pasukonis',
    author_email='jurgisp@gmail.com',
    url='https://github.com/jurgisp/expa',
    license='Apache 2.0',
    description='Metric logging and analysis for ML experiments',
    long_description=(
        pathlib.Path('README.md').read_text()
        if pathlib.Path('README.md').exists()
        else pathlib.Path('../README.md').read_text()
    ),
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    python_requires='>=3.9',
    include_package_data=True,
    install_requires=parse_reqs()[0],
    extras_require=parse_reqs()[1],
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Visualization',
    ],
)
