import numpy as np

def HS_bounds(proportion_phs2, sigma1, sigma2):
    """[summary]
    phase1 is matrix. phase2 is pore fluid.
    sigma2 > sigma1.

    Args:
        proportion_phs2 ([type]): [description]
        sigma1 ([type]): [description]
        sigma2 ([type]): [description]

    Returns:
        tuple: (conductivity[S/m](HS upper bounds), conductivity[S/m](HS lower bounds))
    """
    if sigma1 == sigma2:
        cond_upper, cond_lower = sigma1, sigma1
    else:
        a = 3*(1-proportion_phs2)*(sigma2-sigma1)\
            /(3*sigma2-proportion_phs2*(sigma2-sigma1))
        cond_upper = sigma2*(1-a)
        b = 3*proportion_phs2*(sigma2-sigma1)\
            /(3*sigma1+(1-proportion_phs2)*(sigma2-sigma1))
        cond_lower = sigma1*(1+b)

    return cond_upper, cond_lower

def HS_U_conductivity2porosity(cond_bulk, cond_matrix, cond_liq, upper, lower):
    """[summary]
    return porosity based on HS-U model
    cond_liq > cond_matrix.

    Args:
        cond_bulk ([type]): [description]
        cond_matrix ([type]): [description]
        cond_liq ([type]): [description]
        upper: maximum porosity returned
        lower: minimum porosity returned

    Returns:
        float: estimated porosity (0-1)
    """
    liq_vol_fract = None
    if cond_matrix == cond_liq:
        pass
    else:
        liq_vol_fract = \
            3*cond_liq*(cond_bulk-cond_matrix)/(2*cond_liq+cond_bulk)/(cond_liq-cond_matrix)
            
    if liq_vol_fract > upper:
        return upper
    elif lower > liq_vol_fract:
        return lower
    else:
        return liq_vol_fract

