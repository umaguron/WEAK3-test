create table toughInput (
    toughinput_id integer primary key,
    configIni,
    t2dir,
    module ,
    problemName ,
    t2DataFileName ,
    gridVtkFileName ,
    toughOutputFileName ,
    resultVtuFileName ,
    num_components ,
    num_equations ,
    num_phases ,
    num_secondary_parameters ,
    print_interval ,
    max_timesteps ,
    print_level ,
    tstop ,
    const_timestep ,
    gravity ,
    PRIMARY_AIR ,
    PRIMARY_default ,
    MOPs01 ,
    MOPs02 ,
    MOPs03 ,
    MOPs04 ,
    MOPs05 ,
    MOPs06 ,
    MOPs07 ,
    MOPs08 ,
    MOPs09 ,
    MOPs10 ,
    MOPs11 ,
    MOPs12 ,
    MOPs13 ,
    MOPs14 ,
    MOPs15 ,
    MOPs16 ,
    MOPs17 ,
    problemNamePreviousRun ,
    rockSecList ,
    generSecList ,
    crustalHeatFlowRate ,
    rainfallAnnual_mm ,
    T_rain ,
    isRadial, 
    num_element_axis1,
    num_element_axis2,
    num_element_axis3
);

create table toughresult (
    toughinput_id integer primary key,
    time_steps,
    total_time,
    status,
    convergence_temp,
    convergence_pres,
    start_time,
    end_time,
    elapsed_time,
    updated_time,
    FOREIGN KEY(toughinput_id) references toughinput(toughinput_id)
);

create table ROCK (
    rock_id integer primary key,
    toughinput_id,
    name ,
    nad ,
    density ,
    porosity ,
    permeability_x ,
    permeability_y ,
    permeability_z ,
    conductivity ,
    specific_heat ,
    regionSecList ,
    IRP ,
    RP ,
    ICP ,
    CP ,
    FOREIGN KEY(toughinput_id) references toughinput(toughinput_id)
);

create table gener (
    gener_id integer primary key,
    toughinput_id,
    name ,
    block ,
    area ,
    type ,
    flux ,
    temperature ,
    vol_injblock ,
    dist_injblock ,
    FOREIGN KEY(toughinput_id) references toughinput(toughinput_id)
);

-- 
ALTER TABLE toughresult ADD COLUMN surface_heat real;
ALTER TABLE toughresult ADD COLUMN surface_flow real;
ALTER TABLE toughresult ADD COLUMN surface_flow_l real;
ALTER TABLE toughresult ADD COLUMN surface_flow_g real;
ALTER TABLE toughinput ADD COLUMN updated_time;
ALTER TABLE rock ADD COLUMN updated_time;
ALTER TABLE gener ADD COLUMN updated_time;

-- 20210331 add
ALTER TABLE toughresult ADD COLUMN last_timestep_length real;

-- 20210416 add
ALTER TABLE toughinput ADD COLUMN max_iterations real;
ALTER TABLE toughinput ADD COLUMN max_duration real;
ALTER TABLE toughinput ADD COLUMN texp real;
ALTER TABLE toughinput ADD COLUMN be real;
ALTER TABLE toughinput ADD COLUMN tstart real;
ALTER TABLE toughinput ADD COLUMN max_timestep real;
ALTER TABLE toughinput ADD COLUMN timestep_reduction real;
ALTER TABLE toughinput ADD COLUMN scale real;
ALTER TABLE toughinput ADD COLUMN relative_error real;
ALTER TABLE toughinput ADD COLUMN absolute_error real;
ALTER TABLE toughinput ADD COLUMN upstream_weight real;
ALTER TABLE toughinput ADD COLUMN newton_weight real;
ALTER TABLE toughinput ADD COLUMN derivative_increment real;
ALTER TABLE toughinput ADD COLUMN for real;
ALTER TABLE toughinput ADD COLUMN amres real;

-- 20211019 add
ALTER TABLE toughinput ADD COLUMN matslv;
ALTER TABLE toughinput ADD COLUMN z_precond;
ALTER TABLE toughinput ADD COLUMN o_precond;
ALTER TABLE toughinput ADD COLUMN relative_max_iterations real;
ALTER TABLE toughinput ADD COLUMN closure real;
ALTER TABLE toughinput ADD COLUMN nproc;
ALTER TABLE toughinput ADD COLUMN ksp_type;
ALTER TABLE toughinput ADD COLUMN pc_type;
ALTER TABLE toughinput ADD COLUMN ksp_rtol real;

-- create table region(
--     region_id integer primary key,
--     rock_id,
--     xmin ,
--     xmax ,
--     ymin ,
--     ymax ,
--     zmin ,
--     zmax ,
--     FOREIGN KEY(rock_id) references rock(rock_id)
-- );