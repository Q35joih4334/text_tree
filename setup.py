from setuptools import setup

setup(
   name='text_tree',
   version='0.2.6',
   author='Q35joih4334',
   author_email='Q35joih4334@gmail.com',
   packages=['text_tree'],
   url='https://github.com/Q35joih4334/text_tree',
   license='LICENSE.txt',
   description='Draw text trees',
   long_description=open('README.md').read(),
   install_requires=['ete3', 'spacy', 'matplotlib'],
)