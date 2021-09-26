from setuptools import setup

setup(
   name='text_tree',
   version='0.1.1',
   author='Q35joih4334',
   author_email='',
   packages=['text_tree'],
   url='https://github.com/Q35joih4334/text_tree',
   license='LICENSE.txt',
   description='Draw text trees',
   long_description=open('README.txt').read(),
   install_requires=['ete3', 'spacy', 'matplotlib'],
)