#!/usr/bin/env python

import sys
import argparse
import shutil
import numpy as np
import netCDF4 as nc
from scipy import signal

"""
Smooth out bathymetry by applying a gaussian blur. 

See: http://wiki.scipy.org/Cookbook/SignalSmooth

Convolving a noisy image with a gaussian kernel (or any bell-shaped curve)
blurs the noise out and leaves the low-frequency details of the image standing
out. 

After smoothing various things need to be fixed up:
    - A minimum depth should be set, e.g. we don't want ocean depths of < 1m 
    - All land points should be the same in the smoothed bathymetry.
"""

def gauss_kern(size, sizey=None):
    """ Returns a normalized 2D gauss kernel array for convolutions """
    size = int(size)
    if not sizey:
        sizey = size
    else:
        sizey = int(sizey)
    x, y = np.mgrid[-size:size+1, -sizey:sizey+1]
    g = np.exp(-(x**2/float(size) + y**2/float(sizey)))
    return g / g.sum()


def blur_image(im, n, ny=None) :
    """ 
    Blurs the image by convolving with a gaussian kernel of typical
    size n. The optional keyword argument ny allows for a different
    size in the y direction.
    """
    g = gauss_kern(n, sizey=ny)
    improc = signal.convolve(im, g, mode='valid')

    return improc

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("point_x", help="x coordinate of centre point.", type=int)
    parser.add_argument("point_y", help="y coordinate of centre point.", type=int)
    parser.add_argument("size", help="""
                         Rows and columns that will be smoothed. For example if size == 10,
                         then a 10x10 array centred at (x, y) will be smoothed.""", type=int)
    parser.add_argument("--kernel", help="Size of guassian kernel.", default=5, type=int)
    parser.add_argument("--minimum_depth", help="""
                        After smoothing, set values to a minimum depth.
                        This is used to fix up shallow waters""", default=40, type=int)
    parser.add_argument("input_file", help="Name of the input file.")
    parser.add_argument("input_var", help="Name of the variable to blur.")
    parser.add_argument("output_file", help="Name of the output file.")
    args = parser.parse_args()

    shutil.copy(args.input_file, args.output_file)

    f = nc.Dataset(args.output_file, mode='r+')
    input_var = f.variables[args.input_var][:]

    north_ext = args.point_y + args.size
    assert(north_ext < input_var.shape[0])
    south_ext = args.point_y - args.size
    assert(south_ext >= 0)
    east_ext = args.point_x + args.size
    assert(east_ext < input_var.shape[1])
    west_ext = args.point_x - args.size
    assert(west_ext >= 0)

    input_var = input_var[south_ext:north_ext,west_ext:east_ext]

    # We need to extend/pad the array by <kernel> points along each edge.
    var = np.pad(input_var, (args.kernel, args.kernel), mode='edge')
    smoothed = blur_image(var, args.kernel)

    # After smoothing make sure that there is a certain minimum depth.
    smoothed[(smoothed > 0) & (smoothed < args.minimum_depth)] = args.minimum_depth

    # Ensure that all land points remain the same.
    smoothed[input_var == 0] = 0

    f.variables[args.input_var][south_ext:north_ext,west_ext:east_ext] = smoothed 
    f.close()


if __name__ == '__main__':
    sys.exit(main())
