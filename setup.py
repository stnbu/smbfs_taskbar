# -*- coding: utf-8 -*-

from setuptools import setup
import os

import smbfs_taskbar

with open('README.rst', 'w') as f:
    f.write(smbfs_taskbar.__doc__)

NAME = 'smbfs_taskbar'

def read(file):
    with open(file, 'r') as f:
        return f.read().strip()

VERSION = read('VERSION')

base_kwargs = dict(
    name=NAME,
    version=VERSION,
    description='',
    long_description=read('README.rst'),
    author='Mike Burr',
    author_email='mburr@unintuitive.org',
    url='https://github.com/stnbu/{0}'.format(NAME),
    download_url='https://github.com/stnbu/{0}/archive/master.zip'.format(NAME),
    provides=[NAME],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python',
        'Environment :: MacOS X :: Cocoa',
    ],
    packages=[NAME],
    keywords=[],
    test_suite='test',
    requires=['wxpython', 'keyring'],
)

ICON_PATH = os.path.dirname(os.path.realpath(__file__))
ICON_PATH = os.path.join(ICON_PATH, 'icon.icns')

OPTIONS = dict(
    argv_emulation=True,
    site_packages=True,
    arch='x86_64',
    iconfile=ICON_PATH,
    plist = {
        'CFBundleName': NAME,
        'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION,
    }
)

py2app_kwargs = dict(
    app=['run.py'],
    data_files=[],
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

kwargs = {}
kwargs.update(base_kwargs)
kwargs.update(py2app_kwargs)

setup(**kwargs)
