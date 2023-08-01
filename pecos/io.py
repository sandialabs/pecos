"""
The io module contains functions to read/send data and write results to 
files/html reports.
"""
import pandas as pd
import numpy as np
import logging
import os
from os.path import abspath, dirname, join
import pecos.graphics
import datetime
from jinja2 import Environment, PackageLoader
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import base64

try:
    from sqlalchemy import create_engine
    import minimalmodbus 
except:
    pass
import pytest

        
logger = logging.getLogger(__name__)

env = Environment(loader=PackageLoader('pecos', 'templates'))

def read_campbell_scientific(filename, index_col='TIMESTAMP', encoding=None):
    """
    Read Campbell Scientific CSV file.

    Parameters
    ----------
    filename : string
        File name

    index_col : string, optional
        Index column name, default = 'TIMESTAMP'

    encoding : string, optional
        Character encoding (i.e. utf-16)
    
    Returns
    ---------
    pandas DataFrame
        Data
    """
    logger.info("Reading Campbell Scientific CSV file " + filename)

    try:
        df = pd.read_csv(filename, skiprows=1, encoding=encoding, index_col=index_col, 
                         parse_dates=True, dtype ='unicode', on_bad_lines="skip") #, low_memory=False)
        df = df[2:]
        index = pd.to_datetime(df.index)
        Unnamed = df.filter(regex='Unnamed')
        if Unnamed.columns.shape[0] > 0:
            df = df.drop(Unnamed.columns, 1)
        df = pd.DataFrame(data = df.values, index = index, columns = df.columns, dtype='float64')
    except:
        logger.warning("Cannot extract database, CSV file reader failed " + filename)
        df = pd.DataFrame()
        return

    # Drop rows with NaT (not a time) in the index
    try:
        df.drop(pd.NaT, inplace=True)
    except:
        pass

    return df
    
def send_email(subject, body, recipient, sender, attachment=None, 
               host='localhost', username=None, password=None):
    """
    Send email using Python smtplib and email packages.
    
    Parameters
    ----------
    subject : string
        Subject text
        
    body : string
        Email body, in HTML or plain format
    
    recipient : list of string
        Recipient email address or addresses
    
    sender : string
        Sender email address
        
    attachment : string, optional
        Name of file to attach
        
    host : string, optional
        Name of email host (or host:port), default = 'localhost'
    
    username : string, optional
        Email username for authentication
    
    password : string, optional
        Email password for authentication
    """
    
    logger.info("Sending email")
    
    msg = _create_email_message(subject, body, recipient, sender)
    
    if attachment is not None:
        fp = open(attachment, "rb")  # Read as a binary file, even if it's text  
        att = MIMEApplication(fp.read())
        att.add_header('Content-Disposition', 'attachment', 
                       filename=os.path.basename(attachment))
        fp.close()
        msg.attach(att)
    
    s = smtplib.SMTP(host)
    try: # Authentication
        s.ehlo()
        s.starttls()
        s.login(username, password)
    except:
        pass
    s.sendmail(sender, recipient, msg.as_string())
    s.quit()
    
def _create_email_message(subject, body, recipient, sender):
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = ', '.join(recipient)
    msg['From'] = sender
    
    if "</html>" in body.lower():
        content = MIMEText(body, 'html')
    else:
        content = MIMEText(body, 'plain')
    
    msg.attach(content)
    
    return msg
        
def write_metrics(metrics, filename='metrics.csv'):
    """
    Write metrics file.
    
    Parameters
    -----------
    metrics : pandas DataFrame
        Data to add to the metrics file
    
    filename : string, optional
        File name.  If the full path is not provided, the file is saved into the 
        current working directory. By default, the file is named 'metrics.csv'
    
    Returns
    ------------
    string
        filename
    """
    logger.info("Write metrics file")

    try:
        previous_metrics = pd.read_csv(filename, index_col='TIMESTEP', parse_dates=True)
    except:
        previous_metrics = pd.DataFrame()
        
    #metrics.index = metrics.index.to_native_types() # no longer needed when using time zones
    metrics = metrics.combine_first(previous_metrics) 
    
    if os.path.dirname(filename) == '':
        full_filename = os.path.join(os.getcwd(), filename)
    else:
        full_filename = filename
    fout = open(full_filename, 'w')
    metrics.to_csv(fout, index_label='TIMESTEP', na_rep = 'NaN')
    fout.close()
    
    return full_filename

