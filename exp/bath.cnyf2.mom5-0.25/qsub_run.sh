
#!/bin/csh -f

#PBS -P x77
#PBS -q normal
#PBS -l walltime=05:00:00
#PBS -l ncpus=1168
#PBS -l mem=2000Gb
#PBS -l wd

module load openmpi/1.6.5-mlx
module load ipm

mpirun --mca mtl ^mxm --mca orte_base_help_aggregate 0 -wdir /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/ATM_RUNDIR -n 1 /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/matmxx : -wdir /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/ICE_RUNDIR -n 192 /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/cicexx : -wdir /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/OCN_RUNDIR -n 960 /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/mom5xx 2> /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/OCN_RUNDIR/stderr.txt 1> /short/v45/nah599/auscom/exp/bath.cnyf2.mom5-0.25/OCN_RUNDIR/stdout.txt

