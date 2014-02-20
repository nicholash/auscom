#!/usr/bin/env python

import sys
import argparse
import numpy as np
import netCDF4 as nc

"""
Check that bathymetry and mask have the same land points. 
"""

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("bathymetry_file", help="Name of the bathymetry input file.")
    parser.add_argument("bathymetry_var", help="Name of the bathymetry variable.")
    parser.add_argument("mask_file", help="Name of the mask input file.")
    parser.add_argument("mask_var", help="Name of the mask variable.")
    args = parser.parse_args()

    bath_f = nc.Dataset(args.bathymetry_file)
    mask_f = nc.Dataset(args.mask_file)

    bath = bath_f.variables[args.bathymetry_var][:]
    mask = mask_f.variables[args.mask_var][:]

    bath_f.close()
    mask_f.close()

    # If the mask has land at a certain point the bathymetry must also.
    if not (bath[mask == 0] == 0).all():
        sys.stderr.write("Error: There are land points in the mask that are not depth 0 in the bathymetry.\n")
        return 1

    # Give a warning if the bathymetry has land points but the mask doesn't.
    if not (mask[bath == 0] == 0).all():
        sys.stdout.write("Warning: the bathymetry has land points where the mask does not.\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
