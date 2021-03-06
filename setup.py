#!/usr/bin/env python3
from os import path

from setuptools import find_packages, setup

# read our README
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='earendil',
    url='https://github.com/agrif/earendil/',
    description='machine-readable IRC protocol specification',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Aaron Griffith',
    author_email='aargri@gmail.com',
    license='MIT',
    platforms=['any'],

    project_urls={
        'Source': 'https://github.com/agrif/earendil/',
        'Documentation': 'https://earendil-irc.readthedocs.io/en/latest/',
    },

    keywords='irc specification',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],

    setup_requires=[
        'setuptools_git >= 0.3',
        'better-setuptools-git-version >= 1.0',
    ],
    extras_require={
        'docs': ['mkdocs >= 1.0, < 1.1', 'mkautodoc >= 0.1.0'],
    },
    entry_points={
        'mkdocs.plugins': [
            'earendil-ircdef = earendil.ircdef.mkdocs:Plugin',
        ],
    },
    version_config={
        'version_format': '{tag}.dev{sha}',
    },

    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'lark-parser >= 0.8.0',
        'jinja2 >= 2.10.0',
        'markdown >= 3.2.0',
    ],
    python_requires='>=3.5',
    include_package_data=True,
    test_suite='tests',
)
