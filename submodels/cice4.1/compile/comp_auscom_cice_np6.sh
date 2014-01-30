#! /bin/csh -f

set echo on

if ( $1 == '') then
  echo '*** Please issue the command like ***'
  echo '     > ./comp_auscom_cice.VAYU.nP #nproc    ' 
  echo 'here #proc is the number of cpu to be used for CICE4 (e.g. 1, 2, 4, 6...)'
else
  set nproc = $1
  echo *** $nproc processors will be used to run CICE4... ***
endif

### Change these to your own site and user directory! 
### You will need to create a Makefile Macro in bld
### Platform and its architecture ($HOST = xe)
setenv SITE nci.org.au
setenv ARCH `uname -s`
setenv ARCH nci.org.au

# Set AusCOM home:
setenv AusCOMHOME $cwd:h:h:h

set platform = $SITE

source /etc/profile.d/nf_csh_modules
module purge
module load intel-cc
module load intel-fc
module load netcdf
module load openmpi/1.6.5-mlx

#----------------------------------------------------------------------

### Specialty code
setenv USE_ESMF no        # set to yes for ESMF runs
setenv CAM_ICE  no        # set to yes for CAM runs (single column)
setenv SHRDIR   csm_share # location of CCSM shared code
setenv NETCDF   yes       # set to no if netcdf library is unavailable
setenv DITTO    no        # reproducible diagnostics
setenv AusCOM   yes       # set to yes for AusCOM
setenv OASIS3_MCT yes	  # oasis3-mct version
setenv CHAN     MPI1	  # MPI1 or MPI2 (always MPI1!)
 
### Location of ACCESS system
setenv SYSTEMDIR $AusCOMHOME
echo SYSTEMDIR: $SYSTEMDIR

### Location of this model (source)
setenv SRCDIR $cwd:h
echo SRCDIR: $SRCDIR
 
### Location and names of coupling libraries and inclusions
if ( $AusCOM == 'yes' ) then
    # Location and names of coupling libraries
    setenv CPLLIBDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/lib
    setenv CPLLIBS '-L$(CPLLIBDIR) -lpsmile.${CHAN} -lmct -lmpeu -lscrip'
    setenv CPLINCDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/build/lib
    setenv CPL_INCS '-I$(CPLINCDIR)/psmile.$(CHAN) -I$(CPLINCDIR)/pio -I$(CPLINCDIR)/mct'

    setenv MYFLIB_INCS '-I$(SYSTEMDIR)/submodels/myflib'
    setenv MYFLIB_LIBS '-L$(SYSTEMDIR)/submodels/myflib -lmyflib'
endif
 
### Location and name of the generated exectuable
setenv BINDIR $SYSTEMDIR/bin
setenv EXE cice_${CHAN}_${nproc}p.exe

### Where this model is compiled
setenv OBJDIR $SRCDIR/compile/build_${CHAN}_{$nproc}p
if !(-d $OBJDIR) mkdir -p $OBJDIR
 
### Grid resolution
#setenv GRID gx3 ; setenv RES 100x116
#setenv GRID gx1 ; setenv RES 320x384
#setenv GRID tx1 ; setenv RES 360x240
#setenv GRID tp1 ; setenv RES 1440x1080
setenv GRID tp1 ; setenv RES 360x300
                                                                                
set NXGLOB = `echo $RES | sed s/x.\*//`
set NYGLOB = `echo $RES | sed s/.\*x//`
echo NXGLOB: $NXGLOB
echo NYGLOB: $NYGLOB

### For multi-Layer ice (standard) configuration
set N_ILYR = 4

# Recommendations:
#   NTASK equals nprocs in ice_in
#   use processor_shape = slenderX1 or slenderX2 in ice_in
#   one per processor with distribution_type='cartesian' or
#   squarish blocks with distribution_type='rake'
# If BLCKX (BLCKY) does not divide NXGLOB (NYGLOB) evenly, padding
# will be used on the right (top) of the grid.
#setenv NTASK      4       # total number of processors
#setenv BLCKX     25       # x-dimension of blocks ( not including )
#setenv BLCKY     29       # y-dimension of blocks (  ghost cells  )
setenv NTASK      $nproc
setenv BLCKX      `expr $NXGLOB / 6`       # x-dimension of blocks ( not including )
echo BLCKX: $BLCKX
setenv BLCKY      `expr $NYGLOB / 1`        # y-dimension of blocks (  ghost cells  )
echo BLCKY: $BLCKY

# may need to increase MXBLCKS with rake distribution or padding
@ a = $NXGLOB * $NYGLOB ; @ b = $BLCKX * $BLCKY * $NTASK
@ m = $a / $b ; setenv MXBLCKS $m ; if ($MXBLCKS == 0) setenv MXBLCKS 1
echo Autimatically generated: MXBLCKS = $MXBLCKS
#setenv MXBLCKS 1
                                                                                
setenv CBLD   $SRCDIR/bld
                                                                                
if ( $ARCH == 'UNICOS/mp') setenv ARCH UNICOS
if ( $ARCH == 'UNICOS') then
   cp -f $CBLD/Makefile.$ARCH $CBLD/Makefile
else
   cp -f $CBLD/Makefile.std $CBLD/Makefile
endif

if ($NTASK == 1) then
   setenv COMMDIR serial
else
   setenv COMMDIR mpi
endif
echo COMMDIR: $COMMDIR
                                                                                
setenv DRVDIR cice4
                                                                                
if ($USE_ESMF == 'yes') then
  setenv DRVDIR esmf
endif
                                                                                
if ($AusCOM == 'yes') then
  setenv DRVDIR auscom
endif
echo DRVDIR: $DRVDIR
                                                                                
cd $OBJDIR
                                                                                
### List of source code directories (in order of importance).
cat >! Filepath << EOF
$SRCDIR/drivers/$DRVDIR
$SRCDIR/source
$SRCDIR/$COMMDIR
$SRCDIR/$SHRDIR
EOF
                                                                                
if ( $ARCH == 'UNICOS.ORNL.phoenix' ) then
   ### use -h command for phoenix
   cc -o makdep -h command $CBLD/makdep.c           || exit 2
else if ( $ARCH == 'Linux.ORNL.jaguar' ) then
   gcc -g -o makdep $CBLD/makdep.c                  || exit 2
else
   cc -o makdep $CBLD/makdep.c                      || exit 2
endif
gmake VPFILE=Filepath EXEC=$BINDIR/$EXE \
           NXGLOB=$NXGLOB NYGLOB=$NYGLOB \
           N_ILYR=$N_ILYR \
           BLCKX=$BLCKX BLCKY=$BLCKY MXBLCKS=$MXBLCKS \
      -j 8 -f  $CBLD/Makefile MACFILE=$CBLD/Macros.Linux.$ARCH || exit 2
                                                                                
cd ..
pwd
echo NTASK = $NTASK
echo "global N, block_size"
echo "x    $NXGLOB,    $BLCKX"
echo "y    $NYGLOB,    $BLCKY"
echo max_blocks = $MXBLCKS

