#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import os

license = ""

if os.path.isfile("LICENSE"):
    with open('LICENSE') as f:
        license = f.read()

readme = ""

if os.path.isfile("README.md"):
    with open("README.md") as f:
        readme = f.read()


setup(
    zip_safe=False,
    name='django-debug-toolbar-openstack-panel',
    version='0.0.1',
    packages=['openstack_panel', 'openstack_panel.panels'],
    package_data={'openstack_panel': ['templates/*', 'static/*', ]},
    url='https://github.com/andriyko/django-debug-toolbar-openstack-panel',
    license=license,
    author='Andriy Hrytskiv',
    author_email='ahrytskiv@gmail.com',
    description='A django-debug-toolbar panel for OpenStack Dashboard',
    install_requires=['Django', 'django-debug-toolbar>=1.0.1',
                      'requests==2.3.0', 'six==1.7.2'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Debuggers'],

    long_description=readme,
)
