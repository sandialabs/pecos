"""
The pv module contains custom methods for PV applications.
"""
import pandas as pd
from pecos.metrics import time_integral
import logging

logger = logging.getLogger(__name__)

def insolation(G, tfilter=None):
    """
    Compute insolation defined as:
    
    :math:`H=\int{Gdt}`
    
    where 
    :math:`G` is irradiance and 
    :math:`dt` is the time step between observations.
    The time integral is computed using the trapezoidal rule.
    Results are given in [irradiance units]*seconds.
    
    Parameters
    -----------
    G : pandas DataFrame
        Irradiance time series
        
    tfilter : pandas Series, optional
        Time filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        Insolation
    """
    
    H = time_integral(G, tfilter=tfilter)

    return H
    
def energy(P, tfilter=None):
    """
    Convert energy defined as:
    
    :math:`E=\int{Pdt}`
    
    where 
    :math:`P` is power and 
    :math:`dt` is the time step between observations.
    The time integral is computed using the trapezoidal rule.
    Results are given in [power units]*seconds.
    
    Parameters
    -----------
    P : pandas DataFrame
        Power time series
         
    tfilter : pandas Series, optional
        Time filter containing boolean values for each time index
        
    Returns
    -------
    pandas Series
        Energy
    """
    
    E = time_integral(P, tfilter=tfilter)
    
    return E

def performance_ratio(E, H_poa, P_ref, G_ref=1000):
    """
    Compute performance ratio defined as:

    :math:`PR=\dfrac{Y_{f}}{Yr} = \dfrac{\dfrac{E}{P_{ref}}}{\dfrac{H_{poa}}{G_{ref}}}`
    
    where 
    :math:`Y_f` is the observed energy (AC or DC) produced by the PV system (kWh) 
    divided by the DC power rating at STC conditions.
    :math:`Y_r` is the plane-of-array insolation (kWh/m2) divided 
    by the reference irradiance (1000 W/m2).
    
    Parameters
    -----------
    E : pandas Series or float
        Energy (AC or DC) 
        
    H_poa : pandas Series or float
         Plane of array insolation
         
    P_ref : float
        DC power rating at STC conditions
        
    G_ref : float, optional
        Reference irradiance, default = 1000
        
    Returns
    -------
    pandas Series or float
        Performance ratio in a pandas Series (if E or H_poa are Series) or 
        float (if E and H_poa are floats) 
    """
    
    Yf = E/P_ref
    Yr = H_poa/G_ref
    PR = Yf/Yr
    
    return PR

def normalized_current(I, G_poa, I_sco, G_ref=1000):
    """
    Compute normalized current defined as:

    :math:`NI = \dfrac{\dfrac{I}{I_{sco}}}{\dfrac{G_{poa}}{G_{ref}}}`
    
    where 
    :math:`I` is current, 
    :math:`I_{sco}` is the short circuit current at STC conditions, 
    :math:`G_{poa}` is the plane-of-array irradiance, and 
    :math:`G_{ref}` is the reference irradiance.
    
    Parameters
    -----------
    I : pandas Series or float
        Current
        
    G_poa : pandas Series or float
         Plane of array irradiance
         
    I_sco : float
        Short circuit current at STC conditions
        
    G_ref : float, optional
        Reference irradiance, default = 1000
        
    Returns
    -------
    pandas Series or float
        Normalized current in a pandas Series (if I or G_poa are Series) or 
        float (if I and G_poa are floats) 
    """
    
    N = I/I_sco
    D = G_poa/G_ref
    NI = N/D
    
    return NI
    
def normalized_efficiency(P, G_poa, P_ref, G_ref=1000):
    """
    Compute normalized efficiency defined as:

    :math:`NE = \dfrac{\dfrac{P}{P_{ref}}}{\dfrac{G_{poa}}{G_{ref}}}`
    
    where 
    :math:`P` is the observed power (AC or DC), 
    :math:`P_{ref}` is the DC power rating at STC conditions, 
    :math:`G_{poa}` is the plane-of-array irradiance, and 
    :math:`G_{ref}` is the reference irradiance.
    
    Parameters
    -----------
    P : pandas Series or float
        Power (AC or DC) 
        
    G_poa : pandas Series or float
         Plane of array irradiance
         
    P_ref : float
        DC power rating at STC conditions
        
    G_ref : float, optional
        Reference irradiance, default = 1000
        
    Returns
    -------
    pandas Series or float
        Normalized efficiency in a pandas Series (if P or G_poa are Series) or 
        float (if P and G_poa are floats) 
    """
    
    Yf = P/P_ref
    Yr = G_poa/G_ref
    NE = Yf/Yr
    
    return NE
    
def performance_index(E, E_predicted):
    """
    Compute performance index defined as:
    
    :math:`PI=\dfrac{E}{\hat{E}}`
    
    where 
    :math:`E` is the observed energy from a PV system and  
    :math:`\hat{E}` is the predicted energy over the same time frame.
    :math:`\hat{E}` can be computed using methods in ``pvlib.pvsystem`` 
    and then convert power to energy using ``pecos.pv.enery``.
    
    Unlike with the performance ratio, the performance index should be very 
    close to 1 for a well functioning PV system and should not vary by 
    season due to temperature variations.
    
    Parameters
    -----------
    E : pandas Series or float
        Observed energy
    
    E_predicted : pandas Series or float
        Predicted energy
        
    Returns
    ---------
    pandas Series or float
        Performance index in a pandas Series (if E or E_predicted are Series) or 
        float (if E and E_predicted are floats) 
    """
        
    PI = E/E_predicted
    
    return PI

def energy_yield(E, P_ref):
    """
    Compute energy yield is defined as:
    
    :math:`EY=\dfrac{E}{P_{ref}}`
    
    where 
    :math:`E` is the observed energy from a PV system and  
    :math:`P_{ref}` is the DC power rating of the system at STC conditions.
    
    Parameters
    -----------
    E : pandas Series or float
        Observed energy
    
    P_ref : float
        DC power rating at STC conditions
        
    Returns
    ---------
    pandas Series or float
        Energy yield
    """

    EY = E/P_ref
    
    return EY
    
def clearness_index(H_dn, H_ea):
    """
    Compute clearness index defined as:
    
    :math:`Kt=\dfrac{H_{dn}}{H_{ea}}`
    
    where 
    :math:`H_{dn}` is the direct-normal insolation (kWh/m2)
    :math:`H_{ea}` is the extraterrestrial insolation (kWh/m2)
    over the same time frame.
    Extraterrestrial irradiation can be computed using ``pvlib.irradiance.extraradiation``.  
    Irradiation can be converted to insolation using ``pecos.pv.insolation``.
    
    Parameters
    -----------
    H_dn : pandas Series or float
        Direct normal insolation
    
    H_ea : pandas Series or float
        Extraterrestrial insolation
        
    Returns
    -------
    pandas Series or float
        Clearness index in a pandas Series (if H_dn or H_ea are Series) or 
        float (if H_dn and H_ea are floats) 
    """
        
    Kt = H_dn/H_ea
    
    return Kt
