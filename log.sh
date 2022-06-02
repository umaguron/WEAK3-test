#!/bin/bash
cd  `dirname $0`
if [ -z $3 ];then
cat << EOF
usage
    \$1: word for search in column: t2dir (+where t2dir like '%$1%')
    \$2: lower limit for column: year
    \$3: lower limit for column: dt_last
    \$4: (optional) additional condition clause (like, "and flux > 10")
EOF
exit
fi

sqlite3 log.db << EOF
select 
    --a.toughinput_id,
    --a.configIni,
    a.t2dir as t2dir_________________________________________________________________________________________________________________________________________, 
    a.module ,
    --a.problemName ,
    --a.t2DataFileName ,
    --a.gridVtkFileName ,
    --a.toughOutputFileName ,
    --a.resultVtuFileName ,
    --a.num_components ,
    --a.num_equations ,
    --a.num_phases ,
    --a.num_secondary_parameters ,
    --a.print_interval ,
    --a.max_timesteps ,
    --a.print_level ,
    --a.tstop ,
    --a.const_timestep ,
    --a.gravity ,
    --a.PRIMARY_AIR ,
    --a.PRIMARY_default ,
    --a.MOPs01 ,
    --a.MOPs02 ,
    ----a.MOPs03 ,
    --a.MOPs04 ,
    --a.MOPs05 ,
    --a.MOPs06 ,
    --a.MOPs07 ,
    --a.MOPs08 ,
    --a.MOPs09 ,
    --a.MOPs10 ,
    --a.MOPs11 ,
    --a.MOPs12 ,
    --a.MOPs13 ,
    --a.MOPs14 ,
    --a.MOPs15 ,
    --a.MOPs16 ,
    --a.MOPs17 ,
    --a.problemNamePreviousRun ,
    --a.rockSecList ,
    --a.generSecList ,
    --a.crustalHeatFlowRate ,
    --a.rainfallAnnual_mm ,
    --a.T_rain ,
    --a.isRadial, 
    --a.num_element_axis1,
    --a.num_element_axis2,
    --a.num_element_axis3,
    b.total_time/3600/24/365 as total_year___________, 
    b.time_steps, 
    b.last_timestep_length as dt_last,
    b.surface_heat / 1000000 as "sufHF(MW)",
    --b.surface_flow,
    --b.surface_flow_l,
    b.surface_flow_g as gasFlo,
    --b.convergence_temp,
    --b.convergence_pres,
    --b.start_time,    
    --b.end_time,
    --b.elapsed_time,
    b.updated_time,
    c.name,
    --c.block,
    --c.area,
    --c.type,
    c.flux,
    c.temperature,
    --c.vol_injblock, 
    --c.dist_injblock,
    b.status
from (
    select
    toughinput_id,
    --configIni,
    t2dir, 
    module
    --problemName ,
    --t2DataFileName ,
    --gridVtkFileName ,
    --toughOutputFileName ,
    --resultVtuFileName ,
    --num_components ,
    --num_equations ,
    --num_phases ,
    --num_secondary_parameters ,
    --print_interval ,
    --max_timesteps ,
    --print_level ,
    --tstop ,
    --const_timestep ,
    --gravity ,
    --PRIMARY_AIR ,
    --PRIMARY_default ,
    --MOPs01 ,
    --MOPs02 ,
    --MOPs03 ,
    --MOPs04 ,
    --MOPs05 ,
    --MOPs06 ,
    --MOPs07 ,
    --MOPs08 ,
    --MOPs09 ,
    --MOPs10 ,
    --MOPs11 ,
    --MOPs12 ,
    --MOPs13 ,
    --MOPs14 ,
    --MOPs15 ,
    --MOPs16 ,
    --MOPs17 ,
    --problemNamePreviousRun ,
    --rockSecList ,
    --generSecList ,
    --crustalHeatFlowRate ,
    --rainfallAnnual_mm ,
    --T_rain ,
    --isRadial, 
    --num_element_axis1,
    --num_element_axis2,
    --num_element_axis3
    from toughInput
    where t2dir like '%$1%'
    order by updated_time desc
    limit 300
) a 
left join toughResult b on a.toughinput_id = b.toughinput_id
left outer join gener c on c.toughinput_id = b.toughinput_id
where
    b.total_time >= 3600*24*365.25*$2
    and dt_last >= 0+$3
$4
--order by b.updated_time asc;
order by t2dir asc;
EOF

