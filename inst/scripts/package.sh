#!/bin/bash

version=1.1.2

# package
python3 setup.py sdist bdist_wheel
# upload
twine upload --repository-url https://test.pypi.org/legacy/ dist/ukcensusapi-$version*
#twine upload --repository-url https://upload.pypi.org/legacy/ dist/ukcensusapi-$version*

# test package in tmp env
virtualenv /tmp/env
source /tmp/env/bin/activate

# local wheel
#python3 -m pip install  ~/dev/UKCensusAPI/dist/ukcensusapi-1.1.1-py3-none-any.whl
# test pypi
#python3 -m pip install --index-url https://test.pypi.org/simple/ UKCensusAPI
# real pypi 
python3 -m pip install UKCensusAPI

# clean up
deactivate
rm -rf /tmp/env
