#!/usr/bin/env python 

import sys
import os
import re
import argparse
import netCDF4 as nc

"""
Combine per-procs output files into a single netcdf file.
"""

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('prefix', help='Prefix of the input files.')
    parser.add_argument('x_procs', help='The number of procs in the x direction.')
    parser.add_argument('y_procs', help='The number of procs in the y direction.')
    parser.add_argument('--dir', help='The directory containing input files.', default='./')
    args = parser.parse_args()
        
    postfix = '.nc'

    # Get the file names of all netcdf files that have form: prefix<numbers>.nc
    input_files = [f for f in os.listdir(args.dir) if re.search(r'%s\d+\%s$' % (args.prefix, postfix), f)]
    assert(len(input_files) == x_procs * y_procs)

    # Expect all files to be the same length. 
    assert(all([len(f) == len(input_files[0]) for f in input_files]))

    # Figure out what the output dimension should be.
    with nc.Dataset(input_files[0], 'r') as f:
        x_dim = f.dimensions['x'] * args.x_procs
        y_dim = f.dimensions['y'] * args.y_procs
        t_dim = f.dimensions['t']
        var = f.variables.keys()[0]

    # Open the output file and create dimensions and variable
    output = nc.Dataset(args.prefix + postfix, 'r+')
    output.createDimension('x', x_dim)
    output.createDimension('y', y_dim)
    output.createDimension('t', t_dim)
    output.createVariable(var, 'f8', ('t', 'y', 'x'))

    # Number of digits in the input file number.
    digits = len(files[0]) - len(args.prefix) - len(postfix)

    fnum = 0
    y_start = 0
    x_start = 0
    for y in y_procs:
        for x in x_procs:

            # Construct the filename for this proc, open it and copy to output file.
            filename = args.prefix + str(fnum).zfill(digits) + postfix

            with nc.Dataset(filename) as input_file:
                output.variables[var][:,ystart:,xstart:] = input_file[var][:,:,:]

            print 'Copied %s' % filename
            fnum = fnum + 1

            x_start = x_start + y_dim

        y_start = y_start + y_dim

if __name__ == "__main__":
    sys.exit(main())
