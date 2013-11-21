#!/bin/ksh

#PBS -P v45
#PBS -W group_list=v45
#PBS -q normal
#PBS -l walltime=05:00:00
#PBS -l mem=2000Gb
#PBS -l ncpus=1024
#PBS -l wd
#PBS -N cnyf.mom5-0.25

set -e
set -xv
ulimit -s unlimited

#############################################################################
#
# Setup variables
#
#############################################################################

expid=cnyf2.mom5-0.25 # change expid for each new experiment

# Location where jobs are submitted (and this script is located):
cd `pwd`/../..
AusCOMHOME=`pwd`
expdir=$AusCOMHOME/exp/$expid
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

# Copy in OASIS restart files and change mode. These will be overwritten at the end of the run.
cp $inputdir/oasis3/* $atmrundir/
cp $inputdir/oasis3/* $ocnrundir/
cp $inputdir/oasis3/* $icerundir/

chmod +w $atmrundir/*.nc
chmod +w $ocnrundir/*.nc
chmod +w $icerundir/*.nc

#############################################################################
#
# Run the AusCOM model
#
#############################################################################

module load openmpi/1.6.5-mlx
module load ipm
export IPM_LOGDIR=$expdir/ipm_logs

mpirun --mca orte_base_help_aggregate 0 -wd $atmrundir -n 1 $atmrundir/matmxx : -wd $icerundir -n 48 $icerundir/cicexx : -wd $ocnrundir -n 960 $ocnrundir/mom5xx

echo
echo "*** job completed  at: " `date` "***" 
echo
echo "`date` :  ${jobnum} ${enddate} - done mpirun/mpiexec!" >> $expdir/${expid}.log
echo 'Error code at end of simulation :'$?

exit
