import sys
import os
import glob as gb
import sqlite3
import pandas as pd




class SqlSeries:
    '''creates table from available sql output reports.
    args:
        sqlfile: sqlfile path
        tablename = i.e. "Comfort and Setpoint Not Met Summary"
        reportname (optional): for specifying reportname if there are more than identically-named tables in multiple reports'''
    def __init__(self, sqlfile):
        if ".sql" not in sqlfile:
            sqlfile = sqlfile + '.sql'
            bndfile = sqlfile + '.bnd'

        self.sqlfile = sqlfile
        self.bndfile = sqlfile.replace(".sql",".bnd")
        self.simname = sqlfile.replace(".sql","")


    # private/helper functions (do i need the ones hashed out??)
    # def _df_cols_to_dict(self, df, keycol, valcol):
    #     '''takes dataframe and makes key:val dict out of columns'''
    #     return pd.Series(df[valcol].values, index=df[keycol].values).to_dict()

    # def _idx_to_str(self, tabledf, stringdict, lookup_col):
    #     '''takes any col w/ "Index" and adds associated string'''
    #     string_col = lookup_col.replace("Index","")
    #     if string_col == lookup_col:
    #         raise ValueError("Lookup Col str has to have 'Index' in it")
    #     tabledf[string_col] = tabledf[lookup_col].apply(lambda x: stringdict[x])
    #     return tabledf


    def _bnd_node_dict(self):
            with open(self.bndfile, 'r') as f:
                bndlist = f.readlines()
            
            bndsplit = [x.replace("\n","").split(",") for x in bndlist]
            
            
            nodedict = {}
            for b in bndsplit:
                if b[0].upper().replace(" ","") == "NODE" or b[0].upper().replace(" ","") == " SUSPICIOUSNODE":
                    nodedict[b[2]] = b[3]
            return nodedict


    def _conv_units(self, df):
        bnd_node_dict = self._bnd_node_dict()


        convdict = {
                'Air': {
                    'factor': {
                        'm3/s':2118
                        },
                    'units': {
                        'm3/s': 'cfm'
                        }
                },
                'Water': {
                    'factor': {
                        'm3/s':15850
                        },
                    'units': {
                        'm3/s':'gpm'
                        }
                },
                'neutral': {
                    'factor': {
                        'J': 0.000277778,
                        'grain/lb':7000,
                        'kg/s': 2.2,
                        'W': 3.412,
                        'C': '1.8x+32',
                        'kg': 2.2,
                        'm/s': 1.328084,
                        'W/m2': 10.7639,
                        'Pa': 0.000145038,
                        'hr': 1,
                        'ach': 1,
                        '%': 1,
                        },
                    'units': {
                        'J': 'W',
                        'grain/lb':'lb/lb',
                        'kg/s': 'lb/s',
                        'W': 'btu',
                        'C': 'F',
                        'kg': 'lb',
                        'hr': 'hr',
                        'deg': 'deg',
                        'm/s': 'ft/s',
                        'W/m2': 'W/ft2',
                        'Pa': 'psi',
                        'hr': 'hr',
                        'ach': 'ach',
                        '%': '%',
                    
                        }
                }
            }

        df = df.copy()
        unitlist = []
        for col in df.columns:
            name = col[-2]
            unit = col[-1]
            keyval = col[-3]

            try:
                fname = bnd_node_dict[keyval]
                fconv = convdict[fname]['factor'][unit]
                funit = convdict[fname]['units'][unit]

                if fconv != '1.8x+32':
                    df[col] = df[col].apply(lambda x: x * fconv)                

            except:

                if unit in convdict['neutral']['units'].keys():
                    fname = 'neutral'
                    fconv = convdict['neutral']['factor'][unit]
                    funit = convdict[fname]['units'][unit]
                    
                if unit == '':
                    fname = 'neutral'
                    fconv = 1
                    funit = ''

                if "AIR" in name.upper() or keyval.upper() in 'AIR OUTLET' or keyval.upper() in 'AIR INLET':
                    fname = 'Air'
                    try:
                        funit = convdict[fname]['units'][unit]
                    except:
                        pass
                    
                if 'WATER' in name.upper() or keyval.upper() in 'WATER OUTLET' or keyval.upper() in 'WATER INLET':
                    fname = 'Water'
                    try:
                        funit = convdict[fname]['units'][unit]
                    except:
                        pass

                if unit == 'C':
                    df[col] = df[col].apply(lambda x: (x * 1.8) + 32)
                    funit = 'F'

                if fconv != '1.8x+32':
                    df[col] = df[col].apply(lambda x: x * fconv)
                    
            unitlist.append(funit)
        
        convcols = [list(elem) for elem in df.columns]

        newconvcols = []
        for num, conv in enumerate(convcols):

            newlist = conv[:-1] + [unitlist[num]]
            newconvcols.append(newlist)

        newconvcols = list(map(list, zip(*newconvcols)))
        idx = pd.MultiIndex.from_arrays(newconvcols)
        
        df.columns = idx

        try:
            df.drop('TimeIndex', axis=1, inplace=True)
        except:
            pass

        return df



    def _df_query(self, query):
        '''opens sql, makes query (native sql), closes sql and returns df'''
        conn = sqlite3.connect(self.sqlfile)
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def _df_to_tabledict(self, df):
        '''takes dataframe populated from either "_filter_tabular" or "avail_tabular" and returns list of dicts for "get_tabular"'''
        ziplist = list(zip(df['ReportName'].values.tolist(), df['ReportForString'].values.tolist(), df['TableName'].values.tolist()))
        zipdict = [{
            'ReportName': z[0],
            'ReportForString': z[1],
            'TableName': z[2]
        } for z in ziplist]
        return zipdict


    def _filter_tabular(self, filterquery):
        '''search available tabulardata for any string, return dataframe'''
        avail = self.availseries()
        df = avail[avail.apply(lambda row: row.astype(str).str.contains(filterquery).any(), axis=1)]
        return df


    def _maketime(self):
        timedf = self._df_query("SELECT * FROM Time WHERE Interval = 60")
        def zeropad(val):
            if len(str(val)) == 1:
                val = '0' + str(val)
                return val
            else:
                return val

        timedf['Hour'] = timedf['Hour']-1
        timedf['Month'] = timedf['Month'].apply(lambda x: zeropad(x))
        timedf['Day'] = timedf['Day'].apply(lambda x: zeropad(x))
        timedf['Hour'] = timedf['Hour'].apply(lambda x: zeropad(x))
        timedf['dt'] =  timedf['Month'].astype(str) + "-" + timedf['Day'].astype(str)  + "-" + timedf['Hour'].astype(str)
        dtformat = "%m-%d-%H"
        timedf['dt'] = pd.to_datetime(timedf['dt'], format=dtformat, errors='ignore')
        return timedf


    ## public functions
    def availseries(self):
        rddcols = [
                'ReportDataDictionaryIndex',
                'IsMeter', 
                'Type', 	
                'IndexGroup',
                'TimestepType',
                'KeyValue',
                'Name',
                'ReportingFrequency',
                'ScheduleName',
                'Units'
                ]

        df = self._df_query("SELECT * FROM ReportDataDictionary WHERE ReportingFrequency = 'Hourly'")
        df.columns = rddcols
        return df

    def queryseries(self, filterquery):
        df = self.availseries()
        df = self._filter_tabular(filterquery)
        return df


    def getseries(self, query, units = 'ip'):
        '''can pass in either a df made by using 'queryseries' 
        or just a simple search term, or a list of indices'''

        if type(query) == pd.DataFrame:
            dfidx = query
            idxlist = dfidx['ReportDataDictionaryIndex'].values.tolist()       
        elif type(query) == str:
            dfidx = self.queryseries(query)
            idxlist = dfidx['ReportDataDictionaryIndex'].values.tolist()       
        elif type(query) == list:
            idxlist = query

        serieslist = []

        listquery = 'SELECT "Value","ReportDataDictionaryIndex","TimeIndex" FROM "ReportData" WHERE "ReportDataDictionaryIndex" IN '+str(tuple(dfidx.ReportDataDictionaryIndex))
        df = self._df_query(listquery)

        time = self._maketime()[['TimeIndex', 'dt']]

        df = pd.merge(left = df, right = dfidx, on='ReportDataDictionaryIndex')
        df = pd.pivot_table(df, columns=['IndexGroup', 'TimestepType', 'KeyValue', 'Name', 'Units'], index='TimeIndex')
        df['TimeIndex'] = df.index
        df = pd.merge(left = df.reset_index(drop=True), right = time, on='TimeIndex')
        df.index = df['dt']
        df = df.drop('dt', axis=1)
        df = df.drop('TimeIndex', axis=1)

        idx = pd.MultiIndex.from_tuples(list(df.columns))
        df.columns = idx
        if units == 'ip':
            df = self._conv_units(df)

        return df['Value']
            



        




