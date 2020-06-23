import xml.etree.ElementTree as ET
from cairosvg import svg2png
from os import listdir
from os.path import isfile, join
from PIL import Image
import os
from matplotlib import image
from matplotlib import pyplot as plt
import numpy as np
import math


# remove labels (black baselines)
def remove_baselines(file):
    tree = ET.parse(file)
    root = tree.getroot()
    paths = root.findall('{http://www.w3.org/2000/svg}path')
    for i in paths:
        root.remove(i)
    return tree


# extract labels(baselines) and change color to white and background to black
def extract_baselines(file):
    tree = ET.parse(file)
    root = tree.getroot()
    black_background = ET.fromstring('<rect width="100%" height="100%" fill="black"/>')
    black_background.tag = '{http://www.w3.org/2000/svg}rect'
    root.insert(1, black_background)
    if root.find('{http://www.w3.org/2000/svg}g'):
        el = root.find('{http://www.w3.org/2000/svg}g')
        el.remove(el.find('{http://www.w3.org/2000/svg}image'))
        paths = el.findall('{http://www.w3.org/2000/svg}path')
    else:
        root.remove(root.find('{http://www.w3.org/2000/svg}image'))
        paths = root.findall('{http://www.w3.org/2000/svg}path')

    for i in paths:
        i.attrib["style"] = i.attrib["style"].replace("stroke:#000000", "stroke:#ffffff")
    return tree


def convert_to_greyscale(img):
    Image.open(img).convert('L').save(img)


def convert_to_binary(img):
    Image.open(img).convert('L').point(lambda p: 255 if p > 0 else p).save(img)


def convert_to_binary_thres(img, thres):
    Image.open(img).convert('L').point(lambda p: 0 if p < 255/thres else p).save(img)


# delete (old) files before creating new ones
def delete_old_files():
    p1 = 'data_labelled_svg'
    p2 = 'data_labelled_jpg'
    svgs = [f"{p1}/{f}" for f in listdir(p1) if isfile(join(p1, f))]
    jpgs = [f"{p2}/{f}" for f in listdir(p2) if isfile(join(p2, f))]
    for f in svgs + jpgs:
        os.remove(f)


def create_data():
    mypath = 'data_labelled'
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    counter = 0
    total = len(files)
    for file in files:
        file_ = file.replace(".svg", "")

        counter = counter + 1
        print(f'{file:40}{counter:4} of{total:4}')
        tree_original = remove_baselines(f'{mypath}/{file}')
        tree_original.write(f'data_labelled_svg/{file}')
        svg2png(bytestring=open(f'data_labelled_svg/{file}', 'rb').read(),
                write_to=open(f'data_labelled_jpg/{file_}.jpg', 'wb'))
        convert_to_greyscale(f'data_labelled_jpg/{file_}.jpg')

        tree_labels = extract_baselines(f'{mypath}/{file}')
        tree_labels.write(f'./data_labelled_svg/{file_}_GT0.svg')
        svg2png(bytestring=open(f'./data_labelled_svg/{file_}_GT0.svg', 'rb').read(),
                write_to=open(f'data_labelled_jpg/{file_}_GT0.jpg', 'wb'))
        convert_to_binary(f'data_labelled_jpg/{file_}_GT0.jpg')


def create_txts_with_paths(split):
    data = [os.path.abspath('data_labelled_jpg/'+f) for f in listdir(
        'data_labelled_jpg') if f.find("_GT") == -1]
    split = int(math.ceil(split * len(data)))
    train = data[:split]
    val = data[split:]
    train = "\n".join(train)

    with open("train.lst", "w") as f:
        f.write(train)

    val = "\n".join(val)
    with open("val.lst", "w") as f:
        f.write(val)


#https://arxiv.org/pdf/1802.03345.pdf page 25
#https://en.wikipedia.org/wiki/Dilation_(morphology)
"""
def create_seperator_class(file):
    tree = ET.parse(file)
    root = tree.getroot()
    if root.find('{http://www.w3.org/2000/svg}g'):
        el = root.find('{http://www.w3.org/2000/svg}g')
        el.remove(el.find('{http://www.w3.org/2000/svg}image'))
        paths = el.findall('{http://www.w3.org/2000/svg}path')
    else:
        root.remove(root.find('{http://www.w3.org/2000/svg}image'))
        paths = root.findall('{http://www.w3.org/2000/svg}path')

    lines = np.empty((2, 2), float)
    for i in paths:
        bline_raw = i.attrib['d']
        bline_parsed = bline_raw.split(' ')[1:]
        if len(bline_parsed) == 2:
          line = np.asarray([[float(i.split(',')[0]), float(i.split(',')[1])] for i in bline_parsed])
          print(line.shape)
          lines = np.concatenate((lines, line))
        elif len(bline_parsed) >= 2 and bline_parsed[1] == 'c':
            start = np.array([float(bline_parsed[0].split(',')[0]), float(bline_parsed[0].split(',')[1])])
            first = start + np.array([float(bline_parsed[2].split(',')[0]), float(bline_parsed[2].split(',')[1])])
    print(lines)

    return tree
"""



if __name__ == "__main__":
    #create_seperator_class('/home/yunusc/PycharmProjects/svg-preproccesing/data_labelled/e2.svg')
    delete_old_files()
    create_data()
    create_txts_with_paths(0.7)




