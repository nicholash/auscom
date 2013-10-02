#!/bin/ksh

#PBS -P v45
#PBS -W group_list=v45
#PBS -q normal
#PBS -l walltime=4:00:00
#PBS -l mem=255Gb
#PBS -l ncpus=128
#PBS -l wd
#PBS -N cnyf2-sw1

date
set -e
set -xv
ulimit -s unlimited

#############################################################################
#
# 1. Primary Setups
#
#############################################################################
#
## 1.1 Define experiment ID etc.
#
jobid=$PBS_JOBID    # job-id assigned by PBS (the queue sys)
job=$PBS_JOBNAME	# name of this script

mom_version=mom5
expid=cnyf2.mom5-0.25 # change expid for each new experiment
year_data_end=2007	# data NOT available after this year

#
## 1.2 Define all associated paths
#

# Location where jobs are submitted (and this script is located):
cd `pwd`/../..
AusCOMHOME=`pwd`
expdir=$AusCOMHOME/exp/$expid

# Location of preprocessed input files for the coupled model:
inputdir=/short/v45/auscom/$expid

# Location where the model exectuables are stored:
bindir=$AusCOMHOME/bin

ocnrundir=$expdir/OCN_RUNDIR
atmrundir=$expdir/ATM_RUNDIR
icerundir=$expdir/ICE_RUNDIR
cplrundir=$expdir/CPL_RUNDIR

#############################################################################
#
# 2. Getting All Files into the correct places
#
#############################################################################

mkdir -p $ocnrundir
mkdir -p $atmrundir
mkdir -p $icerundir
mkdir -p $cplrundir

cp $bindir/fms_MOM_ACCESS.x $ocnrundir/mom5xx
cp $bindir/matm_MPI1_nt62.exe $atmrundir/matmxx
cp $bindir/cice_MPI1_6p.exe $icerundir/cicexx

# Individual RUNDIRS
mkdir -p $icerundir/RESTART -p $icerundir/HISTORY 	#subdirs for CICE
mkdir -p $ocnrundir/RESTART $ocnrundir/HISTORY	#subdirs for MOM4

# get input files for oasis3:

# a. ref and grids data
ln -snf $inputdir/oasis3 $cplrundir/INPUT

# input files for cice:
ln -snf $inputdir/cice $icerundir/INPUT

# get input files for mom4:
ln -snf $inputdir/mom5 $ocnrundir/INPUT

# prepare the atm_forcing dataset needed for this run:
ln -snf $inputdir/matm $atmrundir/INPUT

#############################################################################
#
# 4. Launch/Execute the AusCOM Coupled Model on VAYU
#
#############################################################################

#mpirun --mca mpi_paffinity_alone 1 -wd $icerundir -n 6 $icerundir/cicexx : -wd $atmrundir -n 1 $atmrundir/matmxx : -wd $ocnrundir -n 120 $ocnrundir/mom5xx 
mpirun --mca mpi_paffinity_alone 1 -wd $icerundir -n 1 $icerundir/cicexx : -wd $atmrundir -n 1 $atmrundir/matmxx : -wd $ocnrundir -n 4 $ocnrundir/mom5xx 

echo
echo "*** job completed  at: " `date` "***" 
echo
echo "`date` :  ${jobnum} ${enddate} - done mpirun/mpiexec!" >> $expdir/${expid}.log
echo 'Error code at end of simulation :'$?

exit
