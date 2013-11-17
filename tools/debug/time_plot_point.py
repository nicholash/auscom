#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np
import scipy.io.netcdf as nc
import sys
import argparse
import ast

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("point_x", help="x coordinate of point.")
    parser.add_argument("point_y", help="y coordinate of point.")
    parser.add_argument("--fields", help="A Python list of file, field tuples describing fields to plot.")
    parser.add_argument("--all", help="Plot all fields in the file.")

    args = parser.parse_args()
    field_list = []
    if args.fields:
        field_list = ast.literal_eval(args.fields)

    if args.all:
        file = nc.netcdf_file(args.all)
        for name in file.variables.keys():
            if name != 'time':
                field_list.append((args.all, name))
        file.close()
        
    assert(field_list != [])

    fignum = 1
    for filename, field in field_list:

        file = nc.netcdf_file(filename)
        v = file.variables[field][:]

        t = range(v.shape[0])
        y = v[:, int(args.point_x), int(args.point_y)]

        plt.subplot(len(field_list), 1, fignum)
        fignum = fignum + 1
        p, = plt.plot(t, y)
        plt.legend([p], [field])


    plt.show()

if __name__ == '__main__':
    sys.exit(main())
