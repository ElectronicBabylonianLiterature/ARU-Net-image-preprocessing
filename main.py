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


def sort_img_sizes():
    mypath = 'data_labelled'
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    sizes = dict()
    for file in files:
        tree = ET.parse(f'{mypath}/{file}')
        root = tree.getroot()
        height = int(root.attrib['height'])
        width = int(root.attrib['width'])
        sizes[file] = {"h": height, "w": width, "s": height * width}
    return {k: v for k, v in sorted(sizes.items(), key=lambda item: -item[1]['s'])}


def pretty_print_dict(sizes):
    for i, j in list(sizes.items()):
        print(f'{i:40}{str(j):4}')
    print("#################################\n")


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


def calc_scale(total_size, max_size):
    if total_size <= max_size:
        return 1
    else:
        return round(max_size/total_size, 2)


def create_data(sorted_imgs, max_size, to_scale):
    mypath = 'data_labelled'
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    scaling_counter = 0
    counter = 0
    total = len(files)
    for file in files:
        path = f'{mypath}/{file}'

        if to_scale:
            scale = calc_scale(sorted_imgs[file]["s"], max_size)
            if scale < 1:
                scaling_counter = scaling_counter + 1
        else:
            scale = 1

        file_ = file.replace(".svg", "")

        counter = counter + 1
        print(f'{file:40}{counter:4} of{total:4}   scaling-factor: {scale}')
        tree_original = remove_baselines(path)
        tree_original.write(f'data_labelled_svg/{file}')
        svg2png(bytestring=open(f'data_labelled_svg/{file}', 'rb').read(), scale=scale,
                write_to=open(f'data_labelled_jpg/{file_}.jpg', 'wb'))
        convert_to_greyscale(f'data_labelled_jpg/{file_}.jpg')

        tree_labels = extract_baselines(path)
        tree_labels.write(f'./data_labelled_svg/{file_}_GT0.svg')
        svg2png(bytestring=open(f'./data_labelled_svg/{file_}_GT0.svg', 'rb').read(), scale=scale,
                write_to=open(f'data_labelled_jpg/{file_}_GT0.jpg', 'wb'))
        convert_to_binary(f'data_labelled_jpg/{file_}_GT0.jpg')

    print(f"\n------total pictures scaled: {scaling_counter}")


def create_txts_with_paths(split, sorted_dict):

    data = [os.path.abspath('data_labelled_jpg/'+f) for f in listdir(
        'data_labelled_jpg') if f.find("_GT") == -1]


    #data = [os.path.abspath('data_labelled_jpg/'+f.replace('svg', 'jpg')) for f in sorted_dict]
    split = int(math.ceil(split * len(data)))
    train = data[:split]
    val = data[split:]
    train = "\n".join(train)

    with open("train.lst", "w") as f:
        f.write(train)

    val = "\n".join(val)
    with open("val.lst", "w") as f:
        f.write(val)


if __name__ == "__main__":
    MAX_SIZE = 11000000 # estimated by trial and error
    sorted_imgs = sort_img_sizes()
    pretty_print_dict(sorted_imgs)
    delete_old_files()
    create_data(sorted_imgs, MAX_SIZE, True)
    create_txts_with_paths(0.9, sorted_imgs)




