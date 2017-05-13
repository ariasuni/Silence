#!/usr/bin/env python3

import argparse
from pathlib import Path
import xml.etree.ElementTree as ElementTree

from PIL import Image

parser = argparse.ArgumentParser(
    prog='gen-sprite',
    description="""Generate sprites from extracted emojis.""")
parser.add_argument(
    '-e', '--emojis',
    help='folder where emojis are stored',
    default='output/',
    required=False)
parser.add_argument(
    '-i', '--xml',
    help='XML containing emojis map',
    default='emoji-categories.xml',
    required=False)
parser.add_argument(
    '-s', '--size',
    help='Maximum number of emojis per line',
    default='15',
    required=False)
parser.add_argument(
    '-r', '--resize',
    help='Maximum width for sprites',
    default='1530',
    required=False)
args = parser.parse_args()

emoji_path = Path(args.emojis)

xml = ElementTree.parse(args.xml).getroot()
parsedItems = []

for group in xml:
    groupName = group.attrib['name']
    emojis = []
    output = open('{}.txt'.format(groupName), 'w')
    for item in group:
        emoji = item.text.replace(',', '_u').lower()
        emoji_file = emoji_path / 'emoji_u{}.png'.format(emoji)
        if '|' not in emoji and emoji not in parsedItems and emoji_file.is_file():
            parsedItems.append(emoji)
            emojis.append(emoji_file)
            emojiCodePoint = '\\U' + emoji.replace('_u', '\\U')
            emojiCodePoint = emojiCodePoint.split('\\U')
            finalCodePoints = []
            for point in emojiCodePoint:
                point = point.replace('\\U', '')
                if len(point) > 0:
                    if len(point) < 8:
                        point = "0" * (8 - len(point)) + point
                    finalCodePoints.append(point)
            char = '\\U' + '\\U'.join(finalCodePoints)
            output.write(char + '\n')
    images = [Image.open(filename) for filename in emojis]
    output.close()

    if len(images) > 0:
        print("Generating sprite for {}".format(groupName))
        masterWidth = (128 * int(args.size))
        lines = len(images) / float(args.size)
        if not lines.is_integer():
            lines = int(lines + 1)
        masterHeight = int(128 * lines)
        master = Image.new(
            mode='RGBA',
            size=(masterWidth, masterHeight),
            color=(0, 0, 0, 0)
        )

        offset = -1
        for count, image in enumerate(images):
            location = (128 * count) % masterWidth
            if location == 0:
                offset += 1
            master.paste(image, (location, 128 * offset))
        ratio = masterWidth / float(args.resize)
        newHeight = int(masterHeight // ratio)
        master = master.resize((int(args.resize), newHeight))
        master.save(groupName + '.png', 'PNG')
    else:
        print('Ignoring {}...'.format(groupName))
