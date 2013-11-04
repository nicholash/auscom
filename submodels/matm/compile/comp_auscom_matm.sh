#! /bin/csh -f

### Change these to your own site and user directory! 
### You will need to create a Makefile Macro in bld/ 

# Set AusCOM home:
setenv AusCOMHOME $cwd:h:h:h

### Platform and its architecture ($HOST = d2 or tx701 (mawson) )
# setenv SITE ${HOST}.nci.org.au
setenv SITE nci.org.au
setenv ARCH `uname -s`
setenv ARCH $ARCH.$SITE
echo ARCH: $ARCH

setenv OASIS3_MCT yes	# oasis3-mct version
setenv CHAN 	  MPI1	#MPI1 or MPI2 (always MPI1!)

# Users must ensure the correct environment file exists for their platform.
set platform = nci.org.au

source /etc/profile.d/nf_csh_modules
module purge
module load intel-cc
module load intel-fc
module load netcdf
module load openmpi/1.6.5-mlx

#endif
#-------------------------------------------------------------------------------
 
### Location of AusCOM system
setenv SYSTEMDIR $AusCOMHOME
echo SYSTEMDIR: $SYSTEMDIR

### Location of this data ocean model (source)
setenv SRCDIR $cwd:h  #$SYSTEMDIR/submodels/matm
echo SRCDIR: $SRCDIR

### Location and names of coupling libraries
setenv CPLLIBDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/lib
setenv CPLLIBS '-L$(CPLLIBDIR) -lpsmile.${CHAN} -lmct -lmpeu -lscrip'
#echo CPLLIBS: ${CPLLIBS}

### Location of coupling inclusions
setenv CPLINCDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/build/lib
setenv CPL_INCS '-I$(CPLINCDIR)/psmile.$(CHAN) -I$(CPLINCDIR)/pio -I$(CPLINCDIR)/mct'
#echo CPL_INCS: $CPL_INCS


### Grid resolution
setenv GRID nt62
setenv RES 192x94

### Location and name of the generated exectuable 
setenv BINDIR $AusCOMHOME/bin
setenv EXE matm_${CHAN}_${GRID}.exe

### Where this model is compiled
setenv OBJDIR $SRCDIR/compile/build_MPI1_${GRID}
if !(-d $OBJDIR) mkdir -p $OBJDIR


set NXGLOB = `echo $RES | sed s/x.\*//`
set NYGLOB = `echo $RES | sed s/.\*x//`
echo NXGLOB: $NXGLOB, NYGLOB: $NYGLOB

setenv CBLD $SRCDIR/bld
echo CBLD: $CBLD

cp -f $CBLD/Makefile.std $CBLD/Makefile

cd $OBJDIR

### List of source code directories (in order of importance).
cat >! Filepath << EOF
$SRCDIR/source
EOF

cc -o makdep $CBLD/makdep.c                      || exit 2

gmake VPFILE=Filepath EXEC=$BINDIR/$EXE \
           NXGLOB=$NXGLOB NYGLOB=$NYGLOB \
      -f  $CBLD/Makefile MACFILE=$CBLD/Macros.$ARCH || exit 2

cd ..

echo "x    $NXGLOB"
echo "y    $NYGLOB"

