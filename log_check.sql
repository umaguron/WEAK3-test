select 
    a.toughinput_id,
    --a.configIni,
    a.t2dir as t2dir___________________________________________________________, 
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
    b.status,
    --b.surface_heat,
    --b.surface_flow,
    --b.surface_flow_l,
    --b.surface_flow_g,
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
    c.temperature
    --c.vol_injblock, 
    --c.dist_injblock,
from (
    select
        toughinput_id,
        total_time, 
        time_steps, 
        last_timestep_length,
        status,
        --surface_heat,
        --surface_flow,
        --surface_flow_l,
        --surface_flow_g,
        --convergence_temp,
        --convergence_pres,
        --start_time,    
        --end_time,
        --elapsed_time,
        updated_time
    from toughResult
    -- where 
        -- total_time > 3600*24*365*10
    order by updated_time desc
    limit 300
) b 
left join toughinput a on a.toughinput_id = b.toughinput_id
left outer join gener c on c.toughinput_id = b.toughinput_id
order by b.updated_time asc;

.exit
