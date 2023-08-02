"""
The graphics module contains functions to generate scatter, time series, and 
heatmap plots for reports.
"""
import pandas as pd
import numpy as np
try:
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter
except:
    pass
try:
    import plotly
except:
    pass
import textwrap
import os
import logging
import pytest

NoneType = type(None)

logger = logging.getLogger(__name__)

def plot_scatter(x,y,xaxis_min=None, xaxis_max=None, yaxis_min=None, 
                 yaxis_max=None, title=None, figsize=(7.0, 3.0)):
    """
    Create a scatter plot.  If x and y have the same number of columns, then 
    the columns of x are plotted against the corresponding columns of y, in order.
    If x (or y) has 1 column, then that column of data is plotted against all
    the columns in y (or x).
    
    Parameters
    ----------
    x : pandas DataFrame
        X data
    
    y : pandas DataFrame
        Y data
    
    xaxis_min : float, optional
        X-axis minimum, default = None (autoscale)       
        
    xaxis_max : float, optional
        X-axis maximum, default = None (autoscale)
        
    yaxis_min : float, optional
        Y-axis minimum, default = None (autoscale)     
        
    yaxis_max : float, optional
        Y-axis maximum, default = None (autoscale)        
    
    title : string, optional
        Title, default = None
    
    figsize : tuple, optional
        Figure size, default = (7.0, 3.0)
    """
    
    plt.figure(figsize = figsize)
    ax = plt.gca()

    try:
        if x.shape[1] == y.shape[1]:
            for i in range(x.shape[1]):
                plt.plot(x.iloc[:,i],y.iloc[:,i], '.', markersize=3) 
                plt.xticks(rotation='vertical')
        elif x.shape[1] != y.shape[1]:
            if x.shape[1] == 1:
                for col in y.columns:
                    plt.plot(x,y[col], '.', markersize=3) 
                    plt.xticks(rotation='vertical')
            elif y.shape[1] == 1:
                for col in x.columns:
                    plt.plot(x[col],y, '.', markersize=3)
                    plt.xticks(rotation='vertical')
    except:
        plt.text(0.3,0.5,'Insufficient Data', fontsize=8)

    # Format axis
    xmin_plt, xmax_plt = plt.xlim()
    ymin_plt, ymax_plt = plt.ylim()
    if xaxis_min is None:
        xaxis_min = xmin_plt
    if xaxis_max is None:
        xaxis_max = xmax_plt
    if yaxis_min is None:
        yaxis_min = ymin_plt
    if yaxis_max is None:
        yaxis_max = ymax_plt
    plt.xlim((xaxis_min, xaxis_max))
    plt.ylim((yaxis_min, yaxis_max))
    if title:
        plt.title(title)
    ax.tick_params(axis='both', labelsize=8)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0+0.15, box.width, box.height*0.75])

