#!/bin/ksh

#PBS -P x77
#PBS -W group_list=x77
#PBS -q express
#PBS -l walltime=0:30:00
#PBS -l mem=128Gb
#PBS -l ncpus=128
#PBS -l wd
#PBS -N mom5.cnyf2

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

#############################################################################
#
# Run the AusCOM model
#
#############################################################################

module load openmpi
mpirun --mca orte_base_help_aggregate 0 -wd $atmrundir -n 1 $atmrundir/matmxx : -wd $icerundir -n 48 $icerundir/cicexx : -wd $ocnrundir -n 64 $ocnrundir/mom5xx 

echo
echo "*** job completed  at: " `date` "***" 
echo
echo "`date` :  ${jobnum} ${enddate} - done mpirun/mpiexec!" >> $expdir/${expid}.log
echo 'Error code at end of simulation :'$?

exit
