import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate 
import matplotlib.cm as cm

# choise of molality
# m = 0.001
# m = 0.005023
# m = 0.01
# m= 0.01492
# m = 0.01994
m = 0.04942
# m = 0.1
# def equivalent_conductance_function(molality):
# all data are from Quist & Marshall (1968)

molality = [0.001, 0.005023, 0.01, 0.01492, 0.01994, 0.04942, 0.1]
eq_cond_func = []
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

# prepare interpolating function
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
    f_eq_cond = interpolate.interp2d(np.array(dens), np.array(temp), np.array(eqcd), kind='linear')
    eq_cond_func.append(f_eq_cond)


# conductivity [S/m]
conductivity = lambda eq_cond, density, molality: eq_cond * density * molality * 0.001 * 1e5
# resistivity [ohmm]
resistivity = lambda eq_cond, density, molality: 1/(eq_cond * density * molality * 0.1)


x = np.arange(0.8, 1.01, 0.01)

for molality_index, m in enumerate(molality):
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(1,2,1)
    ax2 = fig.add_subplot(1,2,2)

    qmd = QM_data[molality_index]    
    for i,t in enumerate(qmd['temperature']):
        ax.plot(qmd['density'][i], qmd['eq_cond'][i], 'o', color=cm.viridis(t/350), label=f'{t}C')
        ax2.plot(qmd['density'][i], resistivity(qmd['eq_cond'][i],qmd['density'][i],m), 'o', color=cm.viridis(t/350), label=f'{t}C')
    
    for t in [ 300, 250,  200, 150, 100, 50]:
        ax.plot(x, eq_cond_func[molality_index](x,t), '-', color=cm.viridis(t/350), label=f'{t}C')
        ax2.plot(x, resistivity(eq_cond_func[molality_index](x,t),x,m), '-', color=cm.viridis(t/350), label=f'{t}C')
    
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


 
 
 



