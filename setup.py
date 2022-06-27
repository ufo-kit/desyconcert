"""Installation script for DESY Concert plugin."""
from setuptools import setup, find_packages
import desyconcert


setup(
    name='desyconcert',
    python_requires='>=3.7',
    version=desyconcert.__version__,
    author='Tomas Farago',
    author_email='tomas.farago@kit.edu',
    url='http://ankagit.anka.kit.edu/concert/desyconcert',
    description='DESY synchrotron plugin for Concert control system',
    long_description=open('README.rst').read(),
    exclude_package_data={'': ['README.rst']},
    install_requires=['concert'],
    packages=find_packages(),
)