def plot_timeseries(data, tfilter=None, test_results_group=None, xaxis_min=None, 
                    xaxis_max=None, yaxis_min=None, yaxis_max=None, title=None,
                    figsize=(7.0, 3.0), date_formatter=None):
    """
    Create a time series plot using each column in the DataFrame.
    
    Parameters
    ----------
    data : pandas DataFrame or Series
        Data, indexed by time
        
    tfilter : pandas Series, optional
        Boolean values used to include time filter in the plot, default = None 
        
    test_results_group : pandas DataFrame, optional
        Test results for the data
        default = None 
    
    xaxis_min : float, optional
        X-axis minimum, default = None (autoscale)        
        
    xaxis_max : float, optional
        X-axis maximum, default = None (autoscale)    
        
    yaxis_min : float, optional
        Y-axis minimum, default = None (autoscale)            
        
    yaxis_max : float, optional
        Y-axis maximum, default = None (autoscale)
        
    title : string, optional
        Title, default = None
    
    figsize : tuple, optional
        Figure size, default = (7.0, 3.0)
        
    date_formatter : string, optional
        Date formatter used on the x axis, for example, "%m-%d".  Default = None
    """
    
    assert isinstance(data, (pd.Series, pd.DataFrame))
    assert isinstance(tfilter, (NoneType, pd.Series))
    
    plt.figure(figsize = figsize)
    ax = plt.gca()
    
    try:
        # plot time series
        if isinstance(data, pd.Series):
            data.plot(ax=ax, linewidth=0.5, grid=False, legend=False, color='k', 
                      fontsize=8, rot=90, label='Data', x_compat=True)
        else:
            data.plot(ax=ax, linewidth=1, grid=False, legend=False, 
                      fontsize=8, rot=90, label='Data')
    
        if isinstance(tfilter, pd.Series):
            # add tfilter        
            temp = np.where(tfilter - tfilter.shift())
            temp = np.append(temp[0],len(tfilter)-1)
            count = 0
            for i in range(len(temp)-1):
                if tfilter[temp[i]] == 0:
                    if count == 0:
                        ax.axvspan(data.index[temp[i]], data.index[temp[i+1]], 
                                   facecolor='k', alpha=0.2, label='Time filter')
                        count = count+1
                    else:
                        ax.axvspan(data.index[temp[i]], data.index[temp[i+1]], 
                                   facecolor='k', alpha=0.2)     
        
        # add errors 
        try:
            if test_results_group.empty:
                test_results_group = None
        except:
            pass
        if test_results_group is not None:
            key2 = test_results_group['Error Flag'].fillna('')
            grouped2 = test_results_group.groupby(key2)
            
            for error_flag in key2.unique():
                test_results_group2 = grouped2.get_group(error_flag)
                
                error_label = '\n'.join(textwrap.wrap(error_flag, 30))
                if len(test_results_group2.index.values) > 4:
                    warning_label = '\n'.join(textwrap.wrap('Warning ' + 
                        str(test_results_group2.index.values[0:4]).strip('[]') + '...', 30))
                else:
                    warning_label = '\n'.join(textwrap.wrap('Warning ' + 
                        str(test_results_group2.index.values).strip('[]'), 30))
                error_label = error_label + '\n' + warning_label
                
                date_idx2 = np.array([False]*len(data.index))
                for row2 in range(len(test_results_group2.index)):
                    s_index = test_results_group2.columns.get_loc("Start Time")
                    e_index = test_results_group2.columns.get_loc("End Time")
                    date_idx2 = date_idx2 + ((data.index >= test_results_group2.iloc[row2,s_index]) & 
                                             (data.index <= test_results_group2.iloc[row2,e_index]))
                
                if sum(date_idx2) == 0:
                    continue
                
                data2 = data[date_idx2]
                if error_flag in ['Duplicate timestamp', 'Missing data', 
                                  'Corrupt data', 'Nonmonotonic timestamp']:
                    continue
                #if "Data" in error_flag:
                #    color='r'
                #elif "Delta" in error_flag:
                #    color = 'g'
                #else: # Outlier
                #    color = 'b'
                try:
                    ax.scatter(data2.index, data2.values, marker='+', # c=color,
                               linewidths=1, label=error_label)   
                except:
                    ax.scatter(data2.index[0], data2.values[0], marker='+', # c=color,
                               linewidths=1, label=error_label) 
        
        # Format axis
        xmin_plt, xmax_plt = plt.xlim()
        ymin_plt, ymax_plt = plt.ylim()
        if tfilter is not None:
            ymin_plt = np.nanmin(data[tfilter].values)
            ymax_plt = np.nanmax(data[tfilter].values)
        if np.abs(ymin_plt - ymax_plt) < 0.01:
            ymin_plt, ymax_plt = plt.ylim()
    except:
        plt.text(0.3,0.5,'Insufficient Data', fontsize=8)
        xmin_plt, xmax_plt = plt.xlim()
        ymin_plt, ymax_plt = plt.ylim()
    
    # Format axis
    y_range = (ymax_plt - ymin_plt)
    if xaxis_min is None:
        xaxis_min = xmin_plt
    if xaxis_max is None:
        xaxis_max = xmax_plt
    if yaxis_min is None:
        yaxis_min = ymin_plt-y_range/10
    if yaxis_max is None:
        yaxis_max = ymax_plt+y_range/10
    plt.xlim((xaxis_min, xaxis_max))
    plt.ylim((yaxis_min, yaxis_max))
    if title:
        plt.title(title)
    ax.get_yaxis().get_major_formatter().set_useOffset(False)
    ax.tick_params(axis='both', labelsize=8)
    plt.xlabel('Time', fontsize=8)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0+0.15, box.width, box.height*0.75])
    
    if date_formatter is not None:
        date_form = DateFormatter(date_formatter)
        ax.xaxis.set_major_formatter(date_form)

