#! /bin/csh -f

set echo on

if ( $#argv != 2 ) then
  echo '*** Please issue the command like ***'
  echo '     > ./comp_auscom_cice.sh <platform> <driver>' 
  echo 'e.g. comp_auscom_cice.sh nci access'
  exit
else
  set platform = $1
  set driver = $2
endif

# Set AusCOM home:
setenv AusCOMHOME $cwd:h:h:h

# Location of this model (source)
setenv SRCDIR $cwd:h
setenv CBLD   $SRCDIR/bld
                                                                                
source $CBLD/config.$platform

### Specialty code
setenv USE_ESMF no        # set to yes for ESMF runs
setenv CAM_ICE  no        # set to yes for CAM runs (single column)
setenv SHRDIR   csm_share # location of CCSM shared code
setenv NETCDF   yes       # set to no if netcdf library is unavailable
setenv DITTO    no        # reproducible diagnostics
setenv ACCESS   yes       # set to yes for ACCESS
setenv AusCOM   yes       # set to yes for AusCOM
setenv OASIS3_MCT yes	  # oasis3-mct version
setenv CHAN     MPI1	  # MPI1 or MPI2 (always MPI1!)
 
### Location of ACCESS system
setenv SYSTEMDIR $AusCOMHOME
echo SYSTEMDIR: $SYSTEMDIR

### Location and names of coupling libraries and inclusions
if ( $AusCOM == 'yes' ) then
    # Location and names of coupling libraries
    setenv CPLLIBDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/lib
    setenv CPLLIBS '-L$(CPLLIBDIR) -lpsmile.${CHAN} -lmct -lmpeu -lscrip'
    setenv CPLINCDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/build/lib
    setenv CPL_INCS '-I$(CPLINCDIR)/psmile.$(CHAN) -I$(CPLINCDIR)/pio -I$(CPLINCDIR)/mct'

    setenv LIBAUSCOM_INCS '-I$(SYSTEMDIR)/submodels/libauscom'
    setenv LIBAUSCOM_LIBS '-L$(SYSTEMDIR)/submodels/libauscom -lauscom'
endif
 
### Location and name of the generated exectuable
setenv BINDIR $SYSTEMDIR/bin
setenv EXE cice_${CHAN}_${NTASK}p.exe

### Where this model is compiled
setenv OBJDIR $SRCDIR/compile/build_${CHAN}_{$NTASK}p
if !(-d $OBJDIR) mkdir -p $OBJDIR
 
### Grid resolution
setenv GRID tp1

### For multi-Layer ice (standard) configuration
set N_ILYR = 4

# Recommendations:
#   use processor_shape = slenderX1 or slenderX2 in ice_in
#   one per processor with distribution_type='cartesian' or
#   squarish blocks with distribution_type='rake'
# If BLCKX (BLCKY) does not divide NXGLOB (NYGLOB) evenly, padding
# will be used on the right (top) of the grid.

@ a = $NXGLOB * $NYGLOB ; @ b = $BLCKX * $BLCKY * $NTASK
@ m = $a / $b ; setenv MXBLCKS $m ; if ($MXBLCKS == 0) setenv MXBLCKS 1
echo Autimatically generated: MXBLCKS = $MXBLCKS
                                                                                
cp -f $CBLD/Makefile.std $CBLD/Makefile

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
                                                                                
if ($driver == 'auscom') then
  setenv DRVDIR auscom
else
  setenv DRVDIR access
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
                                                                                
cc -o makdep $CBLD/makdep.c || exit 2

make VPFILE=Filepath EXEC=$BINDIR/$EXE \
           NXGLOB=$NXGLOB NYGLOB=$NYGLOB \
           N_ILYR=$N_ILYR \
           BLCKX=$BLCKX BLCKY=$BLCKY MXBLCKS=$MXBLCKS \
      -j 8 -f  $CBLD/Makefile MACFILE=$CBLD/Macros.$platform || exit 2
                                                                                
cd ..
pwd
echo NTASK = $NTASK
echo "global N, block_size"
echo "x    $NXGLOB,    $BLCKX"
echo "y    $NYGLOB,    $BLCKY"
echo max_blocks = $MXBLCKS

