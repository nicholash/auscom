#!/bin/bash
# TODO: Create a makefile

function check {
    "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo "$1 failed."
        exit 1
    fi
}

BASEDIR=$(pwd)
cd submodels/oasis3-mct/compile
check ./comp_oasis3.sh
cd ${BASEDIR}

cd submodels/cice4.1/compile
check ./comp_auscom_cice.sh 6
cd ${BASEDIR}

cd submodels/matm/compile
check ./comp_auscom_matm.sh
cd ${BASEDIR}

cd submodels/mom4p1/compile
check ./comp_auscom_mom4p1.sh
cd ${BASEDIR}

