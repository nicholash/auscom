#!/bin/ksh

#PBS -P v45
#PBS -W group_list=v45
#PBS -q normal
#PBS -l walltime=3:00:00
#PBS -l mem=255Gb
#PBS -l ncpus=128
#PBS -l wd
#PBS -N cnyf2-sw1

set -e
set -xv
ulimit -s unlimited

#############################################################################
#
# Setup variables
#
#############################################################################

expid=cnyf2.mom5 # change expid for each new experiment

# Location where jobs are submitted (and this script is located):
cd `pwd`/../..
AusCOMHOME=`pwd`
expdir=$AusCOMHOME/exp/$expid

# Location of preprocessed input files for the coupled model:
inputdir=/short/v45/auscom/$expid

ocnrundir=$expdir/OCN_RUNDIR
atmrundir=$expdir/ATM_RUNDIR
icerundir=$expdir/ICE_RUNDIR

#############################################################################
#
# Setup inputs.
#
#############################################################################

mkdir -p $icerundir/RESTART -p $icerundir/HISTORY 	#subdirs for CICE
mkdir -p $ocnrundir/RESTART $ocnrundir/HISTORY	#subdirs for MOM4

ln -snf $inputdir/cice $icerundir/INPUT
ln -snf $inputdir/mom5 $ocnrundir/INPUT
ln -snf $inputdir/matm $atmrundir/INPUT

#############################################################################
#
# Run the AusCOM model
#
#############################################################################

mpirun --mca orte_base_help_aggregate 0 --mca mpi_paffinity_alone 1 -wd $atmrundir -n 1 $atmrundir/matmxx : -wd $icerundir -n 6 $icerundir/cicexx : -wd $ocnrundir -n 120 $ocnrundir/mom5xx 

echo
echo "*** job completed  at: " `date` "***" 
echo
echo "`date` :  ${jobnum} ${enddate} - done mpirun/mpiexec!" >> $expdir/${expid}.log
echo 'Error code at end of simulation :'$?

exit
