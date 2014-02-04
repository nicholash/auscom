#!/usr/bin/env python

import sys
import argparse
import subprocess
import shutil
import os
import time
import glob
import stat
import datetime
import calendar
import copy
import yaml
from fnamelist import FortranNamelist, Namcouple
from operator import xor

run_script = """
#!/bin/csh -f

#PBS -P <project>
#PBS -q <queue>
#PBS -l walltime=<walltime>
#PBS -l ncpus=<ncpus>
#PBS -l mem=<mem>
#PBS -l wd

module load openmpi/1.6.5-mlx
module load ipm

mpirun --mca mtl ^mxm --mca orte_base_help_aggregate 0 -wdir <atm_dir> -n <atm_ncpus> <exp_dir>/matmxx : -wdir <ice_dir> -n <ice_ncpus> <exp_dir>/cicexx : -wdir <ocn_dir> -n <ocn_ncpus> <exp_dir>/mom5xx 2> <ocn_dir>/stderr.txt 1> <ocn_dir>/stdout.txt

"""

configs = ['namcouple', 'input_atm.nml', 'data_4_matm.table', 'cice_in.nml', 'input_ice.nml', 'input_ice_gfdl.nml', 'input_ice_monin.nml', 'input.nml', 'diag_table', 'field_table', 'data_table']

def prepare_newrun(exp_dir, input_dir):
    """
    Anything that needs to be done before the model starts.
    """

    # Delete and remake old INPUT and RESTART dirs, these get polluted. e.g. by oasis writing over the restart files.
    for d, m in [('ATM_RUNDIR', 'matm'), ('ICE_RUNDIR', 'cice'), ('OCN_RUNDIR', 'mom5')]:

        rundir = os.path.join(exp_dir, d)
        if os.path.exists(rundir):
            shutil.rmtree(rundir)

        input = os.path.join(exp_dir, d, 'INPUT')
        restart = os.path.join(exp_dir, d, 'RESTART')
        os.makedirs(input)
        os.makedirs(restart)

        # Copy over inputs and fix perms.
        for f in glob.glob('%s/*' % os.path.join(input_dir, m)):
            shutil.copy(f, input)
            os.chmod(os.path.join(input, os.path.basename(f)), 0664)

        # Copy fresh config files into place. 
        for f in configs:
            shutil.copy(os.path.join(exp_dir, f), os.path.join(exp_dir, d))


def prepare_contrun(exp_dir, init_date=None):
    """
    Anything that needs to be done before a continuation run, apart from setting up the dates.
    
    There are some things that the models should take care of. 
    """

    ice_input = os.path.join(exp_dir, 'ICE_RUNDIR', 'INPUT')
    ice_restart = os.path.join(exp_dir, 'ICE_RUNDIR', 'RESTART')
    ocn_input = os.path.join(exp_dir, 'OCN_RUNDIR', 'INPUT')
    ocn_restart = os.path.join(exp_dir, 'OCN_RUNDIR', 'RESTART')
    atm_input = os.path.join(exp_dir, 'ATM_RUNDIR', 'INPUT')

    # Copy over some CICE files. 
    shutil.copy(os.path.join(exp_dir, 'ICE_RUNDIR', 'u_star.nc'), ice_input)
    shutil.copy(os.path.join(exp_dir, 'ICE_RUNDIR', 'sicemass.nc'), ice_input)

    # Setup the CICE restart. 
    # Check that restart file for this start date exists. 
    if init_date:
        assert(os.path.exists(os.path.join(ice_restart, 'iced.%s' % (init_date))))
        with open(os.path.join(ice_restart, 'ice.restart_file'), 'w') as f:
            f.write('iced.%s' % init_date)

    # Copy over new OASIS restart files. FIXME: I don't think this is necessary, needs checking. 
    # E.g. The atm reads a2i and sends it to the ice, it is not read directly by the ice.
    shutil.copy(os.path.join(ice_input, 'i2o.nc'), ocn_input)
    shutil.copy(os.path.join(ocn_input, 'o2i.nc'), ice_input)
    shutil.copy(os.path.join(atm_input, 'a2i.nc'), ice_input)
    shutil.copy(os.path.join(ice_input, 'i2a.nc'), atm_input)

    # Copy over ocean restarts.
    for f in glob.glob('%s/*' % ocn_restart):
        shutil.copy(f, ocn_input)

    # Copy fresh config files into place. FIXME: This is being done in newrun also.
    for d in ['ATM_RUNDIR', 'ICE_RUNDIR','OCN_RUNDIR']:
        for f in configs:
            shutil.copy(os.path.join(exp_dir, f), os.path.join(exp_dir, d))

def ndays_between_dates(begin_date, end_date):
    """
    Calculate the number of days between two dates according to a 365 calendar with no leap years.

    The dates should always have day 01.
    """

    assert(begin_date.day == 1 and end_date.day == 1)

    def leap_days_between_dates(begin_date, end_date):
        """
        Return the number of leap days between two dates. 

        The easiest way to do this is to just iterate over all days. 
        """

        leaps = 0
        one_day = datetime.timedelta(1)

        curr_date = begin_date
        while curr_date != end_date:
            if curr_date.month == 2 and curr_date.day == 29:
                leaps += 1

            curr_date += one_day
            
        return leaps

    # Do the calculation using timedelta and then subtract the leap days added.
    td = end_date - begin_date
        
    return (td.days - leap_days_between_dates(begin_date, end_date))


