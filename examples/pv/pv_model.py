import pecos.pv
import pvlib
import pandas as pd
import numpy as np

def sapm(pm, sapm_parameters, location):
    """
    Run the SAPM and compute metrics. Remove data points that failed a previous 
    quality control test before running the model (using pm.cleaned_data). Check range 
    on DC power relative error and normalized efficiency. Compute PV metrics.  
    """
    index = pm.cleaned_data.index
    
    # Extract data into Pandas series
    dcpower = pm.cleaned_data[pm.trans['DC Power']].sum(axis=1)
    acpower = pm.cleaned_data[pm.trans['AC Power']].sum(axis=1)
    wind = pm.cleaned_data[pm.trans['Wind Speed']].squeeze()
    temperature = pm.cleaned_data[pm.trans['Ambient Temperature']].squeeze()
    poa = pm.cleaned_data[pm.trans['POA']].squeeze()
    poa_diffuse = pd.Series(data=0, index=index)
    dni = pm.cleaned_data[pm.trans['DNI']].squeeze()
    
    # Compute sun position
    solarposition = pvlib.solarposition.get_solarposition(index, location['Latitude'], 
                                                  location['Longitude'])
    
    # Compute cell temperature
    celltemp = pvlib.pvsystem.sapm_celltemp(poa, wind, temperature)

    # Compute absolute airmass
    airmass_relative  = pvlib.atmosphere.get_relative_airmass(solarposition['zenith'])
    airmass_absolute = pvlib.atmosphere.get_absolute_airmass(airmass_relative)
    
    # Compute aoi
    aoi = pvlib.irradiance.aoi(location['Latitude'], 180, solarposition['zenith'], 
                               solarposition['azimuth'])
    
    # Compute effective irradiance
    Ee = pvlib.pvsystem.sapm_effective_irradiance(poa, poa_diffuse, airmass_absolute, 
                                                  aoi, sapm_parameters)
    
    # Run SAPM
    sapm_model = pvlib.pvsystem.sapm(Ee, celltemp['temp_cell'], sapm_parameters)
    
    # Compute the relative error between observed and predicted DC Power.  
    # Add the composite signal and run a range test
    modeled_dcpower = sapm_model['p_mp']*sapm_parameters['Ns']*sapm_parameters['Np']
    dc_power_relative_error = np.abs(dcpower - modeled_dcpower)/dcpower
    pm.add_dataframe(dc_power_relative_error.to_frame('DC Power Relative Error'))
    pm.check_range([0,0.1], 'DC Power Relative Error') 
    
    # Compute normalized efficiency, add the composite signal, and run a range test
    P_ref = sapm_parameters['Vmpo']*sapm_parameters['Impo']* \
                sapm_parameters['Ns']*sapm_parameters['Np'] # DC Power rating
    NE = pecos.pv.normalized_efficiency(dcpower, poa, P_ref)
    pm.add_dataframe(NE.to_frame('Normalized Efficiency'))
    pm.check_range([0.8, 1.2], 'Normalized Efficiency') 
    
    # Compute energy
    energy = pecos.pv.energy(acpower, tfilter=pm.tfilter)
    energy = energy.values[0]

    # Compute insolation
    poa_insolation = pecos.pv.insolation(poa, tfilter=pm.tfilter)
    poa_insolation = poa_insolation.values[0]
    
    # Compute performance ratio
    PR = pecos.pv.performance_ratio(energy, poa_insolation, P_ref)
    
    # Compute performance index
    predicted_energy = pecos.pv.energy(modeled_dcpower, tfilter=pm.tfilter)
    predicted_energy = predicted_energy.values[0]
    PI = pecos.pv.performance_index(energy, predicted_energy)
    
    # Compute clearness index
    dni_insolation = pecos.pv.insolation(dni, tfilter=pm.tfilter)
    dni_insolation = dni_insolation.values[0]
    ea = pvlib.irradiance.extraradiation(index.dayofyear)
    ea = pd.Series(index=index, data=ea)
    ea_insolation = pecos.pv.insolation(ea, tfilter=pm.tfilter)
    ea_insolation = ea_insolation.values[0]
    Kt = pecos.pv.clearness_index(dni_insolation, ea_insolation)
    
    # Compute energy yield
    energy_yield = pecos.pv.energy_yield(energy, P_ref)
    
    # Collect metrics for reporting
    metrics = {'Performance Ratio': PR, 
               'Performance Index': PI,
               'Clearness Index': Kt,
               'Total Energy (kWh)': energy/3600/1000, # convert Ws to kWh
               'POA Insolation (kWh/m2)': poa_insolation/3600/1000, # convert Ws to kWh
               'Energy Yield (kWh/kWp)': energy_yield/3600} # convert s to h
    
    return metrics