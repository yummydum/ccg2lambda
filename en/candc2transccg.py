#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  Copyright 2015 Pascual Martinez-Gomez
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import copy
from lxml import etree
import re
import os
import sys

def get_nodes_by_tag(root, tag):
    nodes = []
    if root.tag == tag:
        nodes.append(root)
    for node in root:
        nodes.extend(get_nodes_by_tag(node, tag))
    return nodes

def assign_ids_to_nodes(ccg_tree, sentence_number, current=0):
    ccg_tree.set('id', 's' + str(sentence_number) + '_sp' + str(current))
    current += 1
    for node in ccg_tree:
        current = assign_ids_to_nodes(node, sentence_number, current)
    return current

def rename_attributes(ccg_root, src_attribute, trg_attribute):
    if src_attribute in ccg_root.attrib:
        ccg_root.set(trg_attribute, ccg_root.get(src_attribute))
        del ccg_root.attrib[src_attribute]
    for child_node in ccg_root:
        rename_attributes(child_node, src_attribute, trg_attribute)

def assign_values_in_feat_structs(ccg_root):
    assert 'category' in ccg_root.attrib, 'Category field not present in node {0}'\
      .format(etree.tostring(ccg_root, pretty_print=True))
    category = ccg_root.get('category')
    category_assigned_value = re.sub(r'([,\]])', r'=true\1', category)
    ccg_root.set('category', category_assigned_value)
    for child_node in ccg_root:
        assign_values_in_feat_structs(child_node)

def assign_child_info(ccg_tree, sentence_number, tokens_node):
    """
    Inserts an attribute in every non-terminal node, indicating the ID
    of its child or children. In case of having children, their IDs
    are separated by a single whitespace.
    This function also introduces a pos="None" attribute for every
    non-terminal node.
    """
    if len(ccg_tree) == 0:
        token_position = ccg_tree.get('start')
        ccg_tree.set('terminal', 't' + str(sentence_number) + '_' + str(token_position))
    else:
        child_str = ' '.join([child_node.get('id') for child_node in ccg_tree])
        ccg_tree.set('child', child_str)
        ccg_tree.set('pos', "None")
    for child_node in ccg_tree:
        assign_child_info(child_node, sentence_number, tokens_node)

def flatten_and_rename_nodes(ccg_root):
    spans = []
    ccg_root.tag = 'span'
    spans.append(ccg_root)
    for child_node in ccg_root:
        spans.extend(flatten_and_rename_nodes(child_node))
    return spans

