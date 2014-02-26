#!/usr/bin/env python

import sys, os
import argparse
import ast
import ESMP
import netCDF4 as nc
import numpy as np

"""
Regrid CICE inputs, based on ESMP tutorial at:
http://www.earthsystemmodeling.org/python_releases/last_esmp/python_doc/html/index.html
"""

def find_nearest(a, val):
    """
    Index of element in array closest to the scalar value 'val'.
    """
    return np.abs(a[0,:,:] - val).argmin()

def build_analytic_field(field, grid, domask):
    '''
    PRECONDITIONS: An ESMP_Field has been created as 'field'.  'grid' has
                   been created and coordinates have been set on both the
                   center and corner stagger locations.  'mask' holds the 
                   masked values of 'grid'.\n
    POSTCONDITIONS: The 'field' has been initialized to an analytic field.\n
    RETURN VALUES: \n ESMP_Field :: field \n
    '''
    DEG2RAD = 3.141592653589793/180.0

    # get the field pointer
    fieldPtr = ESMP.ESMP_FieldGetPtr(field) 
     
    # get the grid bounds and coordinate pointers
    exLB, exUB = ESMP.ESMP_GridGetCoord(grid, ESMP.ESMP_STAGGERLOC_CENTER)

    # get the mask
    if domask:
        mask = ESMP.ESMP_GridGetItem(grid, item=ESMP.ESMP_GRIDITEM_MASK)

    # get the coordinate pointers and set the coordinates
    [x,y] = [0, 1]
    gridXCoord = ESMP.ESMP_GridGetCoordPtr(grid, x, ESMP.ESMP_STAGGERLOC_CENTER)
    gridYCoord = ESMP.ESMP_GridGetCoordPtr(grid, y, ESMP.ESMP_STAGGERLOC_CENTER)

    p = 0 
    for i1 in range(exLB[1], exUB[1]): 
        for i0 in range(exLB[0], exUB[0]): 
            theta = DEG2RAD*gridXCoord[p]
            phi = DEG2RAD*(90.0 - gridYCoord[p])
            fieldPtr[p] = 2.0 + np.cos(theta)**2 * np.cos(2.0*phi)
            p = p + 1

    '''
    theta = np.array(DEG2RAD*gridXCoord[:])
    phi = np.array(DEG2RAD*(90. - gridYCoord[:]))
    fieldPtr[:] = 2. + np.cos(theta[:])**2 * np.cos(2.*phi[:])
    '''
    return field


def compute_mass(valuefield, areafield, fracfield, dofrac):
    '''
    PRECONDITIONS: Two ESMP_Fields have been created and initialized.  'valuefield'
                   contains data values of a field built on the cells of a grid, 
                   'areafield' contains the areas associated with the grid 
                   cells, and 'fracfield' contains the fractions of each cell
                   which contributed to a regridding operation involving
                   'valuefield.  'dofrac' is a boolean value that gives the
                   option to not use the 'fracfield'.\n
    POSTCONDITIONS: The mass of the data field is computed and returned.\n
    RETURN VALUES: integer :: mass \n
    '''

    mass = 0.0
    ESMP.ESMP_FieldRegridGetArea(areafield)
    area = ESMP.ESMP_FieldGetPtr(areafield)
    value = ESMP.ESMP_FieldGetPtr(valuefield)
    frac = 0
    if dofrac:
        frac = ESMP.ESMP_FieldGetPtr(fracfield)

    for i in range(valuefield.size):
        if dofrac:
            mass += area[i]*value[i]*frac[i]
        else:
            mass += area[i]*value[i]

    return (mass, area)