@pytest.mark.skip()
def write_test_results(test_results, filename='test_results.csv'):
    """
    Write test results file.

    Parameters
    -----------
    test_results : pandas DataFrame
        Summary of the quality control test results (pm.test_results)
    
    filename : string, optional
        File name.  If the full path is not provided, the file is saved into the 
        current working directory. By default, the file is named 'test_results.csv'
    
    Returns
    ------------
    string
        filename
    """

    test_results.sort_values(list(test_results.columns), inplace=True)
    test_results.index = np.arange(1, test_results.shape[0]+1)

    logger.info("Writing test results csv file " + filename)
    
    if os.path.dirname(filename) == '':
        full_filename = os.path.join(os.getcwd(), filename)
    else:
        full_filename = filename
    fout = open(full_filename, 'w')
    test_results.to_csv(fout, na_rep = 'NaN')
    fout.close()
    
    return full_filename

def write_monitoring_report(data, test_results, test_results_graphics=None, 
                            custom_graphics=None, metrics=None, 
                            title='Pecos Monitoring Report', config=None, logo=False, 
                            im_width_test_results=1, im_width_custom=1, im_width_logo=0.1,
                            encode=False, file_format='html',
                            filename='monitoring_report.html'):
    """
    Generate a monitoring report.  
    The monitoring report is used to report quality control test results for a single system.
    The report includes custom graphics, performance metrics, and test results.
    
    Parameters
    ----------
    data : pandas DataFrame
        Data, indexed by time (pm.data)
        
    test_results : pandas DataFrame
        Summary of the quality control test results (pm.test_results)
        
    test_results_graphics : list of strings or None, optional
        Graphics files, with full path.  These graphics highlight data points 
        that failed a quality control test, created using pecos.graphics.plot_test_results().
        If None, test results graphics are not included in the report.
        
    custom_graphics : list of strings or None, optional
        Custom files, with full path.  Created by the user.
        If None, custom graphics are not included in the report.
    
    metrics : pandas Series or DataFrame, optional
        Performance metrics to add as a table to the monitoring report
    
    title : string, optional
        Monitoring report title, default = 'Pecos Monitoring Report'
        
    config : dictionary or None, optional
        Configuration options, to be printed at the end of the report.
        If None, configuration options are not included in the report.
    
    logo : string, optional
        Graphic to be added to the report header
    
    im_width_test_results : float, optional
        Image width as a fraction of page size, for test results graphics, default = 1
    
    im_width_custom : float, optional
        Image width as a fraction of page size, for custom graphics, default = 1
        
    im_width_logo: float, optional
        Image width as a fraction of page size, for the logo, default = 0.1
        
    encode : boolean, optional
        Encode graphics in the html, default = False
    
    filename : string, optional
        File name.  If the full path is not provided, the file is saved into the 
        current working directory. By default, the file is named 'monitoring_report.html'
        
    Returns
    ------------
    string
        filename
    """
    logger.info("Writing HTML report")
    
    if test_results_graphics is None:
        test_results_graphics = []
    if custom_graphics is None:
        custom_graphics = []
    if config is None:
        config = {}
        
    if data.empty:
        logger.warning("Empty database")
        start_time = 'NaN'
        end_time = 'NaN'
    else:
        start_time = data.index[0]
        end_time = data.index[-1]
    
    # Set pandas display option     
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 40)
    
    # Collect notes (from the logger file)
    try:
        logfiledir = os.path.join(dirname(abspath(__file__)))
        f = open(join(logfiledir,'logfile'), 'r')
        notes = f.read()
        f.close()
        notes_df = pd.DataFrame(notes.splitlines())
        notes_df.index += 1
    except:
        notes_df = pd.DataFrame()
    
    test_results.sort_values(list(test_results.columns), inplace=True)
    test_results.index = np.arange(1, test_results.shape[0]+1)
    
    # Convert to html format
    if metrics is None:
        metrics = pd.DataFrame()
    
    content = {'start_time': str(start_time), 
               'end_time': str(end_time), 
               'num_notes': str(notes_df.shape[0]),
               'num_data_columns': str(data.shape[1]),
               'num_test_results': str(test_results.shape[0]),
               'num_metrics': str(metrics.shape[0]),
               'config': config}
                
    title = os.path.basename(title)
    
    if file_format == 'html':
        content['test_results_graphics'] = test_results_graphics
        content['custom_graphics'] = custom_graphics
        
        if isinstance(metrics, pd.Series):
            metrics_html = metrics.to_frame().to_html(header=False)
        if isinstance(metrics, pd.DataFrame):  
            metrics_html = metrics.to_html(justify='left')
            
        content['metrics'] = metrics_html    
        content['test_results'] = test_results.to_html(justify='left')
        content['notes'] = notes_df.to_html(justify='left', header=False)
        
        im_width_test_results = im_width_test_results*800
        im_width_custom = im_width_custom*800
        im_width_logo = im_width_logo*800
        
        file_string = _html_template_monitoring_report(content, title, logo, 
                            im_width_test_results, im_width_custom, im_width_logo, encode)
    else:
        test_results_graphics = [g.replace('\\', '/') for g in test_results_graphics]
        custom_graphics = [g.replace('\\', '/') for g in custom_graphics]
        
        content['test_results_graphics'] = test_results_graphics
        content['custom_graphics'] = custom_graphics
        
        content['metrics'] = metrics.to_latex(longtable=True)
        content['test_results'] = test_results.to_latex(longtable=True)
        content['notes'] = notes_df.to_latex(longtable=True)
        
        file_string = _latex_template_monitoring_report(content, title, logo, 
                            im_width_test_results, im_width_custom, im_width_logo)
    
    # Write file
    if os.path.dirname(filename) == '':
        full_filename = os.path.join(os.getcwd(), filename)
    else:
        full_filename = filename
    fid = open(full_filename,"w")
    fid.write(file_string)
    fid.close()
    
    logger.info("")
    
    return full_filename
    