def plot_interactive_timeseries(data, xaxis_min=None, xaxis_max=None, yaxis_min=None, 
                 yaxis_max=None, title=None, filename=None, auto_open=True):
    """
    Create a basic interactive time series graphic using plotly.  Many more 
    options are available, see https://plot.ly for more details.
    
    Parameters
    ----------
    data : pandas DataFrame
        Data, indexed by time
    
    xaxis_min : float, optional
        X-axis minimum, default = None (autoscale)       
        
    xaxis_max : float, optional
        X-axis maximum, default = None (autoscale)
        
    yaxis_min : float, optional
        Y-axis minimum, default = None (autoscale)     
        
    yaxis_max : float, optional
        Y-axis maximum, default = None (autoscale)        
    
    title : string, optional
        Title, default = None
        
    filename : string, optional
        HTML file name, default = None (file will be named temp-plot.html)
    
    auto_open : boolean, optional
        Flag indicating if HTML graphic is opened, default = True
    """
    
    layout = dict(hovermode = 'closest')
    layout = dict(title=title, hovermode = 'closest',
                  xaxis=dict(range=[xaxis_min,xaxis_max]),
                  yaxis=dict(range=[yaxis_min,yaxis_max]))
    plotly_data = []
    for col in data.columns:
        trace = plotly.graph_objs.Scatter(x=data.index.tz_localize(None), 
                                          y=data.loc[:,col], name = col)
        plotly_data.append(trace)
    fig = dict(data=plotly_data, layout=layout)
    if filename:
        plotly.offline.plot(fig, filename=filename, auto_open=auto_open)  
    else:
        plotly.offline.plot(fig, auto_open=auto_open)  
        
def plot_heatmap(data, colors=None, nColors=12, cmap=None, vmin=None, vmax=None, 
                 show_axis=False, title=None, figsize=(5.0, 5.0)): 
    """ 
    Create a heatmap.  Default color scheme is red to yellow to green with 12 
    colors.  This function can be used to generate dashboards with simple color 
    indicators in each cell (to remove borders use bbox_inches='tight' and 
    pad_inches=0 when saving the image).
    
    Parameters
    -----------
    data : pandas DataFrame, pandas Series, or numpy array
        Data
    
    colors : list or None, optional
        List of colors, colors can be specified in any way understandable by 
        matplotlib.colors.ColorConverter.to_rgb().
        If None, colors transitions from red to yellow to green.
    
    num_colors : int, optional
        Number of colors in the colormap, default = 12
        
    cmap : string, optional
        Colormap, default = None. Overrides colors and num_colors listed above.
        
    vmin : float, optional
        Colomap minimum, default = None (autoscale) 
    
    vmax : float, optional
        Colomap maximum, default = None (autoscale) 
    
    title : string, optional
        Title, default = None
    
    figsize : tuple, optional
        Figure size, default = (5.0, 5.0)
    """
    if colors is None:
        colors = [(0.75, 0.15, 0.15), (1, 0.75, 0.15), (0.15, 0.75, 0.15)]
        
    if isinstance(data, (pd.DataFrame, pd.Series)):
        data = data.values
    if len(data.shape) == 1:
        data = np.expand_dims(data, axis=0)
        
    if not cmap:
        from matplotlib.colors import LinearSegmentedColormap
        cmap = LinearSegmentedColormap.from_list(name='custom', colors=colors, N=nColors)
    
    plt.figure(figsize = figsize)
    fig = plt.imshow(data, cmap=cmap, aspect='equal', vmin=vmin, vmax=vmax)
    if not show_axis:
        plt.axis('off')
        fig.axes.get_xaxis().set_visible(False)
        fig.axes.get_yaxis().set_visible(False)
    if title:
        plt.title(title)
    plt.tight_layout()

