// set default values
DEFAULTS_TEXT = {
    max_iterations:"",
    max_timesteps: 100,
    max_duration: "",
    print_interval: 100,
    tstop: 1e20,
    mops01: 1,
    mops07: 1,
    mops08: 0,
    mops16_1: 4,
    texp: "",
    be: "",
    tstart: "",
    tstop: "",
    const_timestep: 1e-5,
    max_timestep: "",
    gravity: 9.807,
    timestep_reduction: "",
    scale: "",
    relative_error: "",
    absolute_error: "",
    upstream_weight: "",
    newton_weight: "",
    derivative_increment: "",
    for: "",
    amres: "",
    history_block: "[]",
    history_connection: "[]",
    crustalHeatFlowRate: 0,
    rainfallAnnual_mm: 0,
    T_rain: 10,
}
DEFAULTS_TEXT_DEPEND_EOS = {
    eco2n: {
        primary: [1.013e5, 0, 0, 10]
    },
    eos2: {
        primary: [1.013e5, 10, 0]
    }
}
DEFAULTS_RADIO = {
    print_level: 0,
    mops09: 0,
    mops10: 0,
    mops11: 0,
    mops12: 0,
    mops13: 0,
    mops15: 0,
    mops16: 2,
    mops17: 9,
    mops18: 0,
    mops24: 0,
}
DEFAULTS_TEXT_SELEC_V2 = {
    FE9: 0.8,
    FE10: 0.8,
}
DEFAULTS_RADIO_SELEC_V2 = {
    IE1: 1,
    IE3: 0,
    IE4: 1,
    IE11: 0,
    IE12: 0,
    IE13: 0,
    IE14: 0,
    IE15: 4,
    IE16: 0,
}
PRIMARY_DESCRIPTION = {
    'EOS2': {
        'length': 3,
        'description_one_p':[
            '<b>P</b> - pressure [Pa] ',
            '<b>T</b> - temperature [ºC]',
            '<b>P<sub>CO2</sub></b> - partial pressure'
        ],
        'description_two_p':[
            '<b>P<sub>g</sub></b> - gas phase pressure [Pa] ',
            '<b>S<sub>g</sub></b> - gas saturation',
            '<b>P<sub>CO2</sub></b> - partial pressure'
        ],
        'caution': 'see EOS2 user\'s guide for details'
    },
    'ECO2N_V2':{
        'length': 4,
        'description_one_p':[
            '<b>P</b> - pressure [Pa] ',
            '<b>X<sub>sm</sub></b> - NaCl salt mass fraction X<sub>s</sub>, or solid NaCl saturation S<sub>s</sub>+10',
            '<b>X3</b> - CO<sub>2</sub> (true) mass fraction in the aqueous phase, or in the gas phase, in the three-component system water-salt-CO<sub>2</sub>',
            '<b>T</b> - temperature [ºC]',
        ],
        'description_two_p':[
            '<b>P</b> - pressure [Pa] ',
            '<b>X<sub>sm</sub></b> - NaCl salt mass fraction X<sub>s</sub>, or solid saturation S<sub>s</sub>+10',
            '<b>S<sub>g</sub></b> - gas phase saturation',
            '<b>T</b> - temperature [ºC]'
        ],
        'caution': 'see ECO2N_V2 user\'s guide for details'
    },
}
