#!/usr/bin/env python

from __future__ import print_function

import sys
import argparse
import numpy as np
import netCDF4 as nc

"""
Check the physical ranges of fields in the coupling dumps.
"""

var_ranges = {'mh_flux' : (-1000, 0)} 

def check_mask(var, var_name, mask):
    """
    Check that all masked points are zero.

    Returns True if they are. 
    """

    num_non_zero_points = np.count_nonzero(var[mask])
    if num_non_zero_points != 0:
        print('Masking: there are {num} non-zero masked points in var {var}'.format(num=num_non_zero_points, var=var_name))
        return False

    return True

def check_var_range(var, var_name):
    """
    Check the physical range of var against predefined limits. 

    Return True if all points are within expected range. 
    """

    if var_name not in var_ranges:
        return True

    (min, max) = var_ranges[var_name]

    found = False
    num_out_of_range_points = np.count_nonzero(var < min)
    if num_out_of_range_points != 0:
        print('Var ranges: there are {num} points below the minimum in var {var}'.format(num=num_out_of_range_points, var=var_name))
        found = True

    num_out_of_range_points = np.count_nonzero(var > max)
    if num_out_of_range_points != 0:
        print('Var ranges: there are {num} points above the maximum in var {var}'.format(num=num_out_of_range_points, var=var_name))
        found = True

    return not found


def is_field_variable(var):
    """
    Checks whether this is a field variable, as opposed to a dimension var. 
    """

    return (len(var.shape) == 3)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('mask_file', help='Name of the mask input file.')
    parser.add_argument('mask_var', help='Name of the mask variable.')
    parser.add_argument('check_file', help='Name of the file to check.')
    parser.add_argument('--flip_mask', action='store_true', default=False, help='Take masked values to be 1, not 0.')
    args = parser.parse_args()

    with nc.Dataset(args.mask_file) as f:
        mask = f.variables[args.mask_var][:]
        mask = mask.astype(bool)
        if args.flip_mask:
            mask = ~mask

    check_f = nc.Dataset(args.check_file)

    # Iterate over all variables. 
    for var_name, v in check_f.variables.iteritems():
        if not is_field_variable(v):
            continue

        # Iterate over all time points.
        for t in range(v.shape[0]):
            var = v[t,:,:]

            if not check_mask(var, var_name, mask):
                break
        
        for t in range(v.shape[0]):
            var = v[t,:,:]

            if not check_var_range(var, var_name):
                break
                
    return 0

if __name__ == '__main__':
    sys.exit(main())
