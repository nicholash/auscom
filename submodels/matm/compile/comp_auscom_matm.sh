#! /bin/csh -f

if ( $1 == '') then
  echo '*** Please issue the command like ***'
  echo '     > ./comp_auscom_matm.sh <platform>  ' 
else
  set platform = $1
endif

# Set AusCOM home:
setenv AusCOMHOME $cwd:h:h:h

setenv OASIS3_MCT yes	# oasis3-mct version
setenv CHAN 	  MPI1	#MPI1 or MPI2 (always MPI1!)

# Location of this data ocean model (source)
setenv SRCDIR $cwd:h
setenv CBLD $SRCDIR/bld

# Set local setting such as loading modules. 
source $CBLD/environs.$platform

### Location of AusCOM system
setenv SYSTEMDIR $AusCOMHOME
echo SYSTEMDIR: $SYSTEMDIR

### Location and names of coupling libraries
setenv CPLLIBDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/lib
setenv CPLLIBS '-L$(CPLLIBDIR) -lpsmile.${CHAN} -lmct -lmpeu -lscrip'

### Location of coupling inclusions
setenv CPLINCDIR $SYSTEMDIR/submodels/oasis3-mct/Linux/build/lib
setenv CPL_INCS '-I$(CPLINCDIR)/psmile.$(CHAN) -I$(CPLINCDIR)/pio -I$(CPLINCDIR)/mct'

setenv LIBAUSCOM_INCS '-I$(SYSTEMDIR)/submodels/libauscom'
setenv LIBAUSCOM_LIBS '-L$(SYSTEMDIR)/submodels/libauscom -lauscom'

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


cp -f $CBLD/Makefile.std $CBLD/Makefile

cd $OBJDIR

### List of source code directories (in order of importance).
cat >! Filepath << EOF
$SRCDIR/source
EOF

cc -o makdep $CBLD/makdep.c                      || exit 2

make VPFILE=Filepath EXEC=$BINDIR/$EXE \
           NXGLOB=$NXGLOB NYGLOB=$NYGLOB \
      -f  $CBLD/Makefile MACFILE=$CBLD/Macros.$platform || exit 2

cd ..

echo "x    $NXGLOB"
echo "y    $NYGLOB"

