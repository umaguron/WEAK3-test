import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate 
import matplotlib.cm as cm

########
density = 0.8
temperature = 230
m = 0.02
########

molality = np.array([0.001, 0.005023, 0.01, 0.01492, 0.01994, 0.04942, 0.1])
QM_data = []
# 0.001
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
# 0.005023:
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
# 0.01:
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
# 0.01492:
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

#  0.01994:
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

# 0.04942:
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

# 0.1
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
# rebuild and interpolate
# molality, dens_temp
points_dens_temp_4each_mol = []
values_eqcond_4each_mol = []
f_eqcond_linearND = []
for molality_index, m in enumerate(molality):
    points_dens_temp = []
    values = []
    qmd = QM_data[molality_index] 
    for i,t in enumerate(qmd['temperature']):
        for j, d in enumerate(qmd['density'][i]):
            points_dens_temp.append([d, t])
            values.append(qmd['eq_cond'][i][j])
    points_dens_temp_4each_mol.append(points_dens_temp)
    values_eqcond_4each_mol.append(values)
    f_eqcond_linearND.append(interpolate.LinearNDInterpolator(points_dens_temp, values))


""" interp2d cubic"""
# prepare interpolating function
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


x = np.arange(0.3, 1.01, 0.01)

### choise of eq_cond func ###
eq_func = f_eqcond_linearND
# eq_func = f_eqcond_cubic
####################################



for molality_index, m in enumerate(molality):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)

    qmd = QM_data[molality_index]    
    for i,t in enumerate(qmd['temperature']):
        ax.plot(qmd['density'][i], qmd['eq_cond'][i], 'o', color=cm.viridis(t/600), label=f'{t}C')
        ax2.plot(qmd['density'][i], resistivity(qmd['eq_cond'][i],qmd['density'][i],m), 'o', color=cm.viridis(t/600), label=f'{t}C')
    
    for t in [600, 550, 500, 450, 400, 350, 300, 200, 100]:
        ax.plot(x, eq_func[molality_index](x,t), '-', color=cm.viridis(t/600), label=f'{t}C')
        ax2.plot(x, resistivity(eq_func[molality_index](x,t),x,m), '-', color=cm.viridis(t/600), label=f'{t}C')
    
    ax.set_xlabel("density")
    ax.set_ylabel("equivalent conductance [S cm^2/mol]")
    ax.set_title(f"molality  {m} [mol/kg]")
    ax.grid()
    ax.legend()
    ax2.set_xlabel("density")
    ax2.set_ylabel("resistivity [ohmm]")
    ax2.legend()
    # ax2.semilogy()
    ax2.set_title(f"molality  {m} [mol/kg]")

plt.show()
plt.clf()


# mol vs conductance curve for each temperature
mol = 10**np.arange(-3,-1,0.01)
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(1,2,1)
ax2 = fig.add_subplot(1,2,2)
# for T in [350, 325, 300, 275, 250, 225, 200, 175, 150, 125, 100, 75, 50]:
for T in [600, 550, 500, 450, 400, 350]:
    # prepare function at given temp, dens
    list_of_eqcond_at_given_dens_temp = []
    for molality_index, m in enumerate(molality):
        list_of_eqcond_at_given_dens_temp.append(eq_func[molality_index](density,T))
    f = interpolate.interp1d(molality,list_of_eqcond_at_given_dens_temp, kind='cubic')
    # plot
    ax.plot(molality, list_of_eqcond_at_given_dens_temp, 'o', color=cm.viridis(T/600))
    ax.plot(mol, f(mol), '-', color=cm.viridis(T/600), label=f'{T}C')
    ax2.plot(molality, resistivity(np.array(list_of_eqcond_at_given_dens_temp),density,molality), 'o', color=cm.viridis(T/350))
    ax2.plot(mol, resistivity(f(mol),density,mol), '-', color=cm.viridis(T/600), label=f'{T}C')
ax.grid()
ax.semilogx()
ax.set_xlabel("molality[mol/kg]")
ax.set_ylabel("equivalent conductance [S cm^2/mol]")
ax.set_title(f'dens.:{density}')
ax.legend()
ax2.grid()
ax2.semilogx()
ax2.legend()
ax2.set_ylabel("resistivity [ohmm]")
ax2.set_xlabel("molality[mol/kg]")
plt.show()

 



