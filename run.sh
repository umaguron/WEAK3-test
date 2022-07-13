#!/bin/bash -x
cd `dirname $0`

if [ -z $1 ];then
echo "empty \$1"
echo "usage \$1: relative path of input.ini" 
exit
fi
ls $1 || exit
#escape
suf=`date "+%s"`s
mkdir tempini &>/dev/null
cp $1 tempini/${suf}_${1////_}
f=tempini/${suf}_${1////_}
    problemname=`python3 configUtil/parseConfig.py $f toughInput problemname`
    TID=`python3 configUtil/parseConfig.py $f configuration TOUGH_INPUT_DIR 2>/dev/null`
    if [ -z $TID ]; then
    settingIni=`python3 configUtil/parseConfig.py $f configuration configIni 2>/dev/null` 
    TID=`python3 configUtil/parseConfig.py $settingIni toughConfig TOUGH_INPUT_DIR  2>/dev/null`
    fi
    if [ -z $TID ]; then
    echo "TOUGH_INPUT_DIR not found in $f. Exit."
    exit
    fi

    outfile=`grep FILENAME_TOUGH_OUTPUT define.py | awk -F= '{print $2}' | sed -e "s/['\"]//g" | sed -e "s/ //g"`
    meshtype=`python3 configUtil/parseConfigMeshT.py $f`
    t2dirfp=${TID}/${problemname}
    outfilefp=${t2dirfp}/$outfile
echo ---- PN: $TID/$problemname
echo ---- CLEAN: $TID/$problemname
    rm -r $t2dirfp &>/dev/null
echo ---- MAKE GRID
    if [ $meshtype == REGULAR ]; then python3 makeGrid.py $f -f
    elif [ $meshtype == A_VORO ]; then python3 makeGridAmeshVoro.py $f -f
    fi
echo ---- MAKE T2DATA 
    python3 tough3exec_ws.py $f -f
echo ---- EXEC 
    start=`date +%s`
    python3 run.py $f #-p 8
    #python3 run.py $f 
    end=`date +%s`
    run_time=$((end - start))
    echo "run.py $run_time [s]" > $t2dirfp/run_time.txt
    ./printIterInfo.sh $outfilefp > ${t2dirfp}/iterinfo.txt
echo ---- REGISTER
    start=`date +%s`
    python3 update_log.py -ini $f
    end=`date +%s`
    run_time=$((end - start))
    echo "update_log.py  $run_time [s]" >> $t2dirfp/run_time.txt
echo ---- PLOT 
    start=`date +%s`
    python3 makeVtu.py $f -foft -coft
    python3 makeVtu.py $f -plc -gifc
    python3 makeVtu.py $f -incon
    python3 makeVtu.py $f -suf
    python3 makeVtu.py $f -sufall 10
    end=`date +%s`
    run_time=$((end - start))
    echo "makeVtu.py $run_time [s]" >> $t2dirfp/run_time.txt
