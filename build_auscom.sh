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
check ./comp_oasis325.VAYU
cd ${BASEDIR}

cd submodels/cice4.1/compile
check ./comp_auscom_cice.VAYU.nP 6
cd ${BASEDIR}

cd submodels/matm/compile
check ./comp_auscom_matm.VAYU
cd ${BASEDIR}

cd submodels/mom4p1/compile
check ./comp_auscom_mom4p1_cfc.VAYU
cd ${BASEDIR}

