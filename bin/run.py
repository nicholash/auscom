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

"""
Set off auscom and access runs. Getting very messy, move to payu. 
"""

run_script = """
#!/bin/csh -f

#PBS -P <project>
#PBS -q <queue>
#PBS -l walltime=<walltime>
#PBS -l ncpus=<ncpus>
#PBS -l mem=<mem>
#PBS -l wd
#PBS -N <exp_name>

module load openmpi/1.6.5-mlx
module load ipm

mpirun --mca mtl ^mxm --mca orte_base_help_aggregate 0 -wdir <atm_dir> -n <atm_ncpus> <exp_dir>/matmxx : -wdir <ice_dir> -n <ice_ncpus> <exp_dir>/cicexx : -wdir <ocn_dir> -n <ocn_ncpus> <exp_dir>/mom5xx 2> <ocn_dir>/stderr.txt 1> <ocn_dir>/stdout.txt

"""

def prepare_newrun(exp_dir, model, input_dir):
    """
    Anything that needs to be done before the model starts.
    """

    # Delete and remake old INPUT and RESTART dirs, these get polluted. e.g. by oasis writing over the restart files.
    for d, m in [('ATM_RUNDIR', 'atm'), ('ICE_RUNDIR', 'ice'), ('OCN_RUNDIR', 'ocn')]:

        rundir = os.path.join(exp_dir, d)
        if os.path.exists(rundir):
            shutil.rmtree(rundir)

        if model == 'access' and d == 'ATM_RUNDIR':
            input = rundir
        else:
            input = os.path.join(exp_dir, d, 'INPUT')

        restart = os.path.join(exp_dir, d, 'RESTART')
        history = os.path.join(exp_dir, d, 'HISTORY')
        os.makedirs(input)
        os.makedirs(restart)
        os.makedirs(history)

        # Copy over inputs and fix perms.
        for f in glob.glob('%s/*' % os.path.join(input_dir, m)):
            shutil.copy(f, input)
            os.chmod(os.path.join(input, os.path.basename(f)), 0664)

        # Copy oasis files into input dir. 
        for f in glob.glob('%s/*' % os.path.join(input_dir, 'oasis')):
            if model == 'access':
                shutil.copy(f, rundir)
                os.chmod(os.path.join(rundir, os.path.basename(f)), 0664)
            else:
                shutil.copy(f, input)
                os.chmod(os.path.join(input, os.path.basename(f)), 0664)

        # For some reason cice needs o2i.nc in a special place. FIXME.
        if model == 'access' and d == 'ICE_RUNDIR':
            shutil.copy(os.path.join(rundir, 'o2i.nc'), os.path.join(restart, 'o2i.nc'))

        # Copy fresh config files into place. 
        for f in glob.glob('%s/config/*' % exp_dir):
            shutil.copy(f, os.path.join(exp_dir, d))

    shutil.copytree(os.path.join(exp_dir, 'atm_tmp_ctrl'), os.path.join(exp_dir, 'ATM_RUNDIR', 'tmp_ctrl'))
    os.makedirs(os.path.join(exp_dir, 'ATM_RUNDIR', 'tmp'))

    if model == 'access':
        # Tell CABLE that this is not a cont run.
        nml = FortranNamelist(os.path.join(exp_dir, 'ATM_RUNDIR', 'cable.nml'))
        nml.set_value('cable', 'cable_user%CABLE_RUNTIME_COUPLED', '.FALSE.')
        nml.write()


