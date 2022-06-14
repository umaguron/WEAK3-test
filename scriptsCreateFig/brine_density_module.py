import numpy as np
import pathlib, sys, os, math
baseDir = pathlib.Path(__file__).parent.resolve()
from scipy.interpolate import LinearNDInterpolator

"""output of read_sowat_out.py"""
SOWAT_OUTPUT="data/sowat_read.txt"
"""utility"""
x_mol2x_wt = lambda x_mol: 58.5*x_mol/(40.5*x_mol+18)
x_wt2x_mol = lambda x_wt: 18*x_wt/(58.5-40.5*x_wt)

# global
T_list = np.array([])
P_list = np.array([])
X_list = np.array([])


def dens_in_PTX_space(pressure=None, temperature=None, x_nacl_mol=None):
    """[summary]
    SoWat NaCl-H2O fluid propertie (Driesner et al., 2007)
    if all arguments are None, it returns full data.
    
    phase index
        1: single phase liquid
        2:V
        3:L 
        4:V+L
        5:L+salt
        6:V+salt
    
    * SoWat NaCl-H2O fluid properties * 
    SoWat stands for Sodium chloride-​Water and is a model (almost an equation of state) for the properties of fluids in the H2O-​NaCl system. It was published in two parts in Geochimica et Cosmochimica Acta:
    
    * citation *
    Driesner T., and Heinrich C.A. (2007): The System H2O-​NaCl. I. Correlation Formulae for Phase Relations in Temperature-​Pressure-Composition Space from 0 to 1000°C, 0 to 5000 bar, and 0 to 1 XNaCl. Geochimica et Cosmochimica Acta 71, 4880-​4901.
    Driesner T. (2007) The System H2O-​NaCl. II. Correlations for molar volume, enthalpy, and isobaric heat capacity from 0 to 1000 degrees C, 1 to 5000 bar, and 0 to 1 XNaCl. Geochimica et Cosmochimica Acta 71(20), 4902-​4919.


    Args:
        pressure ([float]): pressure in bar
        temperature ([float]): temperature in C
        x_nacl_mol ([float]): mole fraction of NaCl 

    Returns:
        [list]: [T(C), P(bar), Xnacl_mol(-), phase_index, total_density (kg/m3)]
    """
    ret = []
    count = 0

    """ get values list for each parameter"""
    global T_list, P_list, X_list
    T_tmp, P_tmp, X_tmp = [], [], []
    if len(T_list)==0 or len(P_list)==0 or len(X_list)==0:
        with open(SOWAT_OUTPUT, "r") as f:
            for line in f:
                arr = line.split(",")
                T_tmp.append(float(arr[1]))
                P_tmp.append(float(arr[2]))
                X_tmp.append(float(arr[3]))
        # unique
        T_list = np.unique(T_tmp)
        P_list = np.unique(P_tmp)
        X_list = np.unique(X_tmp)
        # 昇順
        T_list.sort()
        P_list.sort()
        X_list.sort()
        print(T_list)        
        print(P_list)        
        print(X_list)

    # 最も近い値の2ペアを取得
    if pressure is not None:
        if len(P_list[P_list<=pressure])>0 and len(P_list[P_list>=pressure])>0:
            P_bounds = P_list[P_list<=pressure][-1], P_list[P_list>=pressure][0]
        else:
            sys.exit(f"pressure:{pressure} out of range")
    if temperature is not None: 
        if len(T_list[T_list<=temperature])>0 and len(T_list[T_list>=temperature])>0:
            T_bounds = T_list[T_list<=temperature][-1], T_list[T_list>=temperature][0]
        else:
            sys.exit(f"temperature:{temperature} out of range")
    if x_nacl_mol is not None:
        if len(X_list[X_list<=x_nacl_mol])>0 and len(X_list[X_list>=x_nacl_mol])>0:
            X_bounds = X_list[X_list<=x_nacl_mol][-1], X_list[X_list>=x_nacl_mol][0]
        else:
            sys.exit(f"x_nacl_mol:{x_nacl_mol} out of range")
   
    """ construct interpolating function """
    with open(SOWAT_OUTPUT, "r") as f:
        for line in f:

            arr = line.split(",")
            T = float(arr[1])
            P = float(arr[2])
            Xnacl_mol_in = float(arr[3])

            # 全データだどおもすぎるので。
            if pressure is not None and (P<min(P_bounds) or  max(P_bounds)<P):
                continue
            if temperature is not None and (T<min(T_bounds) or  max(T_bounds)<T):
                continue
            if x_nacl_mol is not None and (Xnacl_mol_in<min(X_bounds) or  max(X_bounds)<Xnacl_mol_in):
                continue

            v=len(arr[4])
            l=len(arr[8])
            s=len(arr[12])
            spl=len(arr[16])
            if spl>0:
                # single phase liquid
                phase = 1
                dens = float(arr[16])
            elif v>0 and l==0 and s==0:
                # V
                phase = 2
                dens = float(arr[4])
            elif v==0 and l>0 and s==0:
                # L
                phase = 3
                dens = float(arr[8])
            elif v>0 and l>0 and s==0:
                # V + L
                phase = 4

                dens_l = float(arr[8])
                molv_l = float(arr[9])
                Xnacl_mol_l = float(arr[11])
                dens_v = float(arr[4])
                molv_v = float(arr[5])
                Xnacl_mol_v = float(arr[7])

                liq_moleFract = (Xnacl_mol_in-Xnacl_mol_v)/(Xnacl_mol_l-Xnacl_mol_v)
                total_moler_volume = molv_l*liq_moleFract + molv_v*(1-liq_moleFract)
                total_moler_wt = 58.5*Xnacl_mol_in + 18*(1-Xnacl_mol_in)

                dens_total = total_moler_wt/total_moler_volume*1000
                dens = dens_total
            
            elif v==0 and l>0 and s>0:
                # L + salt
                phase = 5
                dens_l = float(arr[8])
                molv_l = float(arr[9])
                Xnacl_mol_l = float(arr[11])
                dens_s = float(arr[12])
                molv_s = float(arr[13])
                Xnacl_mol_s = float(arr[15])

                liq_moleFract = (Xnacl_mol_in-Xnacl_mol_s)/(Xnacl_mol_l-Xnacl_mol_s)
                total_moler_volume = molv_l*liq_moleFract + molv_s*(1-liq_moleFract)
                total_moler_wt = 58.5*Xnacl_mol_in + 18*(1-Xnacl_mol_in)
                
                dens_total = total_moler_wt/total_moler_volume*1000
                dens = dens_total

            elif v>0 and l==0 and s>0:
                # V + salt
                phase = 6

                dens_v = float(arr[4])
                molv_v = float(arr[5])
                Xnacl_mol_v = float(arr[7])
                dens_s = float(arr[12])
                molv_s = float(arr[13])
                Xnacl_mol_s = float(arr[15])

                vap_moleFract = (Xnacl_mol_in-Xnacl_mol_s)/(Xnacl_mol_v-Xnacl_mol_s)
                total_moler_volume = molv_v*vap_moleFract + molv_s*(1-vap_moleFract)
                total_moler_wt = 58.5*Xnacl_mol_in + 18*(1-Xnacl_mol_in)
                
                dens_total = total_moler_wt/total_moler_volume*1000
                dens = dens_total
            
            ret.append([T, P, Xnacl_mol_in, phase, dens])
            count += 1
        
    print(f"data points {count}")
    return np.array(ret, dtype=np.float64)

