# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 00:32:05 2021

@author: Q35joih4334
"""


import textacy.datasets
import itertools

from text_tree import text_tree

# Examples
texts = ['Sentence one starts with the same word as sentence two. Sentence two continues a bit differently. Sentence two is also shorter. Last sentence does not meet criteria for root word.']
t, s = text_tree.draw_tree(texts,
                           [{'LOWER': 'sentence'}],
                           'simple_example.png')

texts = ['Tree can also be reversed. The root word will be positioned on the right when tree is reversed. Currently, punctuation in the end of the sentences is disregarded when tree orientation is reversed.']
t, s = text_tree.draw_tree(texts,
                           [{'LOWER': 'reversed'}],
                           'simple_example_reversed.png',
                           reverse=True)

texts = ['Tree can also be reversed. Tree root word will be positioned on the right when tree is reversed. Currently, punctuation in the end of the sentences is disregarded when tree orientation is reversed.',
         'Tree nodes can be highlighted. Tree nodes can have annotations indicating their source/reference.']
t, s = text_tree.draw_tree(texts,
                           [{'LOWER': 'tree'}],
                           'simple_example_highlights_refs.png',
                           highlights=['tree', 'can', 'revers'],
                           doc_refs=['first document', 'second document'])

# Build textacy dataset
# NOTE: it would be preferable if the datset was static for testing
ds = textacy.datasets.IMDB()
ds.download()
texts = []
refs = []
for i, record in enumerate(ds.records(limit=65)):
    texts.append(record.text)
    refs.append('{} {}'.format(record.meta['movie_id'], i))
    

# Run tests
# ---------

params = {
    'rootword_pattern': [
        [{'LOWER': 'the'}],
        [{'LOWER': 'film'}]
    ],
    'reverse': [
        True,
        False
    ],
    'highlights': [
        None,
        ['good', 'film', 'movie']
    ],
    'doc_refs': [
        None,
        refs
    ],
    }

keys, values = zip(*params.items())
params_permutations = [dict(zip(keys, v)) for v in itertools.product(*values)]

for i, params_permutation in enumerate(params_permutations):
    
    print(i, params_permutation)    
    
    t, s = text_tree.draw_tree(texts,
        output_file='TEST - draw_tree {}.pdf'.format(i),
        **params_permutation)