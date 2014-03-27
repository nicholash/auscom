#!/usr/bin/env python

from __future__ import print_function

import sys
import argparse
import numpy as np
import netCDF4 as nc

"""
Check that a field is 0 on all masked points. 

The mask treats 1, or True values as masked. 
"""

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

    # Iterate over all time points.
    for var_name, v in check_f.variables.iteritems():
        if not is_field_variable(v):
            continue

        print_warning = True
        for t in range(v.shape[0]):
            var = v[t,:,:]
            num_non_zero_points = np.count_nonzero(var[mask])
            if (num_non_zero_points != 0) and print_warning:
                print('There are {num} non-zero masked points in var {var}'.format(num=num_non_zero_points, var=var_name, time=t))
                print_warning = False
                
    return 0

if __name__ == '__main__':
    sys.exit(main())
