'''
set of functions to open sql file, find table name, and parse it into a usable format as a dataframe.
'''

import sqlite3
import warnings
import pandas as pd



strtypeidx = {
        1: 'ReportName',
        2: 'ReportForString',
        3: 'TableName',
        4: 'RowName',
        5: 'ColumnName',
        6: 'Units'
            }


class SqlTables:
    '''creates table from available sql output reports.
    args:
        sqlfile: sqlfile path
        tablename = i.e. "Comfort and Setpoint Not Met Summary"
        reportname (optional): for specifying reportname if there are more than identically-named tables in multiple reports'''
    def __init__(self, sqlfile):
        if ".sql" not in sqlfile:
            sqlfile = sqlfile + '.sql'
        self.sqlfile = sqlfile


    # helper functions
    def _df_cols_to_dict(self, df, keycol, valcol):
        '''takes dataframe and makes key:val dict out of columns'''
        return pd.Series(df[valcol].values, index=df[keycol].values).to_dict()

    def _idx_to_str(self, tabledf, stringdict, lookup_col):
        '''takes any col w/ "Index" and adds associated string'''
        string_col = lookup_col.replace("Index","")
        if string_col == lookup_col:
            raise ValueError("Lookup Col str has to have 'Index' in it")
        tabledf[string_col] = tabledf[lookup_col].apply(lambda x: stringdict[x])
        return tabledf

    def _df_query(self, query):
        '''opens sql, makes query (native sql), closes sql and returns df'''
        conn = sqlite3.connect(self.sqlfile)
        df = pd.read_sql((query), conn)
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
        avail = self.avail_tabular()
        df = avail[avail.apply(lambda row: row.astype(str).str.contains(filterquery).any(), axis=1)]
        return df

    def _tryfloat(self, val):
        try:
            val = float(val.strip().replace(" ",""))
        except:
            val = val
        return val

    def _floatdf(self, df):
        floatdf = df.copy()
        for col in floatdf.columns:
            floatdf[col] = floatdf[col].apply(lambda x: self._tryfloat(x))
            
        return floatdf



    # pulling tabulardata tables (i.e. results)
    def avail_tabular(self):
        '''return dataframe of all available tables (with tablename, reportfor, reportname)'''
        tablename = self._df_query("SELECT * FROM 'Strings' WHERE StringTypeIndex = 3")
        reportfor = self._df_query("SELECT * FROM 'Strings' WHERE StringTypeIndex = 2")
        reportname = self._df_query("SELECT * FROM 'Strings' WHERE StringTypeIndex = 1")
        tabulardata = self._df_query("SELECT * FROM 'TabularData'")
        strings = self._df_query("SELECT * FROM 'Strings'")
        stringdict = self._df_cols_to_dict(strings, 'StringIndex', 'Value')
        get_strs = ['ReportNameIndex', 'ReportForStringIndex', 'TableNameIndex']
        for string in get_strs:
            tabulardata = self._idx_to_str(tabulardata, stringdict, string)
            tabulardata.drop(string, axis=1, inplace=True)
        tables = tabulardata[['ReportName', 'ReportForString', 'TableName']].drop_duplicates()
        return tables


    def get_tabular(self, tabledict):
        '''returns single table given table dictionary:
        table['ReportName']
        table['ReportForString']
        table['TableName']
        '''
        reportnameidx = int(self._df_query("SELECT * FROM 'Strings' WHERE StringTypeIndex = 1 and Value = '{0}'".format(tabledict['ReportName']))['StringIndex'])
        reportforidx = int(self._df_query("SELECT * FROM 'Strings' WHERE StringTypeIndex = 2 and Value = '{0}'".format(tabledict['ReportForString']))['StringIndex'])
        tablenameidx = int(self._df_query("SELECT * FROM 'Strings' WHERE StringTypeIndex = 3 and Value = '{0}'".format(tabledict['TableName']))['StringIndex'])

        tablestr = self._df_query("SELECT * FROM 'TabularData' WHERE TableNameIndex = {0} AND ReportForStringIndex = {1} AND ReportNameIndex = {2}".format(tablenameidx, reportforidx, reportnameidx))
        strings = self._df_query("SELECT * FROM 'Strings'")

        stringdict = self._df_cols_to_dict(strings, 'StringIndex', 'Value')
        idxcols = [col for col in tablestr.columns if "Index" in col and "TabularDataIndex" not in col]
        for col in idxcols:
            df = self._idx_to_str(tablestr, stringdict, col)

        df = df[[col for col in df.columns if "Index" not in col]]
        coldict = self._df_cols_to_dict(df, 'ColumnId', 'ColumnName')
        colunitdict = self._df_cols_to_dict(df, 'ColumnId', 'Units')
        rowdict = self._df_cols_to_dict(df, 'RowId', 'RowName')
        valdf = df[['RowId', 'ColumnId', 'Value']].pivot(columns='ColumnId', index='RowId', values='Value')
        valdf.columns = pd.MultiIndex.from_tuples([(coldict[col], colunitdict[col]) for col in valdf.columns])
        valdf.index = [rowdict[row] for row in valdf.index]

        valdf['ReportName'] = tabledict['ReportName']
        valdf['ReportForString'] = tabledict['ReportForString']
        valdf['TableName'] = tabledict['TableName']
        valdf = self._floatdf(valdf)
        return valdf

    def search_tabular(self, filter):
        '''searches any string of available tabular reports and returns list of dataframes with matching in table names'''
        dflist = [self.get_tabular(filterdict) for filterdict in self._df_to_tabledict(self._filter_tabular(filter))]
        return dflist




    # pulling actual tables - standard e+ sql tables
    def simulations(self):
        df = self._df_query("SELECT * FROM 'Simulations'")
        return df