def prepare_contrun(exp_dir, model, cont_date):
    """
    Anything that needs to be done before a continuation run, apart from setting up the dates.
    
    There are some things that the models should take care of themselves.
    """

    cont_date_str = date_to_str(cont_date)

    ice_input = os.path.join(exp_dir, 'ICE_RUNDIR', 'INPUT')
    ice_restart = os.path.join(exp_dir, 'ICE_RUNDIR', 'RESTART')
    ocn_input = os.path.join(exp_dir, 'OCN_RUNDIR', 'INPUT')
    ocn_restart = os.path.join(exp_dir, 'OCN_RUNDIR', 'RESTART')

    # Copy over some CICE files. 
    if model == 'access':
        shutil.copy(os.path.join(exp_dir, 'ICE_RUNDIR', 'mice.nc'), ice_input)
    else:
        shutil.copy(os.path.join(ice_restart, 'u_star.nc'), ice_input)
        shutil.copy(os.path.join(ice_restart, 'sicemass.nc'), ice_input)

    # Setup the CICE restart. 
    # Check that restart file for this start date exists. 
    assert(os.path.exists(os.path.join(ice_restart, 'iced.%s' % (cont_date_str))))
    with open(os.path.join(ice_restart, 'ice.restart_file'), 'w') as f:
        f.write('iced.%s' % cont_date_str)

    # Copy over ocean restarts.
    for f in glob.glob('%s/*' % ocn_restart):
        shutil.copy(f, ocn_input)

    # Copy fresh config files into place. FIXME: This is being done in newrun also.
    for d in ['ATM_RUNDIR', 'ICE_RUNDIR','OCN_RUNDIR']:
        for f in glob.glob('%s/config/*' % exp_dir):
            shutil.copy(f, os.path.join(exp_dir, d))

    if model == 'access':
        # Copy over the oasis restarts. FIXME: should this be done for auscom model?
        shutil.copy(os.path.join(ocn_input, 'o2i.nc'), ice_restart)

        # Copy over UM restart file. 
        um_restart_src = os.path.join(exp_dir, 'ATM_RUNDIR', 'aiihca.da%s' % date_to_um_date(cont_date))
        um_restart_dest = os.path.join(exp_dir, 'ATM_RUNDIR', 'PIC2C-0.25.astart')
        shutil.copy(um_restart_src, um_restart_dest)

        # Tell CABLE that this is a cont run.
        nml = FortranNamelist(os.path.join(exp_dir, 'ATM_RUNDIR', 'cable.nml'))
        nml.set_value('cable', 'cable_user%CABLE_RUNTIME_COUPLED', '.TRUE.')
        nml.write()


def ndays_between_dates(start_date, end_date, include_leap_days):
    """
    Calculate the number of days between two dates according to a 365 calendar.
    If include_leap_days == True then leap days are included.

    The dates should always have day 01.
    """

    assert(start_date.day == 1 and end_date.day == 1)

    def leap_days_between_dates(start_date, end_date):
        """
        Return the number of leap days between two dates. 

        The easiest way to do this is to just iterate over all days. 
        """

        leaps = 0
        one_day = datetime.timedelta(1)

        curr_date = start_date
        while curr_date != end_date:
            if curr_date.month == 2 and curr_date.day == 29:
                leaps += 1

            curr_date += one_day
            
        return leaps

    # Do the calculation using timedelta and then subtract the leap days added.
    td = end_date - start_date

    if include_leap_days:
        return (td.days)
    else:
        return (td.days - leap_days_between_dates(start_date, end_date))


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


def date_to_str(date):
    """Convert a time date object to a string like: yyyymmdd."""

    return (str(date.year).zfill(4) + str(date.month).zfill(2) + str(date.day).zfill(2))

def str_to_date(str):
    """Convert string like: yyyymmdd to a time date object."""

    return datetime.date(int(str[0:4]), int(str[4:6]), int(str[6:8]))

def date_to_um_date(date):
    """Convert a time date object to a um format date string which is yymd0
    
        To accomodate two digit months and days the UM uses letters. e.g. 1st oct 
        is writting 01a10. What does this say about the UM? 
    """

    assert(date.month <= 12)

    month = str(date.month)
    if date.month == 10:
        month = 'a'
    elif date.month == 11:
        month = 'b'
    elif date.month == 12:
        month = 'c'

    return (str(date.year).zfill(2) + month + str(date.day) + str(0))


