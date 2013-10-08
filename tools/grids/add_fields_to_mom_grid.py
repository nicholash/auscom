#!/usr/bin/env python

import sys
import os
import argparse
import numpy as np
from numpy.testing import assert_almost_equal

import netCDF4 as nc

"""
Add T cell area to the mom5 grid.
"""

def add_t_cell_area():

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="mom5 grid file.")

    args = parser.parse_args()

    f = nc.Dataset(args.input_file, 'r+')
    area = np.copy(f.variables['area'])

    f.createDimension('nyt', area.shape[0] / 2)
    f.createDimension('nxt', area.shape[1] / 2)

    tarea = f.createVariable('tarea', 'f8', ('nyt', 'nxt'))
    tarea.units = "m2"
    tarea.title = "Grid t-cell area."

    # The ocean areas are actually 1/4 cell areas because they are calculated 
    # between neighbouring T and U points. The way to get a full T cell area
    # (which is what we want) is to add up all areas surrounding a T point.
    tarea[:] = area[::2,::2] + area[::2, 1::2] + area[1::2,1::2] + area[1::2,::2]

    # This is equivalent to abs(desired-actual) < 0.5 * 10**(-decimal)
    assert_almost_equal(np.sum(area), np.sum(tarea[:]), decimal=-1)

    f.close()

def main():
    add_t_cell_area()

if __name__ == "__main__":
    sys.exit(main())