def get_dens_func(pressure=None, temperature=None, x_nacl_mol=None):
    """_summary_
    if pressure is given, returns function density(T, X_nacl_mol) [kg/m3] at given pressure.
    if temperature is given, returns function density(P, X_nacl_mol) [kg/m3] at given temperature.
    if x_nacl_mol is given, returns function density(P, T) [kg/m3] at given nacl mole fraction.

    Args:
        pressure (_type_, optional): [bar]. Defaults to None.
        temperature (_type_, optional): [C]. Defaults to None.
        x_nacl_mol (_type_, optional): nacl mole fraction[-]. Defaults to None.

    Returns: (function) 
    """

    # get full data
    data = dens_in_PTX_space(pressure=pressure, temperature=temperature, x_nacl_mol=x_nacl_mol)
    T = data[:,0]
    P = data[:,1]
    X_nacl_mol = data[:,2]
    dens = data[:,4]

    if (pressure is None) and (temperature is None) and (x_nacl_mol is not None):
        return LinearNDInterpolator(list(zip(P,T)), dens, fill_value=0)
    elif (pressure is None) and (temperature is not None) and (x_nacl_mol is None):
        return LinearNDInterpolator(list(zip(P,X_nacl_mol)), dens, fill_value=0)
    elif (pressure is not None) and (temperature is None) and (x_nacl_mol is None):
        return LinearNDInterpolator(list(zip(T,X_nacl_mol)), dens, fill_value=0)
    else:
        pass


if __name__ == "__main__":
    # f = get_dens_func(pressure=100)
    # print(f([100, 0.01]))
    # f = get_dens_func(temperature=100)
    # print(f([100, 0.01]))
    f = get_dens_func(x_nacl_mol=0.01)
    print(f([100,100]))