def set_next_startdate(exp_dir, init_date, prev_start_date, runtime_per_submit, submit_num, newrun, model):
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

    days_since_start = ndays_between_dates(init_date, start_date, model == 'access')
    days_this_run = ndays_between_dates(start_date, end_date, model == 'access')

    # init_date is the start date of the experiment. 
    init_str = date_to_str(init_date)
    run_str = date_to_str(start_date)

    atm_rundir = os.path.join(exp_dir, 'ATM_RUNDIR')

    # Atmos.
    if model == 'auscom': 
        nml = FortranNamelist(os.path.join(atm_rundir, 'input_atm.nml'))
        # The start of the experiment.
        nml.set_value('coupling', 'init_date', init_str)
        # The start of the run.
        nml.set_value('coupling', 'inidate', run_str)
        nml.set_value('coupling', 'truntime0', days_since_start*86400)
        nml.set_value('coupling', 'runtime', days_this_run*86400)
        nml.write()
    else:
        # Changes for the UM. 
        nml = FortranNamelist(os.path.join(atm_rundir, 'tmp_ctrl', 'CNTLALL'))
        # Run length
        nml.set_value('NLSTCALL', 'RUN_TARGET_END', '0, 0, %s, 0, 0, 0' % days_this_run)
        # Resubmit increement
        nml.set_value('NLSTCALL', 'RUN_RESUBMIT_INC', '0, 0, %s, 0, 0, 0' % days_this_run)
        # Start time
        nml.set_value('NLSTCALL', 'MODEL_BASIS_TIME', '%s, %s, %s, 0, 0, 0' % (run_str[0:4], run_str[4:6], run_str[6:8]))
        nml.set_value('NLSTCALL', 'ANCIL_REFTIME', '%s, %s, %s, 0, 0, 0' % (run_str[0:4], run_str[4:6], run_str[6:8]))
        nml.write()

        nml = FortranNamelist(os.path.join(atm_rundir, 'tmp_ctrl', 'SIZES'))
        nml.set_value('STSHCOMP', 'RUN_TARGET_END', '0, 0, %s, 0, 0, 0' % days_this_run)
        nml.write()

        def next_three_dump_times(date):
            """
            Return the dump times (in timesteps) for the next three months.
            """

            assert(date.day == 1 and date.month <= 10)
            _, days_1 = calendar.monthrange(date.year, date.month)
            _, days_2 = calendar.monthrange(date.year, date.month + 1)
            _, days_3 = calendar.monthrange(date.year, date.month + 2)

            dump_1 = days_1*48
            dump_2 = dump_1 + days_2*48
            dump_3 = dump_2 + days_3*48

            return (dump_1, dump_2, dump_3)

        dump_1, dump_2, dump_3 = next_three_dump_times(start_date)

        nml = FortranNamelist(os.path.join(atm_rundir, 'tmp_ctrl', 'CNTLGEN'))
        nml.set_value('NLSTCGEN', 'DUMPTIMESim', '%s, %s, %s, %s' % (dump_1, dump_2 , dump_3, '0,'*157))
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

    return (start_date, end_date)

def clean_up():
    pass


def make_run_script(exp_name, model, exp_dir, config):
    """
    Create either auscom or access script. 

    HACK: for now just submit pre-existing access run script. 
    """

    qsub_script = None
    
    if model == 'auscom':
        atm_dir = '%s/ATM_RUNDIR' % (exp_dir)
        ice_dir = '%s/ICE_RUNDIR' % (exp_dir)
        ocn_dir = '%s/OCN_RUNDIR' % (exp_dir)

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
        script = script.replace('<exp_name>' , exp_name[:15])

        qsub_script = os.path.join(exp_dir, 'qsub_run.sh')
        with open(qsub_script, 'w') as f:
            f.write(script)
    else:
        qsub_script = os.path.join(exp_dir, 'run_access.sh')

    return qsub_script

