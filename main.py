import copy
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


from svg.path import parse_path

# remove labels (black baselines)
def remove_baselines(file):
    tree = ET.parse(file)
    root = tree.getroot()
    paths = root.findall('{http://www.w3.org/2000/svg}path')
    for i in paths:
        root.remove(i)

    if root.find('{http://www.w3.org/2000/svg}g'):
        el = root.find('{http://www.w3.org/2000/svg}g')
        paths = el.findall('{http://www.w3.org/2000/svg}path')
        for i in paths:
            el.remove(i)
        return tree
    else:
        return tree


def sort_img_sizes():
    mypath = 'data_labelled'
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    sizes = dict()
    for file in files:
        tree = ET.parse(f'{mypath}/{file}')
        root = tree.getroot()
        height = float(root.attrib['height'])
        width = float(root.attrib['width'])
        sizes[file] = {"h": height, "w": width, "s": height * width}
    return {k: v for k, v in sorted(sizes.items(), key=lambda item: -item[1]['s'])}


def pretty_print_dict(sizes):
    for i, j in list(sizes.items()):
        print(f'{i:40}{str(j):4}')
    print("#################################\n")


# extract labels(baselines) and change color to white and background to black
def extract_baselines_1(file):
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

def extract_baselines_3(tree):
    root = tree.getroot()
    black_background = ET.fromstring('<rect width="100%" height="100%" fill="black"/>')
    black_background.tag = '{http://www.w3.org/2000/svg}rect'
    root.remove(root.find(black_background.tag))
    black_background = ET.fromstring('<rect width="100%" height="100%" fill="white"/>')
    black_background.tag = '{http://www.w3.org/2000/svg}rect'
    root.insert(1, black_background)
    if root.find('{http://www.w3.org/2000/svg}g'):
        el = root.find('{http://www.w3.org/2000/svg}g')
        paths = el.findall('{http://www.w3.org/2000/svg}path')
    else:
        root.remove(root.find('{http://www.w3.org/2000/svg}image'))
        paths = root.findall('{http://www.w3.org/2000/svg}path')

    for i in paths:
        i.attrib["style"] = i.attrib["style"].replace("stroke:#ff0000",
                                                      "stroke:#000000")
        i.attrib["style"] = i.attrib["style"].replace("stroke:#ffffff",
                                                      "stroke:#000000")
    return tree

def extract_baselines_hori(tree):
    root = tree.getroot()
    black_background = ET.fromstring('<rect width="100%" height="100%" fill="black"/>')
    black_background.tag = '{http://www.w3.org/2000/svg}rect'
    root.insert(1, black_background)
    if root.find('{http://www.w3.org/2000/svg}g'):
        el = root.find('{http://www.w3.org/2000/svg}g')
        paths = el.findall('{http://www.w3.org/2000/svg}path')
    else:
        root.remove(root.find('{http://www.w3.org/2000/svg}image'))
        paths = root.findall('{http://www.w3.org/2000/svg}path')

    for i in paths:
        if "#ffffff" in i.attrib["style"]:
            if el:
                el.remove(i)
            else:
                root.remove(i)
        i.attrib["style"] = i.attrib["style"].replace("stroke:#ff0000", "stroke:#ffffff")
    return tree


def convert_to_greyscale(img):
    Image.open(img).convert('L').save(img)


def convert_to_binary(img):
    Image.open(img).convert('L').point(lambda p: 150 if p <= 4 else p).save(img)


def convert_to_binary_thres(img, thres):
    Image.open(img).convert('L').point(lambda p: 0 if p < 255/thres else p).save(img)


# delete (old) files before creating new ones
def delete_old_files():
    p1 = 'data_labelled_svg'
    p2 = 'data_labelled_jpg'
    svgs = [f"{p1}/{f}" for f in listdir(p1) if isfile(join(p1, f))]
    pngs = [f"{p2}/{f}" for f in listdir(p2) if isfile(join(p2, f))]
    for f in svgs + pngs:
        os.remove(f)


def calc_scale(max_size):
    if max_size <= 2000:
        return 0.5
    elif 2000 <= max_size <= 4800:
        return 0.33
    else:
        return 0.2


def create_data(sorted_imgs, max_size, to_scale):
    mypath = 'data_labelled'
    files = [f for f in listdir(mypath) if isfile(join(mypath, f))]

    scaling_counter = 0
    counter = 0
    total = len(files)
    for file in files:
        path = f'{mypath}/{file}'

        if to_scale:
            scale = calc_scale(max(sorted_imgs[file]["h"],sorted_imgs[file]["w"]))
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
                write_to=open(f'data_labelled_jpg/{file_}.png', 'wb'))
        #convert_to_binary(f'data_labelled_jpg/{file_}.png')

        convert_to_greyscale(f'data_labelled_jpg/{file_}.png')

        tree_labels = extract_baselines_1(path)
        tree_labels.write(f'./data_labelled_svg/{file_}_GT0.svg')
        svg2png(bytestring=open(f'./data_labelled_svg/{file_}_GT0.svg', 'rb').read(),
                scale=scale,
                write_to=open(f'data_labelled_jpg/{file_}_GT0.png', 'wb'))



        tree_labels_1 = create_seperator_class(tree_labels)

        tree_labels_2 = copy.deepcopy(tree_labels_1)

        

        tree_labels = extract_baselines_hori(tree_labels_1)
        tree_labels.write(f'./data_labelled_svg/{file_}_GT1.svg')
        svg2png(bytestring=open(f'./data_labelled_svg/{file_}_GT1.svg', 'rb').read(),
                scale=scale,
                write_to=open(f'data_labelled_jpg/{file_}_GT1.png', 'wb'))

        tree_labels_2 = extract_baselines_3(tree_labels_2)
        tree_labels_2.write(f'./data_labelled_svg/{file_}_GT2.svg')
        svg2png(bytestring=open(f'./data_labelled_svg/{file_}_GT2.svg', 'rb').read(),
                scale=scale,
                write_to=open(f'data_labelled_jpg/{file_}_GT2.png', 'wb'))



    print(f"\n------total pictures scaled: {scaling_counter}")


