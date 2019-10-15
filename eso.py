import sys
import os
import glob as gb
import sqlite3
import pandas as pd







def open_eso(file):
    with open(file, 'r') as f:
        flist = f.readlines()
    return flist

def get_data_dict(flist):
    data_dict = []
    for f in flist:
        if "End of Data Dictionary" in f:
            break
        data_dict.append(f)
    return data_dict
    
    
def parse_header(header):
    rpt_dict = {}
    header = header.replace('\n','')
    right = header.split('!')[1]
    period = right.split(' ')[0]
    left = header.split('!')[0]
    leftsplit = left.split(',')
    idx = leftsplit[0]
    p_type = leftsplit[1]

    if len(leftsplit) > 3:
        keyvalue = leftsplit[2]
        name = leftsplit[3]
    else:
        keyvalue = leftsplit[2]
        name = ''
    name_clean = keyvalue + ', ' + name
    return [name_clean, period, keyvalue, name, p_type, idx]#, right]


def get_avail_series(file):
    flist = open_eso(file)
    data_dict = get_data_dict(flist)
    dflist = []
    for d in data_dict[7:]:
        series = parse_header(d)
        dflist.append(series)
    df = pd.DataFrame(dflist)
    df.columns = ['series_name', 'rpt_period', 'keyvalue', 'name', 'period_type', 'rpt_idx']#, 'leftover']
    return df
    
   

def get_series(idx, flist, data_dict_df):    
    seriesarray = [[b.replace('\n','') for b in f.split(',')] for f in flist if f.split(',')[0] == str(idx)]
    info = data_dict_df[data_dict_df.rpt_idx == str(idx)]
    singlearray = [s[1:] for s in seriesarray[1:]]
    return info, singlearray
                  
    
def array_to_df(array):
    info, data = array
    coldict = { 
        'Hourly': ['Value'],
        'Daily': ['Value','Min','Hour','Minute','Max','Hour','Minute'],
        'Monthly': ['Value','Min','Day','Hour','Minute','Max','Day','Hour','Minute'],
        'RunPeriod': ['Value','Min','Month','Day','Hour','Minute','Max','Month','Day','Hour','Minute'],
        }
    
    period = info.rpt_period.tolist()[0]
    dfcolumns = coldict[period]
    df = pd.DataFrame(data)
    df.columns = dfcolumns
    return info, df



def multi_index_df(info, df):
    cols = info.values.tolist()[0]
    rows = df.columns.tolist()
    multi_rows = []
    for row in rows:
        multi_rows.append(tuple(cols + [row]))
    multi = pd.MultiIndex.from_tuples(multi_rows)
    df.columns = multi
    return df







class ReadEso:
    def __init__(self, file):
        self.reports = get_avail_series(file)
        self.file = file
    
    def get_report(self, idx):
        flist = open_eso(self.file)
        data_dict_df = self.reports
        array = get_series(idx, flist, data_dict_df)
        info, df = array_to_df(array)
        df = multi_index_df(info, df)
        return df
        
