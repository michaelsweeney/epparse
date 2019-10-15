from . import timeseries
from . import tables

class epLoad():
    def __init__(self, fname):
        self.sql = timeseries.SqlSeries(fname)
        self.tables = tables.SqlTables(fname)


    