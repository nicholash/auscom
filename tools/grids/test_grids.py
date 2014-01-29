#!/usr/bin/env python

"""
Run some tests on grids.
"""

import sys
import netCDF4 as nc
import numpy as np
from numpy.testing import assert_array_equal, assert_almost_equal

def test_for_concave(grid):
    """
    Test that a grid cell is not concave. 
    """ 
    pass


def test_physical(grid):
    """
    Test that grid is physically reasonable.
    """
    pass


def test_same_area(src, dest):
    """
    Test that source and destination grids cover the same area. 
    """

    src_area = np.copy(src.variables['tarea'])
    dest_area = np.copy(dest.variables['tarea'])

    # This is equivalent to abs(desired-actual) < 0.5 * 10**(-decimal)
    assert_almost_equal(np.sum(src_area), np.sum(dest_area[:]), decimal=-1)

def test_overlapping(src, dest):
    """
    Test that each destination cell is covered by one or more sources.
    """
    
    # A naive approach is to check whether each destination point is within some source grid cell.
    # This will be n^2 in the number of grid points/cells.

    # Another option is to build binary trees of lat and lon intervals, then check that each dest point
    # lies within these.
                
def main():

    dest_grid = nc.Dataset('grid.new.nc', 'r')
    src_grid = nc.Dataset('grid.nc', 'r')

    test_same_area(src_grid, dest_grid)

if __name__ == "__main__":
    sys.exit(main())
