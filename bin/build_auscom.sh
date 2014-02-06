#!/bin/bash

if [ $# != 1 ]; then 
    echo "Usage: build_auscom.sh <platform>"
    exit 1
fi

platform=$1

function check {
    "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo "$1 failed."
        exit 1
    fi
}

# Export this to do a debug build.
#export DEBUG=yes

BASEDIR=$(pwd)
cd ../submodels/oasis3-mct/util/make_dir
echo "include $HOME/auscom/submodels/oasis3-mct/util/make_dir/make.$platform" > make.inc
source config.$platform
check make -j 4 -f TopMakefileOasis3
cd ${BASEDIR}

cd ../submodels/cice4.1/compile
check ./comp_auscom_cice.sh $platform
cd ${BASEDIR}

cd ../submodels/matm/compile
check ./comp_auscom_matm.sh $platform
cd ${BASEDIR}

cd ../submodels/mom/exp
check ./MOM_compile.csh --platform $platform --type MOM_ACCESS
cd ${BASEDIR}
cp ../submodels/mom/exec/$platform/MOM_ACCESS/fms_MOM_ACCESS.x ./