def run(exp_name, model, exp_dir, config, run_direct):
    """
    Submit a job, wait for it to finish, check that it completed properly.
    """

    def wait(run_id):

        while True:
            time.sleep(10)
            qsub_out = ''
            try: 
                qsub_out = subprocess.check_output(['qstat', run_id], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as err:
                qsub_out = err.output

            if 'Job has finished' in qsub_out:
                break

    qsub_script = make_run_script(exp_name, model, exp_dir, config)

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
    ocn_dir = '%s/OCN_RUNDIR' % (exp_dir)
    output = os.path.join(ocn_dir, 'stdout.txt')
    s = ''
    with open(output, 'r') as f:
        s = f.read()

    success = False
    if model == 'access':
        success = (('End of CICE' in s) and ('MOM4: --- completed ---' in s))
    else:
        success = (('End of MATM' in s) and ('End of CICE' in s) and ('MOM4: --- completed ---' in s))

    return (success, output, run_id)

def archive(exp_dir, model, run_name):
    """
    Do some data processing.

    This is a hack, need to move to payu tool.
    """

    archive_dir = os.path.join(exp_dir, 'archive', run_name)
    os.makedirs(archive_dir)

    # Move model dirs into archive, remake new ones, copy INPUT and RESTART back. 
    for model_name in ['ATM_RUNDIR', 'ICE_RUNDIR', 'OCN_RUNDIR']:
        model_dir = os.path.join(exp_dir, model_name)

        if model == 'access':
            if model_name == 'OCN_RUNDIR':
                os.makedirs(os.path.join(archive_dir, model_name))
                for f in glob.glob('%s/ocean*' % model_dir):
                    shutil.move(f, os.path.join(archive_dir, model_name, os.path.basename(f)))
        else:
            shutil.move(model_dir, os.path.join(archive_dir, model_name))
            os.makedirs(model_dir)
            os.makedirs(os.path.join(model_dir, 'HISTORY'))
            shutil.copytree(os.path.join(archive_dir, model_name, 'INPUT'), os.path.join(model_dir, 'INPUT'))
            shutil.copytree(os.path.join(archive_dir, model_name, 'RESTART'), os.path.join(model_dir, 'RESTART'))



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", help="The experiment to run.")
    parser.add_argument("--submits", default=1, type=int, help="The number of times to submit.")
    parser.add_argument("--submit_runtime_months", default=12, type=int, help="The length of each submit in months, defaults to 12.")
    parser.add_argument("--submit_runtime_days", default=0, type=int, help="The length of each submit in days, defaults to 0.")
    parser.add_argument("--new_run", action='store_true', default=False, help="Set this option to indicate a new run.")
    parser.add_argument("--init_date", default='00010101', type=str, help="The initial date of the entire run, this is a string of form yyyymmdd.")
    parser.add_argument("--input_dir", default='/short/v45/auscom', type=str, help="Where input data is kept for each experiment.")
    parser.add_argument("--run_direct", action='store_true', default=False, help="Run the model directly, don't use qsub.")
    parser.add_argument("--skip_run", action='store_true', help="Don't actually run the model, just prepare, archive and resubmit. Used for testing purposes.")
    parser.add_argument("--model", default='auscom', help="Which model to run. Should be either 'auscom' or 'access', defaults to 'auscom'")

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
    init_date = str_to_date(args.init_date)
    script_path = os.path.dirname(os.path.realpath(__file__))
    exp_dir = os.path.abspath(os.path.join(script_path, '../exp/', args.experiment))
    input_dir = os.path.abspath(os.path.join(args.input_dir, args.experiment))

    # Read the config file. 
    config = None
    with open(os.path.join(exp_dir, 'run_config.yaml')) as f:
        config = yaml.safe_load(f)

    if args.new_run:
        assert (os.path.exists(input_dir))
        prepare_newrun(exp_dir, args.model, input_dir)
    else:
        prepare_contrun(exp_dir, args.model, init_date)

    # FIXME: check that an archive directory for this date does not already exist. 

    start_date = None
    end_date = None
    for num_submits in range(args.submits): 

        start_date, end_date = set_next_startdate(exp_dir, init_date, start_date, args.submit_runtime_months, num_submits + 1, args.new_run, args.model)
        args.new_run = False

        if not args.skip_run:
            (ret, err, run_id) = run(args.experiment, args.model, exp_dir, config, args.run_direct)
            if not ret:
                print 'Run failed, see %s' % err
                return 1
            
        archive(exp_dir, args.model, '%s_to_%s' % (start_date, end_date))
        prepare_contrun(exp_dir, args.model, end_date)

    clean_up()

    return 0
        
if __name__ == "__main__":
    sys.exit(main())
