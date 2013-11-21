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
    parser.add_argument("--halo", help="Halo around the point to display.", type=int, default=50)
    parser.add_argument("--topo", help="The bathymetry file.", default='topog.nc')
    args = parser.parse_args()

    f = nc.Dataset(args.topo)
    topo = f.variables['depth'][:]

    mlab.surf(topo[(args.point_y - args.halo):(args.point_y + args.halo), (args.point_x - args.halo):(args.point_x + args.halo)], warp_scale=0.005)
    mlab.points3d([0], [0], [0], color=(1, 0, 0), scale_factor=1.0)
    mlab.show()

if __name__ == '__main__':
    sys.exit(main())
