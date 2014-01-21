#!/usr/bin/env python

import sys
import struct
import numpy as np
import argparse
import netCDF4 as nc

def read_header(file, print_it):
    """
    """

    # Header is the first 24 bytes of the file. 
    header = file.read(24)
    _, num_steps, time, time_forc = struct.unpack('>iidd', header)
    if print_it:
        print "istep0=%d" % num_steps
        print "time=%f" % time
        print "time_forc=%f" % time_forc

    return (num_steps, time, time_forc)

def write_header(file):
    pass

def read_field(file, nx, ny):
    
    # Read the record separator. 
    _ = file.read(8)
    # Read buffer. 
    buf = file.read(8*nx*ny)
    return np.reshape(struct.unpack('>'+str(nx*ny)+'d',buf),(ny,nx))

def convert_to_netcdf(restart_file, output_file, config):
    """
    Convert a CICE restart file to netcdf.
    """
    nx = config['nx']
    ny = config['ny']

    # Set up netcdf file. 
    f_ice = nc.Dataset(output_file, 'w')
    f_ice.createDimension('nx', nx)
    f_ice.createDimension('ny', ny)
    f_ice.createDimension('num_ice_cat', config['num_ice_cat'])
    f_ice.createDimension('num_ice_layers', config['num_ice_layers'])
    f_ice.createDimension('num_snow_layers', config['num_snow_layers'])

    # FIXME: improve variable names and add descriptions.
    for var in ['aicen', 'vicen', 'vsnon', 'trcrn']:
        v = f_ice.createVariable(var, 'f8', dimensions=('num_ice_cat', 'ny', 'nx'))
        for n in range(config['num_ice_cat']):
            v[n,:,:] = read_field(restart_file, nx, ny)

    eicen = f_ice.createVariable('eicen', 'f8', dimensions=('num_ice_layers', 'ny', 'nx'))
    for n in range(config['num_ice_layers']):
        eicen[n,:,:] = read_field(restart_file, nx, ny)
    esnon = f_ice.createVariable('esnon', 'f8', dimensions=('num_snow_layers', 'ny', 'nx'))
    for n in range(config['num_snow_layers']):
        esnon[n,:,:] = read_field(restart_file, nx, ny)

    vars = ['uvel', 'vvel', 'scale_factor', 'swvdr', 'swvdf', 'swir', 'swif', 'strocnxT', 'strocnyT', \
            'stressp_1', 'stressp_2', 'stressp_3', 'stressp_4', 'stressm_1', 'stressm_2', 'stressm_3',\
            'stressm_4', 'stress12_1', 'stress12_2', 'stress12_3', 'sstress12_4', 'iceumask']
    for var in vars:
        v = f_ice.createVariable(var, 'f8', dimensions=('ny', 'nx'))
        v[:,:] = read_field(restart_file, nx, ny)

    f_ice.close()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="The input file to read.")
    parser.add_argument("--output", help="The output file to write.")
    parser.add_argument("--print_header", action='store_true', default=False, help="Print the header fields.")
    parser.add_argument("--nx", default=1440, type=int, help="Number of x points.")
    parser.add_argument("--ny", default=1080, type=int, help="Number of x points.")
    parser.add_argument("--num_ice_cat", default=5, type=int, help="The number of ice categories.")
    parser.add_argument("--num_ice_layers", default=4, type=int, help="The number of ice layers.")
    parser.add_argument("--num_snow_layers", default=1, type=int, help="The number of snow layers.")

    args = parser.parse_args()

    output = args.input + '.nc'
    if args.output is not None:
        output = args.output

    config = {}
    config['nx'] = args.nx # number of points in x.
    config['ny'] = args.ny # number of points in y.
    config['num_ice_cat'] = args.num_ice_cat # number of ice categories.
    config['num_ice_layers'] = args.num_ice_layers 
    config['num_snow_layers'] = args.num_snow_layers 

    file = open(args.input, 'rb')
    read_header(file, args.print_header)
    convert_to_netcdf(file, output, config)
    file.close()

if __name__ == '__main__':
    sys.exit(main())

