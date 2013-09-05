#!/bin/tcsh
#
# Purpose
# -------
# Compiles OASIS3 at nci.org.au

# Set the name of the platform on which we are working 
setenv PLATFORM nci.org.au
echo ""
echo PLATFORM = $PLATFORM
echo ""

# Set the path to the top-level OASIS directory
setenv COUPLE $cwd:h
echo ""
echo COUPLE = $COUPLE
echo ""

# Set path to AusCOM home
setenv AusCOMHOME $cwd:h:h:h
echo "" 
echo AusCOMHOME = $AusCOMHOME
echo "" 

source /etc/profile.d/nf_csh_modules
module purge
module load intel-cc
module load intel-fc
module load netcdf
module load openmpi
 
#------------------------------------------------------------------
# complie the calendar tool for AusCOM run time use by runscript
#ifort -o $AusCOMHOME/bin/calendar.exe $AusCOMHOME/bin/calendar.F90

# Compile OASIS3
echo ""
echo Compiling OASIS3 ...
echo ""
cd  $COUPLE/util/make_dir
make realclean -f TopMakefileOasis3
make oasis3_psmile -j4 -f TopMakefileOasis3

