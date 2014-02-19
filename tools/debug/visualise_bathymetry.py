#!/usr/bin/env python

import sys
import argparse
import numpy as np
import netCDF4 as nc
import mayavi.mlab as mlab

"""
Use MayaVi to visualise the bathymetry at a certain point.
"""

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("point_x", help="x coordinate of point.", type=int)
    parser.add_argument("point_y", help="y coordinate of point.", type=int)
    parser.add_argument("file", help="The bathymetry file.")
    parser.add_argument("--halo", help="Size of halo.", type=int, default=50)
    args = parser.parse_args()

    f = nc.Dataset(args.file)
    topo = f.variables['depth'][:]

    # Calculate the extents of the topo array to show. We don't just add halo to (point_x, point_y)
    # because it may run off the edge of the map.
    north_ext = min(args.point_y + args.halo, topo.shape[0])
    south_ext = max(args.point_y - args.halo, 0)
    east_ext = min(args.point_x + args.halo, topo.shape[1])
    west_ext = max(args.point_x - args.halo, 0)

    width = east_ext - west_ext
    height = north_ext - south_ext

    # The origin of the figure in global coordinates.
    origin_x = west_ext + width / 2
    origin_y = south_ext + height / 2

    point_y = args.point_y - origin_y
    point_x = args.point_x - origin_x

    mlab.surf(topo[south_ext:north_ext, west_ext:east_ext], warp_scale=0.005)
    mlab.points3d([point_y], [point_x], [0], color=(1, 0, 0), scale_factor=1.0)
    mlab.show()

if __name__ == '__main__':
    sys.exit(main())
