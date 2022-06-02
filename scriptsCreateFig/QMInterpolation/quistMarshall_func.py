import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import interpolate 
import matplotlib.cm as cm

########
density = 0.98
temperature = 200
m = 0.1
########
                                                                                
def brine_resistivity(molality, density, temperature):
    """[summary]
    Calculate resistivity value of brine based on the data in Quist & Marshall 
    (1968). 
    At first, compute a 2d interpolating function (linear) for each table (table.I to 
    table.VIII). (equivalent conductance=f(temperature, densitiy)).
    Next, by using above function, calc eq. conductance values in each 
    table at given temp & dens. (We get molality values and corresponding eq.
    conductance values.)
    Then, by interpolating molality values and corresponding eq. conductance 
    values, we get a eq. condactance value at given molality, density
    and temperature.

    Args:
        molality (float): molality of brine [mol/kg]
        density (float): density of brine [g/cm^3]
        temperature (float): temperature of brine [C]

    Returns:
        float : resistivity of brine [ohm-m]
    """ 
    
    molality_QM = np.array([0.001, 0.005023, 0.01, 0.01492, 0.01994, 0.04942, 0.1])
    QM_data = []
    # 0.001
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([985, 940, 885, 835, 785, 730]),
        np.array([960, 920, 865, 810, 758, 705, 660]),
        np.array([760, 715, 660, 612]),
        np.array([685, 650, 595, 550]),
        np.array([490, 450]),
        np.array([357, 340])
    ]
    QM_data.append(data_m)
    # 0.005023:
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([955, 920, 870, 820, 770, 720]),
        np.array([930, 900, 845, 790, 748, 695, 648]),
        np.array([740, 700, 645, 600]),
        np.array([660, 630, 580, 532]),
        np.array([475, 444]),
        np.array([349, 332])
    ]
    QM_data.append(data_m)
    # 0.01:
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([900, 880, 840, 805, 755, 708]),
        np.array([880, 860, 820, 775, 730, 680, 630]),
        np.array([720, 680, 630, 580]),
        np.array([640, 606, 564, 518]),
        np.array([465, 430]),
        np.array([342, 324])
    ]
    QM_data.append(data_m)
    # 0.01492:
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([870, 855, 820, 790, 745, 698]),
        np.array([855, 835, 795, 760, 718, 670, 617]),
        np.array([705, 666, 620, 568]),
        np.array([625, 598, 554, 508]),
        np.array([455, 420]),
        np.array([335, 318])
    ]
    QM_data.append(data_m)

    #  0.01994:
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([850, 835, 805, 775, 735, 690]),
        np.array([835, 820, 775, 745, 710, 660, 605]),
        np.array([690, 658, 610, 558]),
        np.array([610, 588, 543, 500]),
        np.array([445, 412]),
        np.array([330, 314])
    ]
    QM_data.append(data_m)

    # 0.04942:
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([765, 755, 725, 705, 670, 640]),
        np.array([765, 750, 700, 670, 640, 610, 570]),
        np.array([625, 600, 570, 530]),
        np.array([560, 540, 510, 475]),
        np.array([420, 400]),
        np.array([318, 305])
    ]
    QM_data.append(data_m)

    # 0.1
    data_m = {}
    data_m['temperature'] = [350, 300, 250, 200, 150, 100]
    data_m['density'] = [
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
        np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.85, 0.9, 0.95, 1]),
        np.array([0.95, 1]),
        np.array([0.95, 1])
    ]
    data_m['eq_cond'] = [
        np.array([680, 675, 645, 635, 620, 590]),
        np.array([695, 675, 635, 615, 600, 575, 535]),
        np.array([580, 570, 535, 500]),
        np.array([535, 520, 490, 450]),
        np.array([405, 380]),
        np.array([300, 290])
    ]
    QM_data.append(data_m)


    """ LinearNDInterpolator """
    # rebuild and interpolate
    # prepare interpolating function for each table(density x temp)
    points_dens_temp_4each_mol = []
    values_eqcond_4each_mol = []
    f_eqcond_linearND = []
    for molality_index, m in enumerate(molality_QM):
        points_dens_temp = []
        values = []
        qmd = QM_data[molality_index] 
        for i,t in enumerate(qmd['temperature']):
            for j, d in enumerate(qmd['density'][i]):
                points_dens_temp.append([d, t])
                values.append(qmd['eq_cond'][i][j])
        points_dens_temp_4each_mol.append(points_dens_temp)
        values_eqcond_4each_mol.append(values)
        # equivalent condactance as a function of temperature and density
        f_eqcond_linearND.append(interpolate.LinearNDInterpolator(points_dens_temp, values))


    """ interp2d cubic"""
    # prepare interpolating function for each table(density x temp)
    f_eqcond_cubic = []
    for qmd in QM_data:
        # interpolate
        dens = []
        temp = []
        eqcd = []
        for d in qmd['density']:
            dens.extend(d)
        for e in qmd['eq_cond']:
            eqcd.extend(e)
        for i,t in enumerate(qmd['temperature']):
            temp.extend([t]*len(qmd['density'][i]))
        f_eq_cond = interpolate.interp2d(np.array(dens), np.array(temp), np.array(eqcd), kind='cubic')
        f_eqcond_cubic.append(f_eq_cond)


    # conductivity [S/m]
    conductivity = lambda eq_cond, density, molality: eq_cond * density * molality * 0.001 * 1e5
    # resistivity [ohmm]
    resistivity = lambda eq_cond, density, molality: 1/(eq_cond * density * molality * 0.1)


    ### choise of eq_cond func ###
    eq_func = f_eqcond_linearND
    # eq_func = f_eqcond_cubic
    ####################################
  
    list_of_eqcond_at_given_dens_temp = []
    # calc equivalent conductance for each molality value at given temp. and dens.
    for molality_index, m in enumerate(molality_QM):
        list_of_eqcond_at_given_dens_temp.append(eq_func[molality_index](density,temperature))
    # imterpolate.
    # equivalent condactance[S*cm^-2/mol] = f(molality)
    f = interpolate.interp1d(molality_QM,list_of_eqcond_at_given_dens_temp, kind='linear')

    return resistivity(f(molality),density, molality)
    # return conductivity(f(molality),density, molality)

def HS_upper_bounds(proportion_phs1, sigma1, sigma2):
    if sigma1 > sigma2:
        return proportion_phs1 / (1.0 / (sigma1 - sigma2) + (1.0 - proportion_phs1) / 3.0 / sigma2) + sigma2
    else:
        return (1.0 - proportion_phs1) / (1.0 / (sigma2 - sigma1) + proportion_phs1 / 3.0 / sigma1) + sigma1


cond = 1/brine_resistivity(m, density, temperature)
bulk = HS_upper_bounds(0.2, cond, 0.01)

print("molality   :", m)    
print("density    :", density)    
print("temperature:", temperature)    
print("resistivity:", 1/cond)    
print("conductivity:", cond)    
print("bulk resis :", 1/bulk)    
print("bulk cond :", bulk)    