def plot_doy_heatmap(data, cmap='nipy_spectral', vmin=None, vmax=None, 
                     overlay=None, title=None, figsize=(7.0, 3.0)):
    """
    Create a day-of-year (X-axis) vs. time-of-day (Y-axis) heatmap.
    
    Parameters
    ----------
    data : pandas DataFrame or pandas Series
        Data (single column), indexed by time
        
    cmap : string, optional
        Colomap, default = nipy_spectral
        
    vmin : float, optional
        Colomap minimum, default = None (autoscale)
    
    vmax : float, optional
        Colomap maximum, default = None (autoscale)
        
    overlay : pandas DataFrame, optional
        Data to overlay on the heatmap.  
        Time index should be in day-of-year (X-axis) 
        Values should be in time-of-day in minutes (Y-axis)
    
    title : string, optional
        Title, default = None
        
    figsize : tuple, optional
        Figure size, default = (7.0, 3.0)
    """
    
    if type(data) is pd.core.series.Series:
        data = data.to_frame()
            
    # Convert data to a pivot table
    col_name = data.columns[0]
    data['X'] = data.index.dayofyear
    data['Y'] = data.index.hour*60 + \
                data.index.minute + \
                data.index.second/60 + \
                data.index.microsecond/(60*1000000.0)
    piv = pd.pivot_table(data,values=col_name,index=['Y'],columns=['X'],fill_value=np.NaN)
    
    # Create the heatmap
    plt.figure(figsize = figsize)
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(piv, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax,
                   extent=[data['X'].min()-0.5,data['X'].max()+0.5, 
                           data['Y'].max()-0.5,data['Y'].min()+0.5])
    fig.colorbar(im, ax=ax)
    
    # Add overlay
    if type(overlay) is pd.core.frame.DataFrame:
        overlay.plot(ax=ax)
        
    # Add title and labels
    if title:
        ax.set_title(title)
    ax.set_xlabel("Day of the year")
    ax.set_ylabel("Time of day (minutes)")
    plt.tight_layout()
    
@pytest.mark.skip()
def plot_test_results(data, test_results, tfilter=None, image_format='png', 
                      dpi=500, figsize=(7.0,3.0), date_formatter=None, 
                      filename_root='test_results'):
    """
    Create test results graphics which highlight data points that
    failed a quality control test.

    Parameters
    ----------
    data : pandas DataFrame
        Data, indexed by time (pm.data)
        
    test_results : pandas DataFrame
        Summary of the quality control test results (pm.test_results)
    
    tfilter : pandas Series, optional
        Boolean values used to include time filter in the plot, default = None 
        
    image_format : string , optional
        Image format, default = 'png'
    
    dpi : int, optional
        DPI resolution, default = 500
        
    figsize : tuple, optional
        Figure size, default = (7.0,3.0)
    
    date_formatter : string, optional
        Date formatter used on the x axis, for example, "%m-%d".  Default = None
    
    filename_root : string, optional
        File name root. If the full path is not provided, files are saved into the 
        current working directory. Each graphic filename is appended with an integer.
        For example, filename_root = 'test' will generate a files named 'test0.png', 
        'test1.png', etc. By default, the filename root is 'test_results'
    
    Returns
    ----------
    A list of file names
    """
    if os.path.dirname(filename_root) == '':
        full_filename_root = os.path.join(os.getcwd(), filename_root)
    else:
        full_filename_root = os.path.abspath(filename_root)
    
    # Colect file names
    test_results_graphics = []
    
    if test_results.empty:
        return test_results_graphics

    graphic = 0
    
    test_results.sort_values(list(test_results.columns), inplace=True)
    test_results.index = np.arange(1, test_results.shape[0]+1)
    
    # Remove specific error flags
    remove_error_flags = ['Duplicate timestamp', 
                          'Missing data', 
                          'Corrupt data', 
                          'Missing timestamp', 
                          'Nonmonotonic timestamp']
    test_results = test_results[-test_results['Error Flag'].isin(remove_error_flags)]
    grouped = test_results.groupby('Variable Name')

    for col_name, test_results_group in grouped:
        logger.info("Creating graphic for " + col_name)
        
            
        plot_timeseries(data[col_name], tfilter, 
                        test_results_group=test_results_group, figsize=figsize,
                        date_formatter=date_formatter)

        ax = plt.gca()
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width*0.65, box.height])
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
        plt.title(col_name, fontsize=8)
        
        filename = full_filename_root + str(graphic) + '.' + image_format
        test_results_graphics.append(filename)
        plt.savefig(filename, format=image_format, dpi=dpi)
            
        graphic = graphic + 1
        plt.close()

    return test_results_graphics
