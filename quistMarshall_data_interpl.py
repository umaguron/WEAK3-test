"""
All data are from Quist & Marshall (1968). 
[static variables]
MOLALITY_QM: 
    np.array of molality value of each table
F_EQCOND_LINEARND: 
    list of 2d interpolating function (linear) for each table (table.I to table.VII)
    The order of list is consistent to MOLALITY_QM.
    Usage of interpolating function F_EQCOND_LINEARND[i] is as follows:
        eq.conductance (@ MOLALITY_QM[i] m) = F_EQCOND_LINEARND[i](density, temperature)
F_EQCOND_CUBIC: 
    list of 2d interpolating function (cubic spline) for each table (table.I to table.VII)
    The order of list is consistent to MOLALITY_QM.
    Usage of interpolating function F_EQCOND_CUBIC[i] is as follows:
        eq.conductance (@ MOLALITY_QM[i] m) = F_EQCOND_CUBIC[i](density, temperature)
"""             
import numpy as np
from scipy import interpolate 

QM_data = []
""" molality value of each table """
MOLALITY_QM = np.array([0.001, 0.005023, 0.01, 0.01492, 0.01994, 0.04942, 0.1])

""" table.I (0.001m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [
    np.array([190, 400, 660, 900, 1010, 1050, 1050, 1020, 985, 940, 890]),
    np.array([230, 460, 730, 940, 1040, 1070, 1065, 1035, 995, 945, 900]),
    np.array([280, 540, 800, 980, 1070, 1090, 1080, 1050, 1000, 950, 905, 840]),
    np.array([340, 650, 880, 1020, 1100, 1100, 1085, 1055, 1005, 950, 905, 850, 800]),
    np.array([420, 800, 1000, 1080, 1140, 1110, 1090, 1055, 1000, 950, 895, 845, 795, 740]),
    np.array([985, 940, 885, 835, 785, 730]),
    np.array([960, 920, 865, 810, 758, 705, 660]),
    np.array([760, 715, 660, 612]),
    np.array([685, 650, 595, 550]),
    np.array([490, 450]),
    np.array([357, 340])
]
QM_data.append(data_m)

""" table.II (0.005023m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [
    np.array([125, 245, 420, 620, 790, 890, 925, 940, 935, 910, 860]),
    np.array([145, 280, 460, 670, 820, 910, 945, 960, 950, 925, 875]),
    np.array([180, 340, 520, 710, 860, 940, 965, 975, 960, 930, 885, 830]),
    np.array([220, 420, 595, 750, 900, 960, 980, 980, 965, 930, 885, 835, 790]),
    np.array([280, 520, 690, 810, 940, 970, 995, 980, 965, 930, 880, 830, 785, 730]),
    np.array([955, 920, 870, 820, 770, 720]),
    np.array([930, 900, 845, 790, 748, 695, 648]),
    np.array([740, 700, 645, 600]),
    np.array([660, 630, 580, 532]),
    np.array([475, 444]),
    np.array([349, 332])
]
QM_data.append(data_m)

""" table.III (0.01m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [    
    np.array([ 85, 180, 330, 505, 650, 770, 825, 860, 865, 850, 830]),
    np.array([110, 215, 370, 545, 690, 800, 845, 880, 880, 860, 845]),
    np.array([140, 270, 425, 590, 730, 830, 870, 895, 895, 870, 850, 810]),
    np.array([180, 340, 490, 645, 770, 850, 890, 910, 905, 880, 855, 815, 770]),
    np.array([230, 430, 610, 710, 820, 870, 915, 920, 905, 885, 855, 815, 770, 718]),
    np.array([900, 880, 840, 805, 755, 708]),
    np.array([880, 860, 820, 775, 730, 680, 630]),
    np.array([720, 680, 630, 580]),
    np.array([640, 606, 564, 518]),
    np.array([465, 430]),
    np.array([342, 324])
]
QM_data.append(data_m)

""" table.IV (0.01492m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [
    np.array([165, 305, 460, 600, 720, 780, 825, 840, 820, 815]),
    np.array([200, 345, 510, 640, 750, 805, 840, 855, 835, 825]),
    np.array([250, 395, 550, 680, 790, 830, 860, 865, 850, 835, 795]),
    np.array([320, 460, 605, 730, 810, 850, 875, 875, 860, 845, 800, 760]),
    np.array([405, 550, 660, 780, 830, 870, 885, 875, 865, 840, 800, 760, 710]),
    np.array([870, 855, 820, 790, 745, 698]),
    np.array([855, 835, 795, 760, 718, 670, 617]),
    np.array([705, 666, 620, 568]),
    np.array([625, 598, 554, 508]),
    np.array([455, 420]),
    np.array([335, 318])
]
QM_data.append(data_m)

""" table.V (0.01994m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [
    np.array([150, 280, 425, 560, 680, 745, 800, 820, 810, 800]),
    np.array([190, 320, 465, 600, 720, 770, 820, 840, 820, 815]),
    np.array([240, 370, 510, 640, 750, 795, 840, 850, 830, 820, 780]),
    np.array([300, 430, 560, 690, 780, 815, 850, 860, 845, 825, 790, 750]),
    np.array([380, 510, 610, 730, 790, 835, 855, 860, 845, 820, 790, 750, 702]),
    np.array([850, 835, 805, 775, 735, 690]),
    np.array([835, 820, 775, 745, 710, 660, 605]),
    np.array([690, 658, 610, 558]),
    np.array([610, 588, 543, 500]),
    np.array([445, 412]),
    np.array([330, 314])
]
QM_data.append(data_m)

""" table.VI (0.04942m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [
    np.array([40, 95, 185, 310, 420, 530, 610, 660, 700, 715, 720]),
    np.array([50, 120, 210, 340, 450, 560, 640, 685, 715, 735, 740]),
    np.array([70, 150, 250, 380, 485, 590, 665, 710, 735, 750, 750, 730]),
    np.array([100, 205, 310, 430, 525, 620, 690, 735, 750, 760, 750, 735]),
    np.array([135, 280, 380, 480, 580, 650, 710, 750, 760, 760, 745, 730, 690, 655]),
    np.array([765, 755, 725, 705, 670, 640]),
    np.array([765, 750, 700, 670, 640, 610, 570]),
    np.array([625, 600, 570, 530]),
    np.array([560, 540, 510, 475]),
    np.array([420, 400]),
    np.array([318, 305])
]
QM_data.append(data_m)

""" table.VII (0.1m) """
data_m = {}
data_m['temperature'] = [600, 550, 500, 450, 400, 350, 300, 250, 200, 150, 100]
data_m['density'] = [
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85]),
    np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95]),
    np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.85, 0.9, 0.95, 1]),
    np.array([0.95, 1]),
    np.array([0.95, 1])
]
data_m['eq_cond'] = [
    np.array([85, 160, 260, 360, 450, 520, 565, 605, 625, 645]),
    np.array([105, 185, 290, 380, 470, 540, 585, 625, 640, 655]),
    np.array([140, 220, 320, 410, 490, 565, 610, 640, 650, 655, 640]),
    np.array([190, 270, 360, 450, 520, 590, 630, 655, 660, 655, 645]),
    np.array([260, 350, 410, 490, 540, 610, 650, 670, 670, 655, 645, 630, 600]),
    np.array([680, 675, 645, 635, 620, 590]),
    np.array([695, 675, 635, 615, 600, 575, 535]),
    np.array([580, 570, 535, 500]),
    np.array([535, 520, 490, 450]),
    np.array([405, 380]),
    np.array([300, 290])
]
QM_data.append(data_m)

""" LinearNDInterpolator """
# rebuild QM_data and interpolate
# prepare interpolating function for each table(density x temp)
points_dens_temp_4each_mol = []
values_eqcond_4each_mol = []
F_EQCOND_LINEARND = []
for molality_index, m in enumerate(MOLALITY_QM):
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
    F_EQCOND_LINEARND.append(interpolate.LinearNDInterpolator(points_dens_temp, values))


""" interp2d cubic"""
# prepare interpolating function for each table(density x temp)
F_EQCOND_CUBIC = []
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
    F_EQCOND_CUBIC.append(f_eq_cond)