def write_dashboard(column_names, row_names, content, title='Pecos Dashboard', 
                    footnote='', logo=False, im_width=250, datatables=False, 
                    encode=False, filename='dashboard.html'):
    """
    Generate a dashboard.  
    The dashboard is used to compare results across multiple systems.
    Each cell in the dashboard includes custom system graphics and metrics.
    
    Parameters
    ----------
    column_names : list of strings
        Column names listed in the order they should appear in the dashboard, 
        i.e. ['location1', 'location2']
        
    row_names : list of strings
        Row names listed in the order they should appear in the dashboard, 
        i.e. ['system1', 'system2']
        
    content : dictionary
        Dashboard content for each cell. 
        Dictionary keys are tuples indicating the row name and column name, 
        i.e. ('row name', 'column name'), where 'row name' is in the list 
        row_names and 'column name' is in the list column_names. 
        
        For each ('row name', 'column name') key, another dictionary is defined 
        that contains the content to be included in each cell of the dashboard. 
        Each cell can contain text, graphics, a table, and an html link. These 
        are defined using the following **case sensitive** keys:
        
        - **text** (string) =  text at the top of each cell
        - **graphics** (list of strings) =  a list of graphics file names.  Each 
          file name includes the full path
        - **table** (string) = a table in html format, for example a table of 
          performance metrics.  DataFrames can be converted to an html string 
          using df.to_html() or df.transpose().to_html().  Values in the table 
          can be color coded using pandas Styler class. 
        - **link** (dict) = a dictionary where keys define the name of the link 
          and values define the html link (with full path)
        
        For example::
        
            content = {('row name', 'column name'): {
                'text': 'text at the top', 
                'graphic': ['C:\\\\pecos\\\\results\\\\custom_graphic.png'], 
                'table': df.to_html(), 
                'link': {'Link to monitoring report': 'C:\\\\pecos\\\\results\\\\monitoring_report.html'}}
        
    title : string, optional
        Dashboard title, default = 'Pecos Dashboard'
    
    footnote : string, optional
        Text to be added to the end of the report
    
    logo : string, optional
        Graphic to be added to the report header
    
    im_width : float, optional
        Image width in the HTML report, default = 250
        
    datatables : boolean, optional
        Use datatables.net to format the dashboard, default = False.  
        See https://datatables.net/ for more information.
    
    encode : boolean, optional
        Encode graphics in the html, default = False
    
    filename : string, optional
        File name.  If the full path is not provided, the file is saved into the 
        current working directory. By default, the file is named 'dashboard.html'
    
    Returns
    ------------
    string
        filename
    """
    
    logger.info("Writing dashboard")
        
    # Set pandas display option     
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', 40)
    
    html_string = _html_template_dashboard(column_names, row_names, content, 
                                           title, footnote, logo, im_width, 
                                           datatables, encode)
    
    # Write html file
    if os.path.dirname(filename) == '':
        full_filename = os.path.join(os.getcwd(), filename)
    else:
        full_filename = filename
    html_file = open(full_filename,"w")
    html_file.write(html_string)
    html_file.close()
    
    logger.info("")

    return full_filename

