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
cd submodels/oasis3/prism/compile
check ./comp_oasis325.nci
cd ${BASEDIR}

cd submodels/cice4.1/compile
check ./comp_auscom_cice.sh 6
cd ${BASEDIR}

cd submodels/matm/compile
check ./comp_auscom_matm.sh
cd ${BASEDIR}

cd submodels/mom4p1/compile
check ./comp_auscom_mom4p1_cfc.sh
cd ${BASEDIR}

