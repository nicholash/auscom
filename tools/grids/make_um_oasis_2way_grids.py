#!/usr/bin/env python

import sys
import os
import shutil
import argparse

import netCDF4 as nc

"""
Start with working oasis grids, areas, and masks files. From this create *_recv and *_send versions of all atmos related fields. The difference between these is that in the *_send versions the atmosphere has no mask, the whole field is passed to the ocean. This means that there will be no missing data in places where the atmos grid does not overlap with the ocean grid. This missing data can make interpolation difficult.

Basically the atmos covers the whole globe, so just pass it all to the ocean and let the ocean figure out which bits to use. 
"""


def copy_fields(field_names, source_file, dest_file):

    copy_cmd = ''

    for f in field_names:
        copy_cmd += 'echo "a" | ncks -v {field} {input} {output} > /dev/null; '.format(field=f, input=source_file, output=dest_file)

    os.system(copy_cmd)


def rename_fields(source_names, dest_names, file):

    rename_cmd = 'ncrename ' 

    for src, dest in zip(source_names, dest_names):
        rename_cmd += ' -v {src},{dest} '.format(src=src, dest=dest)

    rename_cmd += '{input}'.format(input=file)
    os.system(rename_cmd)


def make_areas(input_areas):
    """
    This is much the smae as make_grids(). 
    """

    orig_names = ['um1t.srf', 'um1u.srf', 'um1v.srf']
    send_names = ['us1t.srf', 'us1u.srf', 'us1v.srf']
    recv_names = ['ur1t.srf', 'ur1u.srf', 'ur1v.srf']

    shutil.copy(input_areas, 'areas.nc')

    rename_fields(orig_names, send_names, 'areas.nc')
    copy_fields(orig_names, input_areas, 'areas.nc')
    rename_fields(orig_names, recv_names, 'areas.nc')


def make_grids(input_grid):
    """
    Gather together all the fields needed for the grids.nc file.
    """

    orig_names = ['um1t.lon', 'um1t.lat', 'um1t.ang', 'um1t.clo', 'um1t.cla', 'um1u.lon', 'um1u.lat', 'um1u.ang', 'um1u.clo', 'um1u.cla', 'um1v.lon', 'um1v.lat', 'um1v.ang', 'um1v.clo', 'um1v.cla']
    send_names = ['us1t.lon', 'us1t.lat', 'us1t.ang', 'us1t.clo', 'us1t.cla', 'us1u.lon', 'us1u.lat', 'us1u.ang', 'us1u.clo', 'us1u.cla', 'us1v.lon', 'us1v.lat', 'us1v.ang', 'us1v.clo', 'us1v.cla']
    recv_names = ['ur1t.lon', 'ur1t.lat', 'ur1t.ang', 'ur1t.clo', 'ur1t.cla', 'ur1u.lon', 'ur1u.lat', 'ur1u.ang', 'ur1u.clo', 'ur1u.cla', 'ur1v.lon', 'ur1v.lat', 'ur1v.ang', 'ur1v.clo', 'ur1v.cla']

    # Copy the whole file. 
    shutil.copy(input_grid, 'grids.nc')

    # Rename/copy some fields
    rename_fields(orig_names, send_names, 'grids.nc')
    copy_fields(orig_names, input_grid, 'grids.nc')
    rename_fields(orig_names, recv_names, 'grids.nc')


def make_masks(input_mask):
    """
    Copy the original masks to new names. Modify the send mask to be all unmasked. 
    """

    orig_names = ['um1t.msk', 'um1u.msk', 'um1v.msk']
    send_names = ['us1t.msk', 'us1u.msk', 'us1v.msk']
    recv_names = ['ur1t.msk', 'ur1u.msk', 'ur1v.msk']

    # Copy the whole file. 
    shutil.copy(input_mask, 'masks.nc')

    rename_fields(orig_names, send_names, 'masks.nc')
    copy_fields(orig_names, input_mask, 'masks.nc')
    rename_fields(orig_names, recv_names, 'masks.nc')

    # Now make the send mask completely unmasked.     
    # Oasis treats 1 as 'masked'.

    with nc.Dataset('masks.nc', 'r+') as f:
        for n in send_names:
            f.variables[n][:] = 0

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("masks", help="Existing OASIS masks file, this should not be in the current directory. \
                                       The newly created masks file is written to the current directory.")
    parser.add_argument("grids", help="Existing OASIS grids file. Should not be in the current directory.")
    parser.add_argument("areas", help="Existing OASIS areas file. Should not be in the current directory.")

    args = parser.parse_args()

    make_grids(args.grids)

    make_masks(args.masks)

    make_areas(args.areas)


if __name__ == "__main__":
    sys.exit(main())

