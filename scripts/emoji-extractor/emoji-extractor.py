#!/usr/bin/env python3

import argparse
import binascii
import io
import shutil
from pathlib import Path
import xml.etree.ElementTree as ElementTree

from fontTools.ttLib import TTFont

parser = argparse.ArgumentParser(
    prog='emoji-extractor',
    description="""Extract emojis from NotoColorEmoji.ttf. Requires FontTools.""")
parser.add_argument(
    '-i', '--input',
    help='the TTF file to parse',
    default='NotoColorEmoji.ttf',
    required=False)
parser.add_argument(
    '-o', '--output',
    help='the png output folder',
    default='output/', required=False)
args = parser.parse_args()

path = Path(args.output)
shutil.rmtree(path, ignore_errors=True)
path.mkdir()

font_xml = io.StringIO()
TTFont(args.input).saveXML(font_xml)
ttx = ElementTree.fromstring(font_xml.getvalue())

for element in ttx.find('CBDT').find('strikedata'):
    data = element.find('rawimagedata').text.split()
    name = element.attrib['name'].lower()
    name = name.replace('uni', 'u')
    image_path = path / 'emoji_{}.png'.format(name)
    print('Extracting {}'.format(image_path.name))
    emoji = open(image_path, "wb")
    for char in data:
            hexChar = binascii.unhexlify(char)
            emoji.write(hexChar)
    emoji.close

for ligature_set_xml in ttx.find('GSUB')\
        .find('LookupList')\
        .find('Lookup')\
        .find('LigatureSubst'):
    ligature_set = ligature_set_xml.attrib['glyph'].lower().replace('uni', 'u')
    if ligature_set.startswith('u'):  # TODO: parse missing emojis
        for ligature_xml in ligature_set_xml:
            component = ligature_xml.attrib['components'].lower()\
                .replace(',', '_')\
                .replace('uni', 'u')
            glyph = ligature_xml.attrib['glyph']
            old_name = 'emoji_{}.png'.format(glyph)
            new_name = 'emoji_{}_{}.png'.format(ligature_set, component)
            print('Renaming {} to {}'.format(old_name, new_name))
            try:
                (path / old_name).rename(path / new_name)
            except:
                print('!! Cannot rename {}'.format(old_name))
    else:
        cmap = ttx.find('cmap').find('cmap_format_12')
        code = ''
        for map_element in cmap:
            if map_element.attrib['name'] == ligature_set:
                replace_s = '' if len(map_element.attrib['code']) > 4 else '00'
                code = map_element.attrib['code'].replace('0x', replace_s)
                old_name = 'emoji_{}.png'.format(ligature_set)
                try:
                    (path / old_name).rename(path / 'emoji_u{}.png'.format(code))
                except:
                    print('!! Cannot rename {}'.format(old_name))
        else:
            if code == '':
                print('Ignoring {}...'.format(ligature_set))

emojis = path.glob('*.png')
for emoji in emojis:
    if not emoji.name.startswith('emoji_u'):
        emoji = emoji.with_name(emoji.name.replace('emoji_', '').replace('.png', ''))
        print('Fixing {}...'.format(emoji.name))
        cmap = ttx.find('cmap').find('cmap_format_12')
        code = ''
        for map_element in cmap:
            if map_element.attrib['name'].lower() == emoji:
                replace_s = '' if len(map_element.attrib['code']) > 4 else '00'
                code = map_element.attrib['code'].replace('0x', replace_s)
                old_name = path / 'emoji_{}.png'.format(emoji)
                try:
                    (path / old_name).rename(path / 'emoji_u{}.png'.format(code))
                except:
                    print('!! Cannot fix _{}'.format(old_name))

# Some flags aren't correctly sorted
trans_table = {
    'fe4e5': '1f1ef_u1f1f5',
    'fe4e6': '1f1fa_u1f1f8',
    'fe4e7': '1f1eb_u1f1f7',
    'fe4e8': '1f1e9_u1f1ea',
    'fe4e9': '1f1ee_u1f1f9',
    'fe4ea': '1f1ec_u1f1e7',
    'fe4eb': '1f1ea_u1f1f8',
    'fe4ec': '1f1f7_u1f1fa',
    'fe4ed': '1f1e8_u1f1f3',
    'fe4ee': '1f1f0_u1f1f7',
}

for old, new in trans_table.items():
    (path / 'emoji_u{}.png'.format(old)).rename(path / 'emoji_u{}.png'.format(new))
