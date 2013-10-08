#!/usr/bin/env python

import sys
import ast
import numpy as np
import netCDF4 as nc
import argparse
from mayavi import mlab
from mayavi.sources.builtin_surface import BuiltinSurface

"""
Read in a number of grids and plot the T and U cells for each.

A good way to visualise and compare grids.
"""

def draw_earth():

    mlab.figure(1, bgcolor=(0.48, 0.48, 0.48), fgcolor=(0, 0, 0),
                   size=(400, 400))
    mlab.clf()

    # Display continents outline, using the VTK Builtin surface 'Earth'
    continents_src = BuiltinSurface(source='earth', name='Continents')
    # The on_ratio of the Earth source controls the level of detail of the
    # continents outline.
    continents_src.data_source.on_ratio = 2 
    continents = mlab.pipeline.surface(continents_src, color=(0, 0, 0))

    # Display a semi-transparent sphere, for the surface of the Earth
    # We use a sphere Glyph, throught the points3d mlab function, rather than
    # building the mesh ourselves, because it gives a better transparent
    # rendering.
    sphere = mlab.points3d(0, 0, 0, scale_mode='none', scale_factor=2, color=(0.67, 0.77, 0.93),
                           resolution=50, opacity=0.7, name='Earth')

    # These parameters, as well as the color, where tweaked through the GUI,
    # with the record mode to produce lines of code usable in a script.
    sphere.actor.property.specular = 0.45
    sphere.actor.property.specular_power = 5
    # Backface culling is necessary for better transparent rendering.
    sphere.actor.property.backface_culling = True

def draw_grid(lons, lats, color=(0, 0, 1)):

    # Display grid points. 
    x = np.cos(lons) * np.cos(lats)
    y = np.sin(lons) * np.cos(lats)
    z = np.sin(lats)

    #points = mlab.points3d(x, y, z, scale_mode='none', scale_factor=0.1, color=color)

    # Draw parallels
    for i in range(x.shape[0]):
        # Appends the last point to the first. 
        mlab.plot3d(np.append(x[i,:], x[i,0:1]), np.append(y[i,:], y[i,0:1]), 
                    np.append(z[i,:], z[i,0:1]), line_width=1.0, tube_radius=None, color=color)

    # Draw meridians 
    for i in range(x.shape[1]):
        mlab.plot3d(x[:,i], y[:,i], z[:,i], line_width=1.0, tube_radius=None, color=color)


def display():

    mlab.view(63.4, 73.8, 4, [-0.05, 0, 0])
    mlab.show()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("fields", help="A Python list of field tuples. \
                         Each tuple is filename, latitude field, longitude field, units, lat resolution, lon resolution, colour. \
                         The colour is a tuple: (red, green, blue), each color ranging from 0 to 1. \
                         The units can be degrees or radians. \
                         The grid may not have exactly the requested resolution because min and max latitudes are always drawn. \
                         For example to plot 40 lat and lon points from an ocean grid in blue: %s \"[('ocean_hgrid.nc', 'x', 'y', 40, 40,'degrees',(1, 0, 0))]\". \
                         Don't forget the double and single quotes." % (sys.argv[0]))

    args = parser.parse_args()

    draw_earth()

    for file_name, lat_name, lon_name, units, lat_res, lon_res, colour in ast.literal_eval(args.fields):
        f = nc.Dataset(file_name, 'r')
        lon = np.copy(f.variables[lon_name])
        lat = np.copy(f.variables[lat_name])
        f.close()

        if units == 'degrees':
            lat = np.deg2rad(lat)
            lon = np.deg2rad(lon)

        row_skip = lon.shape[0] / lat_res 
        col_skip = lon.shape[1] / lon_res

        reduced_lon = lon[::row_skip,::col_skip]
        reduced_lat = lat[::row_skip,::col_skip]

        # Make sure the last (top) parallel is included.
        if not np.array_equal(lat[-1,::col_skip], reduced_lat[-1,]):
            reduced_lon = np.append(reduced_lon, lon[-1:,::col_skip], axis=0)
            reduced_lat = np.append(reduced_lat, lat[-1:,::col_skip], axis=0)

        draw_grid(reduced_lon, reduced_lat, colour)

    display()
    return 0

if __name__ == "__main__":
    sys.exit(main())

