
#!/bin/csh -f

#PBS -P <project>
#PBS -q <queue>
#PBS -l walltime=<walltime>
#PBS -l ncpus=<ncpus>
#PBS -l mem=<mem>
#PBS -l wd
#PBS -o OCN_RUNDIR/stdout.txt
#PBS -e OCN_RUNDIR/stderr.txt

module load openmpi/1.6.5-mlx
module load ipm

mpirun --mca orte_base_help_aggregate 0 -wdir /home/nfs/z3078140/auscom/exp/cnyf2.mom5.ubuntu/ATM_RUNDIR -n 1 /home/nfs/z3078140/auscom/exp/cnyf2.mom5.ubuntu/matmxx : -wdir /home/nfs/z3078140/auscom/exp/cnyf2.mom5.ubuntu/ICE_RUNDIR -n 1 /home/nfs/z3078140/auscom/exp/cnyf2.mom5.ubuntu/cicexx : -wdir /home/nfs/z3078140/auscom/exp/cnyf2.mom5.ubuntu/OCN_RUNDIR -n 4 /home/nfs/z3078140/auscom/exp/cnyf2.mom5.ubuntu/mom5xx

