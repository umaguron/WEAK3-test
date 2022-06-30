
"""
'toughInput', 'problemName','
'toughInput', 'mulgridFileName','
'toughInput', 't2DataFileName','
'toughInput', 'gridVtkFileName','
'toughInput', 'toughOutputFileName','
'toughInput', 'resultVtuFileName','
'toughInput', 'print_block','
'toughInput', 'water_table_elevation','
'toughInput', 'PRIMARY_default','
'toughInput', 'specifies_variable_INCON','
'toughInput', 'primary_sec_list','
'toughInput', 'rockseclist','
'toughInput', 'seedFlg','
'toughInput', 'generSecList','
<--TODO
'toughInput', 'history_block','
'toughInput', 'history_connection','
'toughInput', 'prints_hc_surface','
'toughInput', 'prints_hc_inj','
'toughInput', 'selection_line1','
'toughInput', 'selection_line2','
-->
'toughInput', 'num_times_specified','
'toughInput', 'num_times','
'toughInput', 'max_timestep_TIMES','
'toughInput', 'time_increment','
'toughInput', 'time','
'toughInput', 'assignFocusHf','
'toughInput', 'focusHfRate','
'toughInput', 'focusHfRange','
"""

PARANAME_INI_GUI_CMESH5 = \
(
    # section, key, name_in_gui
    ['toughInput','simulator','simulator'],
    ['toughInput','problemName','problemName'],
    ['toughInput','module','module'],
    ['toughInput','num_components','num_components'],
    ['toughInput','num_equations','num_equations'],
    ['toughInput','num_phases','num_phases'],
    ['toughInput','num_secondary_parameters','num_secondary_parameters'],
    ['toughInput','max_iterations','max_iterations'],
    ['toughInput','print_level','print_level'],
    ['toughInput','max_timesteps','max_timesteps'],
    ['toughInput','max_duration','max_duration'],
    ['toughInput','print_interval','print_interval'],
    ['toughInput','MOPs01','mops01'],
    ['toughInput','MOPs02','mops02'],
    ['toughInput','MOPs03','mops03'],
    ['toughInput','MOPs04','mops04'],
    ['toughInput','MOPs05','mops05'],
    ['toughInput','MOPs06','mops06'],
    ['toughInput','MOPs07','mops07'],
    ['toughInput','MOPs08','mops08'],
    ['toughInput','MOPs09','mops09'],
    ['toughInput','MOPs10','mops10'],
    ['toughInput','MOPs11','mops11'],
    ['toughInput','MOPs12','mops12'],
    ['toughInput','MOPs13','mops13'],
    ['toughInput','MOPs15','mops15'],
    ['toughInput','MOPs16','mops16'],
    ['toughInput','MOPs17','mops17'],
    ['toughInput','MOPs18','mops18'],
    ['toughInput','MOPs24','mops24'],
    ['toughInput','texp','texp'],
    ['toughInput','be','be'],
    ['toughInput','tstart','tstart'],
    ['toughInput','tstop','tstop'],
    ['toughInput','const_timestep','const_timestep'],
    ['toughInput','max_timestep','max_timestep'],
    ['toughInput','gravity','gravity'],
    ['toughInput','timestep_reduction','timestep_reduction'],
    ['toughInput','scale','scale'],
    ['toughInput','relative_error','relative_error'],
    ['toughInput','absolute_error','absolute_error'],
    ['toughInput','upstream_weight','upstream_weight'],
    ['toughInput','newton_weight','newton_weight'],
    ['toughInput','derivative_increment','derivative_increment'],
    ['toughInput','for','for'],
    ['toughInput','amres','amres'],
    ['toughInput','problemNamePreviousRun','problemNamePreviousRun'],
    ['toughInput','1d_hydrostatic_sim_result_ini','1d_hydrostatic_sim_result_ini'],
    ['toughInput','initial_t_grad','initial_t_grad'],
    ['toughInput','crustalHeatFlowRate','crustalHeatFlowRate'],
    ['toughInput','rainfallAnnual_mm','rainfallAnnual_mm'],
    ['toughInput','T_rain','T_rain'],
    ['toughInput','generSecList','generSecList'],
    ['toughInput','PRIMARY_default','PRIMARY_default'],
    ['toughInput','history_block','history_block'],
    ['toughInput','history_connection','history_connection'],
    ['toughInput','prints_hc_surface','prints_hc_surface'],
    ['solver','matslv','matslv'],
    ['solver','zprocs','zprocs'],
    ['solver','oprocs','oprocs'],
    ['solver','ritmax','ritmax'],
    ['solver','closur','closur'],
    ['solver','nProc','nProc'],
    ['solver','ksp_type','ksp_type'],
    ['solver','pc_type','pc_type'],
    ['solver','ksp_rtol','ksp_rtol'],
    ['amesh_voronoi','topodata_fp','topodata_fp'],
    ['mesh','resistivity_structure_fp','resistivity_structure_fp'],
    # ['toughInput','prints_hc_inj','prints_hc_inj'],
)