def _latex_template_monitoring_report(content, title, logo, im_width_test_results, 
                                      im_width_custom, im_width_logo):
    
    template = env.get_template('monitoring_report.tex')

    date = datetime.datetime.now()
    datestr = date.strftime('%m/%d/%Y')
    
    version = pecos.__version__
    
    return template.render(**locals())

def _html_template_monitoring_report(content, title, logo, im_width_test_results, 
                                     im_width_custom, im_width_logo, encode):
    
    # if encode == True, encode the images
    img_dic = {}
    if encode:
        for im in content['custom_graphics']:
            img_encode = base64.b64encode(open(im, "rb").read()).decode("utf-8")
            img_dic[im] = img_encode
        for im in content['test_results_graphics']:
            img_encode = base64.b64encode(open(im, "rb").read()).decode("utf-8")
            img_dic[im] = img_encode

    template = env.get_template('monitoring_report.html')

    date = datetime.datetime.now()
    datestr = date.strftime('%m/%d/%Y')
    
    version = pecos.__version__
    
    return template.render(**locals())

def _html_template_dashboard(column_names, row_names, content, title, footnote, 
                             logo, im_width, datatables, encode):
    
    # if encode == True, encode the images
    img_dic = {}
    if encode:
        for column in column_names:
            for row in row_names:
                try: # not all row/columns have graphics
                    for im in content[row, column]['graphics']:
                       img_encode = base64.b64encode(open(im, "rb").read()).decode("utf-8")
                       img_dic[im] = img_encode 
                except:
                    pass
    
    template = env.get_template('dashboard.html')

    date = datetime.datetime.now()
    datestr = date.strftime('%m/%d/%Y')

    version = pecos.__version__

    return template.render(**locals())

def device_to_client(config):
    """
    Read channels on modbus device, scale and calibrate the values, and store 
    the data in a MySQL database. The inputs are provided by a configuration 
    dictionary that describe general information for data acquisition and the 
    devices.
    
    Parameters
    ----------
    config : dictionary
        Configuration options, see :ref:`devicetoclient_config`
    """ 
    
    # Extract Database Information
    sec0 = float(datetime.datetime.now().strftime('%s'))
    while True: 
        logging.info('Device to client: '+str(datetime.datetime.now()))
        sec1 = float(datetime.datetime.now().strftime('%s'))
        if sec1 - sec0 >= config['Client']['Interval']:
            run = True
            sec0 = sec1
        else:
            run = False
        
        if run:
            dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            labels,dall = [],[]
            retry = config['Client']['Retries']
            for device in config['Devices']:
                # Read channels on modbus device 
                instr = minimalmodbus.Instrument(device['USB'],device['Address'])
                instr.serial.baudrate = device['Baud']
                instr.serial.bytesize = device['Bytes']
                instr.serial.stopbits = device['Stopbits']
                instr.serial.parity = device['Parity']
                
                ds,ls = [],[]
                for data in device['Data']:
                    i = 0
                    while i < retry:
                        l = data['Name']
                        try:
                            d = instr.read_register(data['Channel'], 
                            						numberOfDecimals=data['Scale'], 
                            						functioncode=data['Fcode'], 
                            						signed=data['Signed']) * data['Conversion']
                            break
                        except:
                            if i == retry-1:
                                d = np.nan
                            else:
                                pass
                        i += 1

                    ds.append(d)
                    ls.append(l) 
                
                dall.extend(ds)
                labels.extend(ls)  

            # Add datetime to collected channel values and labels
            dall.extend([dt])
            labels.extend(['datetime'])
            logging.info(ds)
  
            # Convert collected data into pandas DataFrame format
            df = pd.DataFrame(dall).T
            df.columns = labels
            df = df.where((pd.notnull(df)),None)

            # Insert data into database 
            try:
                # Connect to database
                engine = create_engine('mysql://'+config['Client']['Username']+ \
                                       ':'+config['Client']['Password']+'@'+ \
                                        config['Client']['IP']+'/'+ \
                                        config['Client']['Database'])	
                # Write DataFrame to database
                df.to_sql(name=config['Client']['Table'],con=engine, 
                          if_exists='append', index=False) #,dtype = data_type)		
            except:
                pass
