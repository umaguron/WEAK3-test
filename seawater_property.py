import iapws
iapws.SeaWater
import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from define import *

# https://www.jodc.go.jp/jodcweb/JDOSS/index_j.html
# N33-N35, E139-E140 (miyake)
seawater_statistics = [
    {'depth':0, 'salinity':34.43138453, 'temp':21.15302555},
    {'depth':10, 'salinity':34.41049439, 'temp':20.87590619},
    {'depth':20, 'salinity':34.47719996, 'temp':20.34291111},
    {'depth':30, 'salinity':34.51720191, 'temp':19.87974692},
    {'depth':50, 'salinity':34.5674094, 'temp':18.96491075},
    {'depth':75, 'salinity':34.60286533, 'temp':17.86596717},
    {'depth':100, 'salinity':34.6150096, 'temp':16.81951468},
    {'depth':125, 'salinity':34.59873745, 'temp':15.90300563},
    {'depth':150, 'salinity':34.58221192, 'temp':15.02509749},
    {'depth':200, 'salinity':34.52677864, 'temp':13.4826785},
    {'depth':250, 'salinity':34.46231355, 'temp':11.98466653},
    {'depth':300, 'salinity':34.41426073, 'temp':10.69950202},
    {'depth':400, 'salinity':34.32812735, 'temp':8.504727601},
    {'depth':500, 'salinity':34.28159578, 'temp':6.789771666},
    {'depth':600, 'salinity':34.28643655, 'temp':5.522221298},
    {'depth':700, 'salinity':34.31362944, 'temp':4.784717542},
    {'depth':800, 'salinity':34.34597305, 'temp':4.154193548},
    {'depth':900, 'salinity':34.38, 'temp':3.689180064},
    {'depth':1000, 'salinity':34.41454128, 'temp':3.38987234},
    {'depth':1100, 'salinity':34.44467213, 'temp':3.119026217},
    {'depth':1200, 'salinity':34.4759322, 'temp':2.933064516},
    {'depth':1300, 'salinity':34.50410959, 'temp':2.751625},
    {'depth':1400, 'salinity':34.52434783, 'temp':2.586027397},
    {'depth':1500, 'salinity':34.54163265, 'temp':2.45},]

FUNC_SEA_SALINITY = interp1d(
    [_['depth'] for _ in seawater_statistics], 
    [_['salinity'] for _ in seawater_statistics],
    bounds_error=False,
    fill_value=seawater_statistics[-1]['salinity'])

FUNC_SEA_TEMP = interp1d(
    [_['depth'] for _ in seawater_statistics], 
    [_['temp'] for _ in seawater_statistics],
    bounds_error=False,
    fill_value=seawater_statistics[-1]['temp'])


P = ATMOS_PRESSURE # Pa
dh = 50 # m
depths = np.arange(0,5000,dh)
dens = []
hydro_p = []
for h in depths:
    rho = iapws.SeaWater(T=273.15+FUNC_SEA_TEMP(h), P=P/1e6, S=FUNC_SEA_SALINITY(h)/1000).rho
    P += GRAV_ACCEL * dh * rho
    dens.append(rho)
    hydro_p.append(P)

FUNC_SEA_PRESSURE = interp1d(depths, hydro_p)

# plt.plot(depths, FUNC_SEA_PRESSURE(depths))
# plt.plot(depths, 1e5+depths*(sum(dens)/len(dens))*9.806)
# plt.show()

