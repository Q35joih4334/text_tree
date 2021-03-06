# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 01:00:56 2021

@author: Q35joih4334
"""

import re
import itertools
import spacy
import spacy.lang.en
import matplotlib
import ete3

def _perceived_luminance(r, g, b):
    return .299*r + .587*g + .114*b

class codifier:

    """
    Codifies input text to numbers
    """

    def __init__(self):
        self.codemapper = {}

    def codify(self, text):
        if text not in self.codemapper:
            self.codemapper[text] = len(self.codemapper) + 1
        return self.codemapper[text]

def segment_matching_sents(doc_texts,
                           rootword_pattern,
                           reverse=False,
                           nlp=None,
                           sent_splitting='rule'):

    """
    Matches sentences in text that start or end with rootword pattern. Findgs
    sentences starting with rootword pattern or sentences ending with rootword
    pattern. Segments list of text sentences into list of lists.

    Input:

        doc_texts: text as a list of strings

        rootword_pattern: pattern to be input to spacy.matcher

        reverse (default: False): reverse root matching

        nlp (optional): spacy nlp object (default: loads spacy en_core_web_sm)

        sent_splitting (dep, stat, rule [DEFAULT]): sentence splitting strategy

    Output:

        list of lists containing sentence tokens as strings
    """

    if not isinstance(doc_texts, list):
        raise TypeError('doc_texts argument must be list')

    if not nlp:

        # Dependency parse splitting
        if sent_splitting == 'dep':
            nlp = spacy.load('en_core_web_sm',
                             disable=['ner', 'tagger', 'textcat', 'lemmatizer'])

        # Statistical sentence segmenter
        elif sent_splitting == 'stat':
            nlp = spacy.load('en_core_web_sm', exclude=["parser"],
                             disable=['ner', 'tagger', 'textcat', 'lemmatizer'])
            nlp.enable_pipe('senter')

        # Rule-based pipeline component
        elif sent_splitting == 'rule':
            nlp = spacy.lang.en.English()
            nlp.add_pipe('sentencizer')

    Codifier = codifier()

    matcher = spacy.matcher.Matcher(nlp.vocab)
    matcher.add('rootword', [rootword_pattern])

    doc_sents = []

    for doc_text_i, text in enumerate(doc_texts):

        sent_tokens = []

        # NOTE: this might be unsafe if text length is really long
        # TODO: maybe there could be a safer way to do this?
        nlp.max_length = len(text)

        doc = nlp(text)

        matches = matcher(doc)

        if matches:

            for match_id, start, end in matches:

                span = doc[start:end] #TODO: rename this to root_span
                sent = span.sent

                # All tokens after root word
                after_tokens = span.doc[span[-1].i + 1:span.sent[-1].i + 1]

                tokens = []

                # Rootword match in sentence start
                if span[0].i == span.sent[0].i and not reverse:

                    for token in sent:

                        tokens.append({
                            '_id': Codifier.codify(token.text.lower()),
                            '_token_text': token.text,
                            '_whitespace': token.whitespace_,
                            '_token_is_punct': token.is_punct})

                    sent_tokens.append(tokens)

                # Rootword match in sentence end
                # If all tokens after root word are non-words (apart from puncts)
                # TODO: or whitespace?
                # TODO: will this skip the sentence if after_tokens is empty?
                elif all([x.is_punct for x in after_tokens]) and reverse:

                    for token in reversed(sent):

                        trailing_punct = token.i in [x.i for x in after_tokens]

                        if not trailing_punct:

                            tokens.append({
                                '_id': Codifier.codify(token.text.lower()),
                                '_token_text': token.text,
                                '_whitespace': token.whitespace_,
                                '_token_is_punct': token.is_punct})

                    sent_tokens.append(tokens)

        # NOTE: All docs are included, regardless of whether matching
        # sentences are found or not. The reason for this is ensuring that
        # doc_sents, doc_refs and doc_attrs are always of equal length.
        # TODO: this is a bit ugly solution, maybe doc_sents, doc_refs and
        # doc_attrs should be concatenated into list of dicts first?
        # Current solution also leaves empty lists in doc_sents
        doc_sents.append(sent_tokens)

    return doc_sents


# TODO: add a test that the created tree is actually a tree!
#       ete3 gets stuck if trying to enter a non-tree?
#       ete3 doesn't have a test for tree?
def tree_from_list(doc_sents,
                   doc_refs=None,
                   doc_attrs=None):

    """
    Returns ete3 Tree from a list of lists containing sentences.
    Whitespace is expected to be a separate item in list.

    Each token and whitespace represents one node. Tree structure is based on
    lowercase tokens (_node_name). Original text is retained as node attribute
    in each node (_label). A simple version of node name with special
    characters removed is created (_simple_label), which can be useful for
    sorting the tree.

    Input:

        doc_sents (list of lists): sentences (required)

        doc_refs (list of strings): reference for each sentence (optional)

        doc_attrs (list of dicts): node attributes to be added to ete3 Tree nodes

    Output:

        ete3 Tree
    """

    if not doc_refs:
        doc_refs = [None for x in range(len(doc_sents))]

    if not doc_attrs:
        doc_attrs = [{} for x in range(len(doc_sents))]

    parent_child_table = []
    node_features = {}

    for doc_sent, doc_ref, doc_attr in zip(doc_sents, doc_refs, doc_attrs):

        for sent_tokens_i, sent_tokens in enumerate(doc_sent):

            # Create (cumulative) sentence structure
            # Also create node attribute data
            sent_node_names = []
            for sent_token_i, sent_token in enumerate(sent_tokens):

                cumulative_tokens = sent_tokens[0:sent_token_i + 1]

                node_name = '_'.join([str(x['_id']) for x in cumulative_tokens])

                simple_label = ''.join([x['_token_text'].lower() for x in cumulative_tokens])
                simple_label = ''.join(filter(str.isalnum, simple_label))

                attrs = doc_attr.copy() #collect optional attributes
                attrs.update(sent_token) #add _token_text and _whitespace
                attrs.update({
                    '_node_name': node_name,
                    '_simple_label': simple_label,
                    '_ref': doc_ref})

                sent_node_names.append(node_name)
                node_features[node_name] = attrs

            # Create parent_child_table for ete3 Tree
            for i in range(len(sent_node_names) - 1):

                parent = sent_node_names[i]
                child = sent_node_names[i + 1]

                if parent != child:
                    parent_child_table.append((parent, child, 0))

    # Create ete3 Tree and add node attributes
    tree = ete3.Tree.from_parent_child_table(set(parent_child_table))

    for node in tree.traverse():
        node.add_features(**node_features[node.name])

    # Clean up nodes
    for node in tree.traverse():

        # Remove punct nodes
        # TODO: maybe this should be optional
        #if len(node.get_children()) > 1: #junction
        if len(node.get_leaves()) > 1:
            if node._token_is_punct or node._token_text.strip() == '':
                node.delete()

    return tree

# TODO: this could be cleaned up
# TODO: consider moving layout outside from here
def default_treestyle(tree,
                      reverse=False,
                      highlights=None,
                      cmap=matplotlib.cm.get_cmap('tab20'),
                      sort_by_name=True,
                      sort_by_topology=True):

    if not highlights:
        highlights = []

    cmap_colors = itertools.cycle([cmap(x) for x in range(cmap.N)])
    highlight_colors = {x.lower():next(cmap_colors) for x in highlights}

    # Hide nodes from tree visualization
    for node in tree.traverse():
        node.img_style['fgcolor'] = '#FFFFFFFF'
        node.img_style['bgcolor'] = '#FFFFFFFF'
        node.img_style["hz_line_color"] = '#FFFFFFFF'
        node.img_style['size'] = 0

    # TODO: these params should be accessible from default_treestyle
    def text_tree_default_layout(node,
                                 node_margin=.5,
                                 space_margin_mult=.4,
                                 branch_margin=10,
                                 fontsize_min=8,
                                 fontsize_max=96):

        name_face = ete3.TextFace(node._token_text)

        # Handle font size change depending on leave count under the node
        # Limit fontsize
        leaf_count = len(node.get_leaves())
        font_size = sorted([fontsize_min, leaf_count * fontsize_min, fontsize_max])[1]
        name_face.fsize = font_size

        # Node margin is added to avoid nodes overlapping
        name_face.margin_left = node_margin
        name_face.margin_right = node_margin

        # Add extra margin if node has whitespace
        if reverse and node._whitespace == ' ':
            name_face.margin_left = space_margin_mult * font_size

        elif not reverse and node._whitespace == ' ':
            name_face.margin_right = space_margin_mult * font_size

        # Add Additional margin in case node is at tree branch
        if len(node.get_sisters()) > 0:
            name_face.margin_left = branch_margin

        if len(node.get_children()) > 1: #junction
            name_face.margin_right = branch_margin

        # Handle highlighting
        bgcolor = (1, 1, 1, 1)
        for pattern, color in highlight_colors.items():
            if re.search(pattern, node._token_text, re.IGNORECASE):
                bgcolor = color
                break

        # Switch text color between white and black depending on background color
        if _perceived_luminance(*bgcolor[:3]) > .5:
            text_color = (0, 0, 0)
        else:
            text_color = (1, 1, 1)
        name_face.inner_background.color = matplotlib.colors.to_hex(bgcolor[:3])
        name_face.fgcolor = matplotlib.colors.to_hex(text_color)

        # Add node text
        ete3.faces.add_face_to_node(name_face, node, column=0)

        # Add reference
        if node.is_leaf():
            if node._ref:
                ref_face = ete3.TextFace(node._ref, fsize=6)
                ref_face.margin_right = 10
                ref_face.margin_left = 10
                ete3.faces.add_face_to_node(ref_face, node, column=1, aligned=False)

    ts = ete3.TreeStyle()

    ts.show_leaf_name = False
    ts.layout_fn = text_tree_default_layout
    ts.root_opening_factor = 1
    ts.scale = 20
    ts.show_scale = False

    ts.margin_top = 20
    ts.margin_bottom = 20
    ts.margin_right = 20

    # ts.draw_guiding_lines = True
    # ts.guiding_lines_color = "#cccccc"

    if reverse:
        ts.orientation = 1
    else:
        ts.orientation = 0

    # Sort
    # TODO: check if _simple_label exists in all nodes
    # NOTE: such check is actually not necessary if tree_from_list has been used
    if sort_by_name:
        tree.sort_descendants('_simple_label')

    if sort_by_topology:
        tree.ladderize()

    return tree, ts

def draw_tree(doc_texts,
              rootword_pattern,
              output_file,
              reverse=False,
              doc_refs=None,
              doc_attrs=None,
              highlights=None,
              nlp=None,
              sent_splitting='rule'):

    """
    Build text tree and save it as a file.

    This is a convenience function that runs all other function in a simple
    manner.

    Input:

        texts: lists of texts (strings) to be presented as a tree

        rootword_pattern: pattern to be input to spacy.matcher

        output_file: path for the tree to be drawn

        reverse (default: False): reverse segmentation (for sentences ending
        with word of interest)

        doc_refs (optional): list of strings containing references to be displayed next to sentence

        highlights (optional): list of regexp patterns to use for highlighting nodes

    Output:

        tree as ete3 object

        segmented texts

    """

    if not doc_refs:
        doc_refs = [None for x in range(len(doc_texts))]

    if not doc_attrs:
        doc_attrs = [{} for x in range(len(doc_texts))]

    # Extract matching sentences
    print('Extracting matching sentences.', end=' ')
    doc_sents = segment_matching_sents(doc_texts,
                                       rootword_pattern,
                                       reverse=reverse,
                                       nlp=nlp,
                                       sent_splitting=sent_splitting)

    # Check for how many sentences were found
    total_matching_sentences = sum([len(x) for x in doc_sents])
    print('Found {} sentences.'.format(total_matching_sentences))

    if total_matching_sentences == 0:
        print('No matching sentences found, skipping.')
        return None, None

    # Make tree
    print('Building tree.')
    tree = tree_from_list(doc_sents, doc_refs=doc_refs, doc_attrs=doc_attrs)

    # Apply style
    print('Applying style.')
    tree, ts = default_treestyle(tree, reverse=reverse, highlights=highlights)

    # Render to file
    print('Rendering tree to {}'.format(output_file))
    tree.render(output_file, tree_style=ts)

    return tree, doc_sents
