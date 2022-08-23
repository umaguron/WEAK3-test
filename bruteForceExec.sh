#!/bin/bash 
# bfExec以下のディレクトリを指定するとその中にある全てのiniファイルに対して計算を実施する
cd `dirname $0`

if [ -z $1 ];then
echo "empty \$1"
echo "usage \$1: relative path of directory that includes input.ini files used in bruteforce execution" 
exit
fi
ls $1 || exit

for f in $1/*.ini
do   
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
    meshtype=`python3 configUtil/parseConfigMeshT.py $f`
    t2dirfp=${TID}/${problemname}
    outfile=`grep FILENAME_TOUGH_OUTPUT define.py | awk -F= '{print $2}' | sed -e "s/['\"]//g" | sed -e "s/ //g"`
    outfilefp=${t2dirfp}/$outfile
echo ---- PN: $TID/$problemname
echo ---- CLEAN: $TID/$problemname
continue
    [ -z $TID ] ||  rm -r $t2dirfp
echo ---- MAKE GRID
    if [ $meshtype == REGULAR ]; then python3 makeGrid.py $f -f
    elif [ $meshtype == A_VORO ]; then python3 makeGridAmeshVoro.py $f -f
    fi
echo ---- MAKE T2DATA 
    python3 tough3exec_ws.py $f -f
echo ---- EXEC 
    python3 run.py $f 
    ./printIterInfo.sh $outfilefp > ${t2dirfp}/iterinfo.txt
echo ---- PLOT 
    python3 makeVtu.py $f -foft -coft 
    # python3 makeVtu.py $f -plc 
    # python3 makeVtu.py $f -suf
    python3 makeVtu.py $f -pl
echo ---- REGISTER
    python3 update_log.py -ini $f
done
./log.sh $TID 0 0 > ${TID}/log_result_all.txt
./log.sh $TID 100 0 > ${TID}/log_result_over100yr.txt
./log.sh $TID 10000 0 > ${TID}/log_result_over10000yr.txt
