import time
import sys
import os
from os import path
from itertools import product

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import format_io as f_io


def main():
    plants = ["simple_plant", "coffee", "DA1_Average_MAP_90"]
    format = ["mtg", "opf", "gltf", "glb", "vtp"]

    plants_df = []
    format_df = []
    reading_time = []
    vertices_nb = []
    file_size = []

    for p,f in product(plants,format):
        file = "%s/%s.%s"%(p,p,f)
        plants_df.append(p)
        format_df.append(f)

        if path.exists(file):
            io = f_io.io(file)

            ctime = time.time()
            io.read()
            reading_time.append( time.time() - ctime)

            vertices_nb.append(len(io.g))
            file_size.append(path.getsize(file))
        else:
            reading_time.append(float('nan'))
            vertices_nb.append(0)
            file_size.append(0)

    d = {
        "plants":plants_df,
        "format":format_df,
        "reading_time":reading_time,
        "vertices_nb":vertices_nb,
        "file_size":file_size
    }

    df = pd.DataFrame(d)
    df.to_csv("compare.csv")

def plot():
    df = pd.read_csv("compare.csv")
    df_no_nan = df[~df["reading_time"].isna()]
    
    time = df_no_nan["reading_time"]
    size = df_no_nan["file_size"]

    formats = df_no_nan["format"]

    fig, axs = plt.subplots(1,2, sharey=True)

    for f in formats.unique():
        selected = df_no_nan[df_no_nan["format"]==f]
        size_of_format = selected["file_size"]/(1024**2)
        time_of_format = selected["reading_time"]
        vertices_nb = selected["vertices_nb"]
        axs[0].scatter(size_of_format, time_of_format, label = f)
        axs[1].scatter(vertices_nb, time_of_format, label = f)

    axs[1].set_xlabel('Mtg nodes number')
    # axs[1].set_ylabel('time for constructing mtg (s)')
    axs[1].set_yscale("log")
    axs[1].set_xscale("log")
    axs[1].legend()

    axs[0].set_xlabel('file size (Mb)')
    axs[0].set_ylabel('time for constructing mtg (s)')
    axs[0].set_yscale("log")
    axs[0].set_xscale("log")
    axs[0].legend()


    # plt.xscale('log')
    # plt.yscale('log')
    # plt.legend()
    fig.set_tight_layout(True)
    plt.show()



if __name__ == "__main__":
    arg = sys.argv[1]
    if arg == "plot":
        plot()
    elif arg == "main":
        main()