def candc_to_transccg(ccg_tree, sentence_number):
    """
    This function converts a sentence CCG tree generated by the C&C parser
    into a CCG tree using the format from transccg. For that purpose, we
    encapsulate into a <sentence> node two subtrees:
    <tokens> :
      1) An 'id' field is added, with the format s{sentence_number}_{token_number}.
      2) The C&C attribute 'word' of a leaf node is renamed into 'surf'.
      3) The C&C attribute 'lemma' of a leaf node is renamed into 'base'.
      4) The rest of the attributes of a leaf node remain unchanged.
    <ccg> :
      1) Copy tokens as <span> nodes with no tree structure, where:
         1.1) A 'terminal' attribute is added, pointing to the 'id' attribute of
              <tokens> subtree.
      2) Non-terminal nodes:
         2.1) The 'type' attribute is renamed as the 'rule' attribute, which
              contains the name of the rule (e.g. forward application, etc.).
         2.2) A 'child' attribute is added, that contains a space-separated list
              of <span> IDs.
      3) All nodes (including the recently created <span> terminals nodes):
         3.1) The attribute 'id' has the format s{sentence_number}_sp{span_number}.
              The order is depth-first.
         3.2) The attribute 'cat' is renamed as 'category'.
         3.3) Categories with feature structures of the form POS[feat] (note that
              there is no value associated to "feat") are converted to POS[feat=true].
    """
    # Obtain the <tokens> subtree and store it in variable tokens_node.
    tokens = get_nodes_by_tag(ccg_tree, 'lf')
    for i, token in enumerate(tokens):
        token.tag = 'token'
        token.set('id', 't' + str(sentence_number) + '_' + str(i))
        # Prefix every surface and base form with an underscore.
        # This is useful to avoid collisions of reserved words (e.g. "some", "all")
        # in nltk or coq. We also substitute dots '.' by 'DOT'.
        word = normalize_string(token.get('word'), 'surf')
        lemma = normalize_string(token.get('lemma'), 'base')
        token.set('surf', word)
        token.set('base', lemma)
        del token.attrib['word']
        del token.attrib['lemma']
    tokens_node = etree.Element('tokens')
    for token in tokens:
        tokens_node.append(copy.deepcopy(token))
    # Obtain the <ccg> subtree and store it in variable ccg_node.
    ccg_tree.set('root', 's' + str(sentence_number) + '_sp0')
    ccg_tree.set('id', 's' + str(sentence_number) + '_ccg0')
    # Assign an ID to every node, in depth order.
    ccg_root = ccg_tree[0]
    assign_ids_to_nodes(ccg_root, sentence_number)
    assign_child_info(ccg_root, sentence_number, tokens_node)
    # Rename attributes.
    rename_attributes(ccg_root, 'cat', 'category')
    rename_attributes(ccg_root, 'type', 'rule')
    # Assign values to feature structures. E.g. S[adj] --> S[adj=true]
    assign_values_in_feat_structs(ccg_root)
    # Flatten structure.
    spans = flatten_and_rename_nodes(ccg_root)
    for child_span in spans:
        ccg_tree.append(child_span)
        if child_span.get('id').endswith('sp0'):
            child_span.set('root', 'true')
    sentence_node = etree.Element('sentence')
    sentence_node.append(tokens_node)
    sentence_node.append(ccg_tree)
    return sentence_node

def normalize_string(raw_string, attribute):
    normalized = raw_string
    if attribute == 'base':
        normalized = normalized.lower()
    return normalized

def make_transccg_xml_tree(transccg_trees):
    """
    Create the structure:
    <root>
      <document>
        <sentences>
          <sentence id="s1">
          ...
          </sentence>
        </sentences>
      </document>
    </root>
    """
    sentences_node = etree.Element('sentences')
    for transccg_tree in transccg_trees:
        sentences_node.append(transccg_tree)
    document_node = etree.Element('document')
    document_node.append(sentences_node)
    root_node = etree.Element('root')
    root_node.append(document_node)
    return root_node

def main(args=None):
    import textwrap
    usage = textwrap.dedent("""\
        Usage:
            python candc2transccg.py <candc_trees.xml>

            candc_trees.xml should contain sentences parsed by C&C parser.
            This program will print in standard output the trees in transccg format.
      """)
    if args is None:
        args = sys.argv[1:]
    if len(args) != 1:
        print('Wrong number of arguments.')
        print(usage)
        sys.exit(1)
    if not os.path.exists(args[0]):
        print('File does not exist: {0}'.format(args[0]))
        sys.exit(1)
    candc_trees_filename = args[0]

    parser = etree.XMLParser(remove_blank_text=True)
    xml_tree = etree.parse(candc_trees_filename, parser)
    root = xml_tree.getroot()
    ccg_trees = root.findall('ccg')

    transccg_trees = []
    for i, ccg_tree in enumerate(ccg_trees):
        transccg_tree = candc_to_transccg(ccg_tree, i)
        transccg_trees.append(transccg_tree)

    transccg_xml_tree = make_transccg_xml_tree(transccg_trees)
    # transccg_xml_tree.write(pretty_print=True, encoding='utf-8')
    encoding = xml_tree.docinfo.encoding
    result = etree.tostring(transccg_xml_tree, xml_declaration=True,
                            encoding=encoding, pretty_print=True)
    print(result.decode('utf-8'))

if __name__ == '__main__':
    main()
