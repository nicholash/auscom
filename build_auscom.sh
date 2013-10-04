#!/bin/bash

function check {
    "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo "$1 failed."
        exit 1
    fi
}

BASEDIR=$(pwd)
cd submodels/oasis3-mct/util/make_dir
check make -j 4 -f TopMakefileOasis3
cd ${BASEDIR}

cd submodels/cice4.1/compile
check ./comp_auscom_cice.sh 6
cd ${BASEDIR}

cd submodels/matm/compile
check ./comp_auscom_matm.sh
cd ${BASEDIR}

cd submodels/mom5/exp
check ./MOM_compile.csh --platform nci --type MOM_ACCESS
cd ${BASEDIR}
cp ./submodels/mom5/exec/nci/MOM_ACCESS/fms_MOM_ACCESS.x bin/

