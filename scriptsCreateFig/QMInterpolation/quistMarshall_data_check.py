import os
import sys
# import configparser
# import json
# import _readConfig
import argparse
import shutil
import numpy as np
import matplotlib.pyplot as plt
import math
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

# all data are from Quist & Marshall (1968)
if m == 0.001:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([985, 940, 885, 835, 785, 730])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([960, 920, 865, 810, 758, 705, 660])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([760, 715, 660, 612])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([685, 650, 595, 550])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([490, 450])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([357, 340])
elif m == 0.005023:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([955, 920, 870, 820, 770, 720])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([930, 900, 845, 790, 748, 695, 648])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([740, 700, 645, 600])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([660, 630, 580, 532])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([475, 444])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([349, 332])
elif m == 0.01:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([900, 880, 840, 805, 755, 708])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([880, 860, 820, 775, 730, 680, 630])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([720, 680, 630, 580])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([640, 606, 564, 518])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([465, 430])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([342, 324])
elif m == 0.01492:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([870, 855, 920,790, 745, 698])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([855, 835, 795, 760, 718, 670, 617])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([705, 666, 620, 568])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([625, 598, 554, 508])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([455, 420])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([335, 318])
elif m == 0.01994:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([850, 835, 805, 775, 735, 690])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([835, 820, 775, 745, 710, 660, 605])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([690, 658, 610, 558])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([610, 588, 543, 500])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([445, 412])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([330, 314])
elif m == 0.04942:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([765, 755, 725, 705, 670, 640])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([765, 750, 700, 670, 640, 610, 570])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([625, 600, 570, 530])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([560, 540, 510, 475])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([420, 400])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([318, 305])
elif m == 0.1:
    density_350 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95])
    eq_cond_350 = np.array([680, 675, 645, 635, 620, 590])
    density_300 = np.array([0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1])
    eq_cond_300 = np.array([695, 675, 635, 615, 600, 575, 535])
    density_250 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_250 = np.array([580, 570, 535, 500])
    density_200 = np.array([0.85, 0.9, 0.95, 1])
    eq_cond_200 = np.array([535, 520, 490, 450])
    density_150 = np.array([0.95, 1])
    eq_cond_150 = np.array([405, 380])
    density_100 = np.array([0.95, 1])
    eq_cond_100 = np.array([300, 290])

# interpolate
dens = []
# dens.extend(density_350)
dens.extend(density_300)
dens.extend(density_250)
dens.extend(density_200)
dens.extend(density_150)
dens.extend(density_100)
temp = []
# temp.extend([350]*len(density_350))
temp.extend([300]*len(density_300))
temp.extend([250]*len(density_250))
temp.extend([200]*len(density_200))
temp.extend([150]*len(density_150))
temp.extend([100]*len(density_100))
eqcd = []
# eqcd.extend(eq_cond_350)
eqcd.extend(eq_cond_300)
eqcd.extend(eq_cond_250)
eqcd.extend(eq_cond_200)
eqcd.extend(eq_cond_150)
eqcd.extend(eq_cond_100)
f_eq_cond = interpolate.interp2d(np.array(dens), np.array(temp), np.array(eqcd), kind='cubic')


# conductivity [S/m]
conductivity = lambda eq_cond, density, molality: eq_cond * density * molality * 0.001 * 1e5
# resistivity [ohmm]
resistivity = lambda eq_cond, density, molality: 1/(eq_cond * density * molality * 0.1)


fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(1,2,1)
x = np.arange(0.75, 1.01, 0.01)

# ax.plot(density_350, eq_cond_350, 'ro', label='350C')
ax.plot(density_300, eq_cond_300, 'o', color=cm.viridis(300/350), label='300C')
ax.plot(density_250, eq_cond_250, 'o', color=cm.viridis(250/350), label='250C')
ax.plot(density_200, eq_cond_200, 'o', color=cm.viridis(200/350), label='200C')
ax.plot(density_150, eq_cond_150, 'o', color=cm.viridis(150/350), label='150C')
ax.plot(density_100, eq_cond_100, 'o', color=cm.viridis(100/350), label='100C')
ax.set_xlabel("density")
ax.set_ylabel("equivalent conductance [S cm^2/mol]")
ax.set_title(f"molality  {m} [mol/kg]")
ax.grid()
ax.legend()

for t in [350, 305, 290, 300, 275, 250, 225, 200, 175, 150, 125]:
    ax.plot(x, f_eq_cond(x,t), '-', color=cm.viridis(t/350), label=f'{t}C')

ax2 = fig.add_subplot(1,2,2)
# ax2.plot(density_350, conductivity(eq_cond_350, density_350, 0.001), 'ro', label='350C')
ax2.plot(density_300, resistivity(eq_cond_300, density_300, m), 'o', color=cm.viridis(300/300), label='300C')
ax2.plot(density_250, resistivity(eq_cond_250, density_250, m), 'o', color=cm.viridis(250/300), label='250C')
ax2.plot(density_200, resistivity(eq_cond_200, density_200, m), 'o', color=cm.viridis(200/300), label='200C')
ax2.plot(density_150, resistivity(eq_cond_150, density_150, m), 'o', color=cm.viridis(150/300), label='150C')
ax2.plot(density_100, resistivity(eq_cond_100, density_100, m), 'o', color=cm.viridis(100/300), label='100C')
for t in [300, 250, 200, 150, 100]:
    ax2.plot(x, resistivity(f_eq_cond(x,t),x,m), '-', color=cm.viridis(t/300), label=f'{t}C')

ax2.set_xlabel("density")
ax2.set_ylabel("resistivity [ohmm]")
ax2.legend()
# ax2.semilogy()
ax2.set_title(f"molality  {m} [mol/kg]")
plt.show()


 
 
 