def create_txts_with_paths(split, sorted_dict):

    #data = [os.path.abspath('data_labelled_png/'+f) for f in listdir('data_labelled_png') if f.find("_GT") == -1]


    data = [os.path.abspath('data_labelled_jpg/'+f.replace('svg', 'png')) for f in sorted_dict]
    split = int(math.ceil(split * len(data)))
    train = data[:split]
    val = data[split:]
    train = "\n".join(train)

    with open("train.lst", "w") as f:
        f.write(train)

    val = "\n".join(val)
    with open("val.lst", "w") as f:
        f.write(val)


def split_c(str):
    return float(str.split(',')[0]), float(str.split(',')[1])


def calc_orth(start, end):
    vec = tuple(np.subtract(end, start))
    orth_vec_1 = np.array([round(-vec[1], 2), round(vec[0], 2)])

    #orth_vec_2 = (vec[1], -vec[0])

    length = np.linalg.norm(orth_vec_1)
    np.seterr(divide='ignore', invalid='ignore')
    orth_vec_1_scaled = (orth_vec_1/length)*30
    orth_vec_1_scaled = (orth_vec_1_scaled[0], orth_vec_1_scaled[1])
    orth_vec_2_scaled = (-orth_vec_1_scaled[0], -orth_vec_1_scaled[1])
    return [[start, orth_vec_1_scaled], [start, orth_vec_2_scaled]]

def calc_sep(lines, curves):
    vecs = []
    if lines:
        for x in lines:
            start = x[0]
            end = x[1]
            vec1 = calc_orth(start, end)
            vec2 = calc_orth(end ,start)
            vecs.extend(vec1)
            vecs.extend(vec2)
    if curves:
        for z in curves:
            start = z[0]
            end = z[1]
            vec3 = calc_orth(start, end)
            vecs.extend(vec3)

    return vecs

#https://arxiv.org/pdf/1802.03345.pdf page 25
#https://en.wikipedia.org/wiki/Dilation_(morphology)
# this implementation creates the seperator class (no morphology whatsovever)


def create_seperator_class(tree):
    root = tree.getroot()
    el = None
    if root.find('{http://www.w3.org/2000/svg}g'):
        el = root.find('{http://www.w3.org/2000/svg}g')
        paths = el.findall('{http://www.w3.org/2000/svg}path')
    else:
        paths = root.findall('{http://www.w3.org/2000/svg}path')

    lines = []
    curves = []
    for i in paths:
        bline_raw = i.attrib['d']
        try:
            bline_raw = i.attrib['{http://www.inkscape.org/namespaces/inkscape}original-d']
        except:
            print("wut")
        letter = bline_raw.split(' ')[0]
        bline_parsed = bline_raw.split(' ')[1:]
        if len(bline_parsed) == 2 and letter == 'm':
            start = split_c(bline_parsed[0])
            end = tuple(np.add(start, split_c(bline_parsed[1])))
            lines.append([start, end])
        if len(bline_parsed) == 2 and letter == 'M':
            start = split_c(bline_parsed[0])
            end = split_c(bline_parsed[-1])
            lines.append([start, end])
        elif len(bline_parsed) >= 2 and bline_parsed[1] == 'c':
            start = split_c(bline_parsed[0])
            start_2 = tuple(np.add(start, split_c(bline_parsed[2])))
            end = tuple(np.add(start, split_c(bline_parsed[-1])))
            end_2 = tuple(np.subtract(end, split_c(bline_parsed[-2])))
            if start == start_2 or end == end_2:
                p = parse_path(bline_raw)
                lines.append([(p[1].start.real, p[1].start.imag), (p[-1].end.real, p[-1].end.imag)])
            else:
                curves.append([start, start_2])
                curves.append([end, end_2])
    print(lines)
    print(curves)
    vecs = calc_sep(lines, curves)

    for i, j in enumerate(vecs):
        seperator = f'<path id="sep{i}" d="m {j[0][0]},{j[0][1]} {j[1][0]},{j[1][1]}" style = "fill:none;stroke:#ff0000;stroke-width:3" />'
        seperator = ET.fromstring(seperator)
        seperator.tag = '{http://www.w3.org/2000/svg}path'
        if el:
            el.insert(-1, seperator)
        else:
            root.insert(-1, seperator)

    return tree


if __name__ == "__main__":
    MAX_SIZE = 10000000 # estimated by trial and error
    sorted_imgs = sort_img_sizes()
    pretty_print_dict(sorted_imgs)
    delete_old_files()
    create_data(sorted_imgs, MAX_SIZE, True)
    create_txts_with_paths(0.9, sorted_imgs)