def compare_fields(interp_field, exact_field, dstfracfield, srcmass, dstmass):
    '''
    PRECONDITIONS: 'interp_field' is a Field that holds the values resulting
                  from a regridding operation, 'exact_field' is a Field
                  containing the values of the exact solution that is 
                  expected, and 'dstfracfield' is a Field containing the
                  fractions of the 'interp_field' which contributed to the
                  regridding product.  'srcmass' and 'dstmass' are the 
                  mass values for the source and destination data fields. \n
    POSTCONDITIONS: The interpolation accuracy of a regridding operation is
                  determined by comparing the 'interp_field' to the 
                  'exact_field'.  The mass conservation is validated by
                  comparing the 'srcmass' to the 'dstmass'.\n
    RETURN VALUES: None \n
    '''

    vm = ESMP.ESMP_VMGetGlobal()
    localPet, _ = ESMP.ESMP_VMGet(vm)

    # get the data pointers for the fields
    interp = ESMP.ESMP_FieldGetPtr(interp_field)
    exact = ESMP.ESMP_FieldGetPtr(exact_field)
    dstfrac = ESMP.ESMP_FieldGetPtr(dstfracfield)

    if (interp_field.size != exact_field.size):
        raise TypeError('compare_fields: Fields must be the same size!')

    # initialize to True, and check for False point values
    total_error = 0.0
    max_error = 0.0
    min_error = 1000000.0
    for i in range(interp_field.size):
        if (exact[i] != 0.0):
            err = abs(interp[i]/dstfrac[i] - exact[i])/abs(exact[i])
        else:
            err = abs(interp[i]/dstfrac[i] - exact[i])
        total_error = total_error + err

        if (err > max_error): 
            max_error = err
        if (err < min_error): 
            min_error = err

    # check the mass
    csrv = False
    csrv_error = abs(dstmass - srcmass)/srcmass
    if (csrv_error < 10e-12):
       csrv = True
    itrp = False
    if (max_error < 10E-2):
        itrp = True

    if (itrp and csrv):
        print "PASS"
    else:
        print "FAIL"
    print "       Total error = "+str(total_error)
    print "       Max error   = "+str(max_error)
    print "       Min error   = "+str(min_error)
    print "       Csrv error  = "+str(csrv_error)
    print "       srcmass     = "+str(srcmass)
    print "       dstmass     = "+str(dstmass)
  
    return

def run_regridding(srcfield, dstfield, srcfracfield, dstfracfield):
    '''
    PRECONDITIONS: Two ESMP_Fields have been created and a regridding operation 
                   is desired from 'srcfield' to 'dstfield'.  The 'srcfracfield'
                   and 'dstfractfield' are Fields created to hold
                   the fractions of the source and destination fields which 
                   contribute to the regridding operation.\n
    POSTCONDITIONS: An ESMP regridding operation has set the data on 'dstfield', 
                    'srcfracfield', and 'dstfracfield'.\n
    RETURN VALUES: \n ESMP_Field :: dstfield \n ESMP_Field :: srcfracfield \n
                   ESMP_Field :: dstfracfield \n
    '''
    # call the regridding functions
    routehandle = ESMP.ESMP_FieldRegridStore(srcfield, dstfield,
                                             srcMaskValues=np.array([1], dtype=np.int32),
                                             dstMaskValues=np.array([1], dtype=np.int32),
                                             regridmethod=ESMP.ESMP_REGRIDMETHOD_CONSERVE,
                                             unmappedaction=ESMP.ESMP_UNMAPPEDACTION_ERROR,
                                             srcFracField=srcfracfield, 
                                             dstFracField=dstfracfield)
    ESMP.ESMP_FieldRegrid(srcfield, dstfield, routehandle)
    ESMP.ESMP_FieldRegridRelease(routehandle)

    return dstfield, srcfracfield, dstfracfield