def add_months_to_date(date, num_months):
    """
    Add a number of months to a date to get a new one. 
    """

    assert(date.day == 1) 

    new_date = None
    if (12 - date.month) >= num_months:
        new_date = datetime.date(date.year, date.month + num_months, 1)
    else:
        num_months += (date.month - 1)
        years = num_months // 12
        months = num_months % 12
        new_date = datetime.date(date.year + years, months + 1, 1)

    return new_date


def set_next_startdate(exp_dir, init_date, prev_start_date, runtime_per_submit, submit_num, newrun):
    """
    Tell the models when to start by modifying the input namelists.

    runtime_per_submit is in months.
    """

    if prev_start_date is None:
        start_date = init_date
    else:
        prev_end_date = add_months_to_date(prev_start_date, runtime_per_submit)
        start_date = prev_end_date

    end_date = add_months_to_date(start_date, runtime_per_submit)

    assert(init_date.day == 1)
    assert((prev_start_date is None) or prev_start_date.day == 1)
    assert(start_date.day == 1)

    days_since_start = ndays_between_dates(init_date, start_date)
    days_this_run = ndays_between_dates(start_date, end_date)

    # init_date is the start date of the experiment. 
    init_str = str(init_date.year).zfill(4) + str(init_date.month).zfill(2) + str(init_date.day).zfill(2)
    run_str = str(start_date.year).zfill(4) + str(start_date.month).zfill(2) + str(start_date.day).zfill(2)

    # Atmos.
    atm_rundir = os.path.join(exp_dir, 'ATM_RUNDIR')
    nml = FortranNamelist(os.path.join(atm_rundir, 'input_atm.nml'))
    # The start of the experiment.
    nml.set_value('coupling', 'init_date', init_str)
    # The start of the run.
    nml.set_value('coupling', 'inidate', run_str)
    nml.set_value('coupling', 'truntime0', days_since_start*86400)
    nml.set_value('coupling', 'runtime', days_this_run*86400)
    nml.write()

    # Ice
    ice_rundir = os.path.join(exp_dir, 'ICE_RUNDIR')
    nml = FortranNamelist(os.path.join(ice_rundir, 'cice_in.nml'))
    nml.set_value('setup_nml', 'year_init', start_date.year)
    nml.set_value('setup_nml', 'runtype', '\'initial\'') if newrun else nml.set_value('setup_nml', 'runtype', '\'continue\'')
    nml.set_value('setup_nml', 'restart', '.false.') if newrun else nml.set_value('setup_nml', 'restart', '.true.')
    (dt, _, _) = nml.get_value('setup_nml', 'dt')
    assert(days_this_run*86400 % int(dt) == 0)
    nml.set_value('setup_nml', 'npt', (days_this_run*86400) // int(dt))
    nml.write()
    nml = FortranNamelist(os.path.join(ice_rundir, 'input_ice.nml'))
    nml.set_value('coupling_nml', 'init_date', init_str)
    nml.set_value('coupling_nml', 'inidate', run_str)
    nml.set_value('coupling_nml', 'runtime0', days_since_start*86400)
    nml.set_value('coupling_nml', 'runtime', days_this_run*86400)
    nml.set_value('coupling_nml', 'jobnum', submit_num)
    nml.write()

    # Ocean
    ocn_rundir = os.path.join(exp_dir, 'OCN_RUNDIR')
    nml = FortranNamelist(os.path.join(ocn_rundir, 'input.nml'))
    nml.set_value('ocean_solo_nml', 'years', runtime_per_submit // 12)
    nml.set_value('ocean_solo_nml', 'months', runtime_per_submit % 12)
    nml.set_value('ocean_solo_nml', 'days', 0)
    nml.set_value('ocean_solo_nml', 'hours', 0)
    nml.set_value('ocean_solo_nml', 'minutes', 0)
    nml.set_value('ocean_solo_nml', 'seconds', 0)
    # This date_init value is read from RESTART/ocean_solo.res if it exists. 
    nml.set_value('ocean_solo_nml', 'date_init', str(start_date.year).zfill(4) + ',' + str(start_date.month).zfill(2) + ',01,0,0,0')
    nml.write()

    # Oasis namcouple
    for r in [atm_rundir, ice_rundir, ocn_rundir]:
        nc = Namcouple(os.path.join(r, 'namcouple'))
        # FIXME: there is a bug in the models, an extra timestep is made at the end of a month. 
        # This then causes an assertion failure in oasis. For the time being just increase the 
        # oasis max by one day. 
        nc.set_runtime((days_this_run + 1)*86400)
        nc.write()

    return start_date

def clean_up():
    pass


def run(exp_dir, config, run_direct):
    """
    Submit a job, wait for it to finish, check that it completed properly.
    """

    def wait(run_id):

        while True:
            time.sleep(10)
            try: 
                qsub_out = subprocess.check_output(['qstat', run_id])
            except subprocess.CalledProcessError:
                break

            if 'Job has finished' in qsub_out:
                break

    atm_dir = '%s/ATM_RUNDIR' % (exp_dir)
    ice_dir = '%s/ICE_RUNDIR' % (exp_dir)
    ocn_dir = '%s/OCN_RUNDIR' % (exp_dir)

    try:
        os.remove('qsub_run.sh')
    except OSError:
        pass

    # Write script out as a file.
    script = run_script
    for s in ['project', 'queue', 'walltime', 'ncpus', 'mem']:
        if s in config:
            script = script.replace('<' + s + '>', str(config[s]))

    script = script.replace('<atm_dir>', atm_dir)
    script = script.replace('<atm_ncpus>', str(config['atm']['ncpus']))
    script = script.replace('<ice_dir>', ice_dir) 
    script = script.replace('<ice_ncpus>', str(config['ice']['ncpus']))
    script = script.replace('<ocn_dir>', ocn_dir)
    script = script.replace('<ocn_ncpus>', str(config['ocean']['ncpus']))

    script = script.replace('<exp_dir>' , exp_dir)

    qsub_script =  os.path.join(exp_dir, 'qsub_run.sh')
    with open(qsub_script, 'w') as f:
        f.write(script)

    # Submit the experiment
    if run_direct:
        subprocess.call([qsub_script], shell=True)
        run_id = str(time.time())
    else:
        run_id = subprocess.check_output(['qsub', qsub_script])
        run_id = run_id.rstrip()

        print 'Job submitted, runid: %s' % run_id

        # Wait for termination.
        wait(run_id)

    # Read the output file and check that run suceeded.
    output = os.path.join(ocn_dir, 'stdout.txt')
    s = ''
    with open(output, 'r') as f:
        s = f.read()

    return (('End of MATM' in s) and ('End of CICE' in s) and ('MOM4: --- completed ---' in s), output, run_id)

def archive(exp_dir, runid):
    """
    Copy all data associated with the run to an archive directory.
    """

    archive_dir = os.path.join(exp_dir, 'archive', runid)
    os.makedirs(archive_dir)

    for rundir in ['ATM_RUNDIR', 'ICE_RUNDIR', 'OCN_RUNDIR']:
        shutil.copytree(os.path.join(exp_dir, rundir), os.path.join(archive_dir, rundir))

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", help="The experiment to run.")
    parser.add_argument("--submits", dest="submits", default=1, type=int, help="The number of times to submit.")
    parser.add_argument("--submit_runtime_months", dest="submit_runtime_months", default=12, type=int, help="The length of each submit in months, defaults to 12.")
    parser.add_argument("--submit_runtime_days", dest="submit_runtime_days", default=0, type=int, help="The length of each submit in days, defaults to 0.")
    parser.add_argument("--new_run", dest="new_run", action='store_true', default=False, help="Set this option to indicate a new run.")
    parser.add_argument("--init_date", dest="init_date", default='00010101', type=str, help="The initial date of the entire run, this is a string of form yyyymmdd.")
    parser.add_argument("--input_dir", dest="input_dir", default='/short/v45/auscom', type=str, help="Where input data is kept for each experiment.")
    parser.add_argument("--run_direct", dest="run_direct", action='store_true', default=False, help="Run the model directly, don't use qsub.")

    args = parser.parse_args()

    if (args.submit_runtime_days != 0):
        sys.stderr.write('Arg --submit_runtime_days not supported\n')
        parser.print_help()
        return 1

    if (args.submit_runtime_months != 0) and (args.submit_runtime_days != 0):
        sys.stderr.write('Args --submit_runtime_months and --submit_runtime_days cannot both be non-zero.\n')
        parser.print_help()
        return 1

    # Strange, datetime.date doesn't have strptime()
    init_date = datetime.date(int(args.initdate[0:4]), int(args.initdate[4:6]), int(args.initdate[6:8]))
    script_path = os.path.dirname(os.path.realpath(__file__))
    exp_dir = os.path.abspath(os.path.join(script_path, '../exp/', args.experiment))
    input_dir = os.path.abspath(os.path.join(args.inputdir, args.experiment))

    # Read the config file. 
    config = None
    with open(os.path.join(exp_dir, 'run_config.yaml')) as f:
        config = yaml.safe_load(f)

    if args.new_run:
        assert (os.path.exists(input_dir))
        prepare_newrun(exp_dir, input_dir)
    else:
        prepare_contrun(exp_dir, args.initdate)

    prev_start_date = None
    for num_submits in range(args.submits): 

        prev_start_date = set_next_startdate(exp_dir, init_date, prev_start_date, args.submit_runtime_months, num_submits + 1, args.new_run)
        args.new_run = False

        (ret, err, run_id) = run(exp_dir, config, args.run_direct)
        archive(exp_dir, run_id)

        if not ret:
            print 'Run failed, see %s' % err
            return 1
            
        prepare_contrun(exp_dir)

    clean_up()

    return 0
        
if __name__ == "__main__":
    sys.exit(main())
