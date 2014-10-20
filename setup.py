import os
from setuptools import setup, find_packages

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='starmato-pdf',
    version='0.1',
    packages=find_packages(),
    install_requires=['reportlab==2.5',],
    package_data={
        'starmato.pdf': [
            'locale/fr_FR/LC_MESSAGES/*.*',
            'media/*.*',
        ],
    },
    license='MIT',
    description='A Django app to easily export data from Models to nice pdf documents.',
    long_description=README,
    url='http://www.go-tsunami.com/',
    author='GoTsunami',
    author_email='ab@go-tsunami.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django :: 1.6',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
