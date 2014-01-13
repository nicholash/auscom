#!/bin/ksh

#PBS -P v45
#PBS -W group_list=v45
#PBS -q normal
#PBS -l walltime=05:00:00
#PBS -l mem=2000Gb
#PBS -l ncpus=1168
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

rm -rf $icerundir/INPUT $ocnrundir/INPUT $atmrundir/INPUT

mkdir -p $icerundir/RESTART $icerundir/HISTORY $icerundir/INPUT	#subdirs for CICE
mkdir -p $ocnrundir/RESTART $ocnrundir/HISTORY $ocnrundir/INPUT	#subdirs for MOM4
mkdir -p $atmrundir/RESTART $atmrundir/HISTORY $atmrundir/INPUT	#subdirs for MOM4

# Copy in input files and change mode. These will be overwritten at the end of the run.
cp $inputdir/matm/* $atmrundir/INPUT/
cp $inputdir/mom5/* $ocnrundir/INPUT/
cp $inputdir/cice/* $icerundir/INPUT/

chmod +w $atmrundir/INPUT/*.nc
chmod +w $ocnrundir/INPUT/*.nc
chmod +w $icerundir/INPUT/*.nc

#############################################################################
#
# Run the AusCOM model
#
#############################################################################

module load openmpi/1.6.5-mlx
module load ipm

mpirun -wdir $atmrundir -n 1 $atmrundir/matmxx : -wdir $icerundir -n 192 $icerundir/cicexx : -wdir $ocnrundir -n 960 $ocnrundir/mom5xx

echo
echo "*** job completed  at: " `date` "***" 
echo
echo "`date` :  ${jobnum} ${enddate} - done mpirun/mpiexec!" >> $expdir/${expid}.log
echo 'Error code at end of simulation :'$?

exit
