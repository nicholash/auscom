#!/usr/bin/env python 

import sys
import os
import re
import argparse
import numpy as np
import netCDF4 as nc

"""
Combine per-procs output files into a single netcdf file.
"""

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('var', help='Variable to be combined, and the prefix of the input files.')
    parser.add_argument('x_procs', help='The number of procs in the x direction.')
    parser.add_argument('y_procs', help='The number of procs in the y direction.')
    parser.add_argument('--dir', help='The directory containing input files.', default='./')
    parser.add_argument('--verbose', help='Print progress.', action='store_true')
    args = parser.parse_args()
        
    postfix = '.nc'
    x_procs = int(args.x_procs)
    y_procs = int(args.y_procs)

    # Get the file names of all netcdf files that have form: var.<numbers>.nc
    input_files = [f for f in os.listdir(args.dir) if re.search(r'^%s\.\d+\%s$' % (args.var, postfix), f)]
    assert(len(input_files) == x_procs * y_procs)

    # Expect all files to be the same length. 
    assert(all([len(f) == len(input_files[0]) for f in input_files]))

    # Needed to calculate output dimensions and check dimensions of other inputs.
    f = nc.Dataset(args.dir + input_files[0])
    x_dim = len(f.dimensions['x'])
    y_dim = len(f.dimensions['y'])
    t_dim = len(f.dimensions['t'])
    f.close()

    # Open the output file and create dimensions and variable
    output = nc.Dataset(args.var + postfix, 'w')
    output.createDimension('x', x_dim * x_procs)
    output.createDimension('y', y_dim * y_procs)
    output.createDimension('t', t_dim)
    output.createVariable(args.var, 'f', ('t', 'y', 'x'))

    # Number of digits in the input file number.
    digits = len(input_files[0]) - len(args.var) - len('.') - len(postfix)

    fnum = 0
    y_start = 0
    not_zero = False
    for y in range(y_procs):

        x_start = 0
        for x in range(x_procs):

            # Construct the filename for this proc, open it and copy to output file.
            basename = args.var + '.' + str(fnum).zfill(digits) + postfix
            filename = os.path.join(args.dir, basename)

            if args.verbose:
                print 'Processing %s' % filename

            if not os.path.exists(filename):
                sys.stderr.write('File %s, not found' % filename)
                output.close()
                return 1

            input_file = nc.Dataset(filename)
            assert((len(input_file.dimensions['x']) == x_dim) and (len(input_file.dimensions['y']) == y_dim))
            output.variables[args.var][:,y_start:(y_start + y_dim),x_start:(x_start + x_dim)] = input_file.variables[args.var][:,:,:]
            input_file.close()

            fnum = fnum + 1

            x_start = x_start + x_dim

        y_start = y_start + y_dim

    output.close()

if __name__ == "__main__":
    sys.exit(main())
