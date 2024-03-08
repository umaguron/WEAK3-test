#!/bin/bash

function exitmessage () {
cat <<EEE
$1
EEE
exit
}

[ -z $1 ] && exitmessage "[usage] \$1: output file of TOUGH3 program"
ls $1 &>/dev/null || exitmessage "file $1 not found"

sed -n -E '/PETSC Solver failed to converged|^ [ A-z0-9]{5}\(.{8}\)|STOP EXECUTION|CANNOT FIND PARAMETERS AT ELEMENT|\+\+\+\+\+\+\+\+\+|\!\!\!\!\!\!\!\!\!\!\!\!\!\! EXCESSIVE RESIDUAL|NO CONVERGENCE AFTER | LAST TIME STEP WAS|TOUGH STATUS: Failed in|\.\.\.ITERATING/p' ${1}

