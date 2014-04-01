#!/usr/bin/env python 

from __future__ import print_function

import sys
import os
import argparse
import netCDF4 as nc

"""
Combine per-proc dumps into a single global field.
"""

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('var_name', help='Name of the variable to combine.')
    parser.add_argument('--path', help='Path to directory where all the inputs are found.')
    args = parser.parse_args()

    if not args.path:
        args.path = './'

    # Get some details from the first input.
    time_pts = 0
    with nc.Dataset('{}.000000.nc'.format(os.path.join(args.path, args.var_name))) as f:
        time_pts = f.variables[args.var_name].shape[0]
    assert(time_pts != 0)

    # Set up the output.
    output = nc.Dataset('{}.nc'.format(args.var_name), 'w')
    output.createDimension('nx', 1440)
    output.createDimension('ny', 1080)
    output.createDimension('time', time_pts)
    output.createVariable('time', 'f8', ('time'))
    output.createVariable(args.var_name, 'f8', ('time', 'ny', 'nx'))

    # Open each file in turn, copy over each slab to the output. 
    cpu_id = 0
    for j in range(30):
        for i in range(32):
            input_name = '{}.{}.nc'.format(os.path.join(args.path, args.var_name), str(cpu_id).zfill(6))
            print('combining {}'.format(input_name))
            with nc.Dataset(input_name) as f:
                x_start = i * 45
                x_end = ((i + 1) * 45)
                y_start = j * 36
                y_end = ((j + 1) * 36)
                # Not that we need to exclude halos in the input. 
                output.variables[args.var_name][:,y_start:y_end,x_start:x_end] = f.variables[args.var_name][:,1:-1,1:-1]
            cpu_id += 1
        
    output.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
