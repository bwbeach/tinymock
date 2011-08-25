from setuptools import setup, find_packages
import sys, os

version = '0.2.2'

setup(name='tinymock',
      version=version,
      description="Super-simple mock functions and objects.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Brian Beach',
      author_email='bwbeach@beachfamily.net',
      url='http://www.beachfamily.net/tinymock/',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