def make_grid(field_def, mask=None):
    """
    Define a grid

    Use the cice grid. 
    """

    f, lon_name, lat_name, clon_name, clat_name = field_def

    lons = np.copy(f.variables[lon_name])
    lons = np.rad2deg(lons)
    lats = np.copy(f.variables[lat_name])
    lats = np.rad2deg(lats)

    clons = np.copy(f.variables[clon_name])
    clons = np.rad2deg(clons)
    clats = np.copy(f.variables[clat_name])
    clats = np.rad2deg(clats)

    # Create a grid with 1 periodic dimension.
    grid = ESMP.ESMP_GridCreate1PeriDim(np.array((lons.shape[1], lons.shape[0]), dtype=np.int32))

    # Add centres to grid.
    ESMP.ESMP_GridAddCoord(grid, staggerloc=ESMP.ESMP_STAGGERLOC_CENTER)
    lb_center, ub_center = ESMP.ESMP_GridGetCoord(grid, ESMP.ESMP_STAGGERLOC_CENTER)

    [x, y] = [0, 1]
    x_center = ESMP.ESMP_GridGetCoordPtr(grid, x, ESMP.ESMP_STAGGERLOC_CENTER)
    y_center = ESMP.ESMP_GridGetCoordPtr(grid, y, ESMP.ESMP_STAGGERLOC_CENTER)
    x_center[:] = lons.flatten()
    y_center[:] = lats.flatten()

    # Add corners to grid. 
    ESMP.ESMP_GridAddCoord(grid, staggerloc=ESMP.ESMP_STAGGERLOC_CORNER)
    lb_corner, ub_corner = ESMP.ESMP_GridGetCoord(grid, ESMP.ESMP_STAGGERLOC_CORNER)
    nx, ny = ub_corner[:] - lb_corner[:]

    x_corner = ESMP.ESMP_GridGetCoordPtr(grid, x, ESMP.ESMP_STAGGERLOC_CORNER)
    x_corner[:] = np.NAN
    x_corner = x_corner.reshape(ny, nx)
    y_corner = ESMP.ESMP_GridGetCoordPtr(grid, y, ESMP.ESMP_STAGGERLOC_CORNER)
    y_corner[:] = np.NAN
    y_corner = y_corner.reshape(ny, nx)

    # Need to copy over the corners which are shape (4, 300, 360) to flat a (301, 360) 
    # array (for example). This is done by copying over all the corner 0 coordinates,
    # then fixing up the top row. 

    x_corner[:ny-1,:] = clons[0,:,:] 
    y_corner[:ny-1,:] = clats[0,:,:]

    assert (np.isnan(np.sum(x_corner)) and np.isnan(np.sum(y_corner)))

    x_corner[ny-1:,:] = clons[3,-1,:]
    y_corner[ny-1:,:] = clats[3,-1,:]

    x_corner = x_corner.reshape(ny*nx)
    y_corner = y_corner.reshape(ny*nx)

    x_corner = (x_corner + 360.) % 360.

    # Check that there are no NANs left.
    assert not (np.isnan(np.sum(x_corner)) or np.isnan(np.sum(y_corner)))

    if mask is not None:
       print 'Using mask'
       ESMP.ESMP_GridAddItem(grid, item=ESMP.ESMP_GRIDITEM_MASK)
       m = ESMP.ESMP_GridGetItem(grid, item=ESMP.ESMP_GRIDITEM_MASK)
       mask = mask.reshape(m.shape[0])
       m[mask == True] = 1
       m[mask == False] = 0
       import pdb
       pdb.set_trace()

    return grid

def setup_grid_and_fields(src_def, dest_def, src_mask=None, dest_mask=None):

    ESMP.ESMP_Initialize()
    ESMP.ESMP_LogSet(True)

    # Create source and destination grids.
    src_grid = make_grid(src_def, src_mask)
    dest_grid = make_grid(dest_def, dest_mask)

    # Fields to regrid
    src_field = ESMP.ESMP_FieldCreateGrid(src_grid, 'src_field')
    dest_field = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_field')

    # Area and fraction fields.
    src_frac = ESMP.ESMP_FieldCreateGrid(src_grid, 'src_frac')
    dest_frac = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_frac')

    dest_area = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_area')
    src_area = ESMP.ESMP_FieldCreateGrid(src_grid, 'src_area')

    return (src_grid, dest_grid, src_field, dest_field, src_frac, dest_frac, src_area, dest_area)

