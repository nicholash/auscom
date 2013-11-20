#!/usr/bin/env python

import sys
import argparse

"""
Use MayaVi to visualise the bathymetry at a certain point.
"""

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("point_x", help="x coordinate of point.")
    parser.add_argument("point_y", help="y coordinate of point.")
    parser.add_argument("--halo", help="Halo around the point to display.", default=100)
    parser.add_argument("--topo", help="The bathymetry file.", default='topog.nc')


if __name__ == '__main__':
    sys.exit(main())