def test_regrid():
    """
    Check the OASIS grids by regridding and analytic function and comparing to the expected result.

    This does not pass, although close. Need to experiment with some different grid setups to see 
    what's going on. Leave this for now.
    """
    src_grid, dest_grid, src_field, dest_field, src_frac, dest_frac, src_area, dest_area = setup_grid_and_fields()

    dest_exact = ESMP.ESMP_FieldCreateGrid(dest_grid, 'dest_exact')

    # Intialise analytic test field.
    src_field = build_analytic_field(src_field, src_grid, False)
    dest_exact = build_analytic_field(dest_exact, dest_grid, False)

    # Do the regridding 
    dest_field, src_frac, dest_frac = run_regridding(src_field, dest_field, src_frac, dest_frac)

    # Compute mass
    src_mass, _ = compute_mass(src_field, src_area, src_frac, True)
    dest_mass, _ = compute_mass(dest_field, dest_area, 0, False)

    compare_fields(dest_field, dest_exact, dest_frac, src_mass, dest_mass)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("src_grid", help="A Python tuple describing the source grid. \
                         The tuple is: filename, longitude field, latitude field, corner longitudes field , \
                         corner latitudes field.\"")
    parser.add_argument("dest_grid", help="A Python tuple describing the destination grid. \
                         It has the same format as the source grid argument.")
    parser.add_argument("field", help="A field tuples describing the field to regrid. \
                         The tuple is: source filename, field name, destination filename. E.g. \
                         %s \"('grid.nc', 'lons', 'lats', 'clons', 'clats')\" \
                         \"('grid.new.nc', 'lons', 'lats', 'clons', 'clats')\" \
                         \"('core_runoff.nc', 'runoff', 'core_runoff.new.nc')\". \
                         If the destination file does not exist it will be created. \
                         Don't forget the double and single quotes." % sys.argv[0])
    parser.add_argument("--src_mask_file", help="Specify a mask for the src field. If this is not given but \
                                                 the src field has missing values, then those will be used  \
                                                 as a mask.")
    parser.add_argument("--src_mask_var", help="The source mask variable name.")
    parser.add_argument("--flip_src_mask", action='store_true', help="Invert the source mask. Program expectes 1 or True to represent masked.")
    parser.add_argument("--dest_mask_file", help="Specify a mask for the dest field.")
    parser.add_argument("--dest_mask_var", help="The dest mask variable name.")
    parser.add_argument("--flip_dest_mask", action='store_true', help="Invert the dest mask. Program expectes 1 or True to represent masked.")

    args = parser.parse_args()

    # Open src and dest grid files provided on the command line.
    args_src_grid = list(ast.literal_eval(args.src_grid))
    args_dest_grid = list(ast.literal_eval(args.dest_grid))
    src_grid_filename, src_lons, _, _, _ = args_src_grid
    dest_grid_filename, dest_lons, _, _, _ = args_dest_grid

    src_grid_file = nc.Dataset(src_grid_filename, 'r')
    dest_grid_file = nc.Dataset(dest_grid_filename, 'r')

    args_src_grid[0] = src_grid_file
    args_dest_grid[0] = dest_grid_file

    src_file, field_name, dest_file = ast.literal_eval(args.field)
    src_file = nc.Dataset(src_file, 'r')
    src_field_tmp = np.copy(src_file.variables[field_name])

    src_mask = None
    dest_mask = None
    # Check whether the field has missing values, in which case a src mask is needed.
    if hasattr(src_file.variables[field_name], 'missing_value'):
        assert(args.src_mask_file is None and args.src_mask_var is None)
        src_mask = np.ma.getmask(src_file.variables[field_name][:])
        src_mask = src_mask[0,:,:]

        # FIXME: HACK to get a particular field regridded. Put 0 everywhere where there's a missing value.
        src_mask = None
        src_field_tmp[src_field_tmp == src_file.variables[field_name].missing_value] = 0.0

    if args.src_mask_file:
        # If no missing values, then use --src_mask_var
        assert(args.src_mask_var is not None)

        with nc.Dataset(args.src_mask_file) as f:
            src_mask = f.variables[args.src_mask_var][:]
            # In case src_mask is ints or reals, convert to proper masked array. 
            src_mask = np.ma.make_mask(src_mask)

    else:
        sys.stdout.write("INFO: no mask present, regridding without mask.\n")
        # If neither of the above, then give a message/warning but proceed anyway. 

    if src_mask is not None:
        if (args.dest_mask_file is None) or (args.dest_mask_var is None):
            sys.stderr.write("Source field has mask, a dest mask and var must be provided.\n") 
            return 1

        with nc.Dataset(args.dest_mask_file) as f:
            dest_mask = f.variables[args.dest_mask_var][:]
            # In case src_mask is ints or reals, convert to proper masked array. 
            dest_mask = np.ma.make_mask(dest_mask)

    if args.flip_src_mask:
        assert(src_mask is not None)
        src_mask = ~src_mask

    if args.flip_dest_mask:
        assert(dest_mask is not None)
        dest_mask = ~dest_mask

    # Create the destination file.
    if os.path.exists(dest_file):
        dest_file = nc.Dataset(dest_file, 'r+')
    else:
        dest_file = nc.Dataset(dest_file, 'w')
    dest_shape = dest_grid_file.variables[dest_lons].shape

    if not dest_file.dimensions.has_key('nx'):
        dest_file.createDimension('nx', dest_shape[1])
        dest_file.createDimension('ny', dest_shape[0])
        dest_file.createDimension('time', src_file.variables['time'].shape[0])
    if not dest_file.variables.has_key(field_name):
        dest_file.createVariable(field_name, 'f8', ('time', 'ny', 'nx'))

    # Open up the source and destination grids and do setup. 
    # _cl suffic is for 'clean', i.e. not modified since initialisation.
    src_grid_cl, dest_grid_cl, src_field_cl, dest_field_cl, src_frac_cl, dest_frac_cl, src_area_cl, dest_area_cl = setup_grid_and_fields(args_src_grid, args_dest_grid, src_mask, dest_mask)

    # Iterate over all time points and perform regridding.
    assert(len(src_field_tmp.shape) == 3)
    for t in range(src_field_tmp.shape[0]):
        print 'Regridding at timestep %s' % t

        # Load the field to be regridded.
        src_field_ptr = ESMP.ESMP_FieldGetPtr(src_field_cl) 

        src_field_ptr[:] = ((src_field_tmp[t,:,:]).reshape(src_field_cl.size))[:]
        dest_field, src_frac, dest_frac = run_regridding(src_field_cl, dest_field_cl, src_frac_cl, dest_frac_cl)

        # Write out field to desination field.
        dest_field_ptr = ESMP.ESMP_FieldGetPtr(dest_field)
        dest_field_ptr = dest_field_ptr.reshape(dest_shape)

        dest_file.variables[field_name][t,:,:] = dest_field_ptr[:,:] 

        # Check some results. 
        src_mass, src_area = compute_mass(src_field_cl, src_area_cl, src_frac_cl, True)
        dest_mass, dest_area = compute_mass(dest_field, dest_area_cl, 0, False)
        np.testing.assert_approx_equal(src_mass, dest_mass)

    # clean up
    ESMP.ESMP_FieldDestroy(src_field_cl)
    ESMP.ESMP_FieldDestroy(dest_field_cl)
    ESMP.ESMP_FieldDestroy(src_frac_cl)
    ESMP.ESMP_FieldDestroy(dest_frac_cl)
    ESMP.ESMP_FieldDestroy(src_area_cl)
    ESMP.ESMP_FieldDestroy(dest_area_cl)
    ESMP.ESMP_GridDestroy(src_grid_cl)
    ESMP.ESMP_GridDestroy(dest_grid_cl)
    ESMP.ESMP_Finalize()

    src_file.close()
    dest_file.close()
    src_grid_file.close()
    dest_grid_file.close()


if __name__ == "__main__":
    sys.exit(main())
