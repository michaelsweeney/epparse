'''
module for taking dataframes for
hourly results,
parsing them by unit/object/value,
and passing them into separate
interactive plotly graphs for
results analysis and exploration.

    available plotly colorscales:
        ['Blackbody',
        'Bluered',
        'Blues',
        'Earth',
        'Electric',
        'Greens',
        'Greys',
        'Hot',
        'Jet',
        'Picnic',
        'Portland',
        'Rainbow',
        'RdBu',
        'Reds',
        'Viridis',
        'YlGnBu',
        'YlOrRd']

'''
import os
import pandas as pd
from distutils.version import LooseVersion as lv
import numpy as np

import plotly
from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.offline as py
import plotly.graph_objs as go
from plotly import tools
import textwrap

config = {'editable':True}
init_notebook_mode(connected=True)

def colname_to_int(df, colname):
    '''helper function.
    allows passage of integer or string into function.
    if function is string, finds respective position'''
    
    if type(colname) == str:
        num = df.columns.get_loc(colname)
        name = colname
    else:
        num = colname
        name = df.iloc[:,colname].name
    return num, name
        

def scatter(df,
            x, y, z = False, 
            height=700, width=1000, 
            plot_title='default', y_title='default', x_title='default', marker_title='Units', 
            plot=True, asFigure=False, layoutupdate=False, colorscale='Viridis'):
    
    '''take df, x, y, z (optional) columns as integers and
    return plotly plot'''
    
    if type(df) == pd.core.series.Series:
        df = pd.DataFrame(df)
    
    x, xname = colname_to_int(df, x)
    y, yname = colname_to_int(df, y)

    if z:
        z, zname = colname_to_int(df, z)
        zintname = df.iloc[:,z].name
        marker = dict(color = df.iloc[:,z].values,
                        colorscale=colorscale,
                        showscale=True,
                        colorbar={'title': marker_title, 'titleside': 'right'})
              
        trace = go.Scatter(
            x = df.iloc[:,x].values,
            y = df.iloc[:,y].values,
            mode = 'markers',
            marker=marker)

        title = str(xname) + " vs " + str(yname) + ", colored by " + str(zintname)    
    
    else:
        
        marker = dict(colorscale='Viridis')    
        trace = go.Scatter(
        x = df.iloc[:,x].values,
        y = df.iloc[:,y].values,
        mode = 'markers',
        marker=marker)

        title = str(xname) + " vs " + str(yname)

    #override default args
    if plot_title != 'default': title = plot_title
    if x_title != 'default': xname = x_title
    if y_title != 'default': yname = y_title
    
    layout = dict(title = title,
                  yaxis = dict(title = str(yname), zeroline = False),
                  xaxis = dict(title = str(xname), zeroline = False),
                  height = height,
                  width = width)

    if layoutupdate:
        layout.update(layoutupdate)
        
    data = [trace]    
    fig = dict(data=data, layout=layout)    
    if plot:
        py.iplot(fig,config=config)
    if asFigure:
        return fig
 


def heatmap(df,
            colname, 
            plot_title = 'default',
            resolution = 'day', aggfunc='mean', 
            zmin = 'default', zmax = 'default',
            zsmooth='best',
            reversescale=False,
            colorscale='RdBu', colorbar_title = 'Units',
            height=600, width=1000,
            plot=True, asFigure=False, layoutupdate=False):

    '''take df, x, y, z (optional) columns as integers and
    return a plotly heatmap'''
    
    if type(df) == pd.core.series.Series:
        df = pd.DataFrame(df)
    x, plt_title = colname_to_int(df, colname)
    
    dfpivot = pd.DataFrame(df.iloc[:,x])
    dfpivot['hour'] = dfpivot.index.hour
    dfpivot['day'] = dfpivot.index.map(lambda x: x.strftime('%b-%d'))
    dfpivot['week'] = dfpivot.index.week    
    dfpivot['month'] = dfpivot.index.month
    dfpivot['dayofyear'] = dfpivot.index.dayofyear
    dfpivot.columns = [''.join(x) for x in dfpivot.columns]
    dfpivot = dfpivot.pivot_table(values=dfpivot.columns[0], index = 'hour', columns = ['dayofyear', 'week', 'day', 'month'], aggfunc = aggfunc)
    

    trace = go.Heatmap(
        x = [x[2] for x in dfpivot.columns],
        y = dfpivot.index.values,
        z = dfpivot.values,
        zsmooth=zsmooth,
        reversescale=reversescale,
        colorscale=colorscale,
        colorbar=dict(title=colorbar_title))

    if zmin != 'default':
        if zmax == 'default':
            raise ValueError("Error: If entering zmin or zmax, BOTH must be specified.")
        trace.update(zmin = zmin)
        trace.update(zmax = zmax)
        
    if plot_title == 'default': 
        title = str(plt_title) + " Annual Heatmap"
    
    else: title = plot_title
    
    layout = dict(title = title,
                  height = height,
                  width = width) 
                  
    data = [trace]    
    fig = dict(data=data, layout=layout)    
    fig['layout'].update({
                        'font' : {'family': 'Futura LT BT, monospace', 'size': 14},
                        'title' : title,
                        'titlefont': {'size': 24},
                        'xaxis': {'title' : 'Day of Year'},
                        'yaxis': {'title' : 'Hour of Day'}
})
    if layoutupdate:
        layout.update(layoutupdate)
    
    
    if lv(plotly.__version__) >= lv('3.5'):
        fig['data'][0]['colorbar']['title'].update({'side':'right'})
    else:
        fig['data'][0]['colorbar'].update({'titleside':'right'})
    if plot:
        py.iplot(fig,config=config)
    if asFigure:
        return fig


def surface(df,
            colname, 
            plot_title = 'default',
            resolution = 'day', aggfunc='mean', 
            zmin = 'default', zmax = 'default',
            reversescale=False,
            colorscale='RdBu', colorbar_title = 'Units',
            height=600, width=1200,
            plot=True, asFigure=False, layoutupdate=False):

    '''take df, x, y, z (optional) columns as integers and
    return a plotly heatmap'''
    
    if type(df) == pd.core.series.Series:
        df = pd.DataFrame(df)
    x, plt_title = colname_to_int(df, colname)
    
    dfpivot = pd.DataFrame(df.iloc[:,x])
    dfpivot['hour'] = dfpivot.index.hour
    dfpivot['day'] = dfpivot.index.map(lambda x: x.strftime('%b-%d'))
    dfpivot['week'] = dfpivot.index.week    
    dfpivot['month'] = dfpivot.index.month
    dfpivot['dayofyear'] = dfpivot.index.dayofyear
    dfpivot.columns = [''.join(x) for x in dfpivot.columns]
    dfpivot = dfpivot.pivot_table(values=dfpivot.columns[0], index = 'hour', columns = ['dayofyear', 'week', 'day', 'month'], aggfunc = aggfunc)
    

    trace = go.Surface(
        x = [x[2] for x in dfpivot.columns],
        y = dfpivot.index.values,
        z = dfpivot.values,
        reversescale=reversescale,
        colorscale=colorscale,
        colorbar=dict(title=colorbar_title))

    if zmin != 'default':
        if zmax == 'default':
            raise ValueError("Error: If entering zmin or zmax, BOTH must be specified.")
        trace.update(zmin = zmin)
        trace.update(zmax = zmax)
        
    if plot_title == 'default': 
        title = str(plt_title) + " Annual Heatmap"
    
    else: title = plot_title
    
    layout = dict(title = title,
                  height = height,
                  width = width) 
                  
    data = [trace]    
    fig = dict(data=data, layout=layout)    
    fig['layout'].update({
                        'font' : {'family': 'Futura LT BT, monospace', 'size': 14},
                        'title' : title,
                        'titlefont': {'size': 24},
                        'xaxis': {'title' : 'Day of Year'},
                        'yaxis': {'title' : 'Hour of Day'}
})
    if layoutupdate:
        layout.update(layoutupdate)
        
    fig['data'][0]['colorbar'].update({'titleside':'right'})
    if plot:
        py.iplot(fig,config=config)
    if asFigure:
        return fig
        
def line(df,
         plot_title='Hourly Plot', yaxistitle = 'units', xaxistitle = 'Year', 
         colorscale='set1',
         width=1200, height=800,
         plot=True, asFigure=False, layoutupdate=False, autosize = True): 
            
    '''simple plot for a dataframe. plots all columns.'''
    if type(df.columns) == pd.core.index.MultiIndex:
        df.columns = [', '.join(col) for col in df.columns]
    if type(df) == pd.core.series.Series:
        df = pd.DataFrame(df)

    data = [go.Scatter(x = df.index,
                       y = df[col].values, 
                       mode = 'lines',
                       name = ''.join(str('<br>'.join(textwrap.wrap(col, width=100)).split(", ")[-3:]))[1:-1],
                       line=dict(width=1.5))
            for col in df]

                                
    if autosize:
        layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor = 'rgba(0,0,0,0)',
                           font=dict(family='Futura LT BT, monospace', size = 14),
                           title=plot_title,
                           height=height,
                           titlefont= dict(size=24),
                           xaxis = dict(title= xaxistitle, titlefont= dict(size = 18)),
                           yaxis = dict(title=yaxistitle, titlefont=dict(size =18)),
                           #legend = dict(orientation='h', xanchor='right', x=1.02, yanchor='top', y=0))
                           legend = dict(x=1.02))
    else:
        layout = go.Layout(width=width,
                           height=height,
                           paper_bgcolor='rgba(0,0,0,0)',
                           plot_bgcolor = 'rgba(0,0,0,0)',
                           font=dict(family='Futura LT BT, monospace', size = 14),
                           title=plot_title,
                           titlefont= dict(size=24),
                           xaxis = dict(title= xaxistitle, titlefont= dict(size = 18)),
                           yaxis = dict(title=yaxistitle, titlefont=dict(size =18)),
                           #legend = dict(orientation='h', xanchor='right', x=1.02, yanchor='top', y=0)),
                           legend = dict(x=1.02))
    if layoutupdate:
        layout.update(layoutupdate)  
    fig = dict(data=data, layout=layout)
    if plot:
        py.iplot(fig, config=config)
    if asFigure:
        return fig       


   
def line_dailyrange(df,
            colname, 
            plot_title = 'default',
            height=600, width=1200,
            plot=True, asFigure=False, layoutupdate=False, autosize=False):

    '''take df and column, return piv df of min max mean'''
    
    if type(df) == pd.core.series.Series:
        df = pd.DataFrame(df)
    x, plt_title = colname_to_int(df, colname)
    
    dfpivot = pd.DataFrame(df.iloc[:,x])
    dfpivot['dayofyear'] = dfpivot.index.dayofyear
    dfpivot.columns = ['a', 'b']
    dfpivot = pd.concat([pd.pivot_table(dfpivot, 'a', 'b', aggfunc='min'), pd.pivot_table(dfpivot, 'a', 'b', aggfunc='max'), pd.pivot_table(dfpivot, 'a', 'b', aggfunc='mean')], axis=1)
    dfpivot.columns = ['min', 'max', 'mean']
    
    trace0 = go.Scatter(x = dfpivot.index.values, y = dfpivot['min'].values,
                    fill=None,
                    name="Daily Min",
                    mode='lines',
                    line=dict(color='rgb(65, 105, 225)'))

    trace1 = go.Scatter(x = dfpivot.index.values, y = dfpivot['max'].values,
                        fill='tonexty',
                        name="Daily Max",
                        mode='lines',
                        line=dict(color='rgb(65, 105, 225)'))

    trace2 = go.Scatter(x = dfpivot.index.values, y = dfpivot['mean'].values,
                        fill=None,
                        name="Daily Mean",
                        mode='lines',
                        line=dict(color='rgb(255, 0, 0)'))

    data = [trace0, trace1, trace2]           
    if plot_title == 'default': 
        title = str(plt_title) + " Daily Range"
    
    else: 
        title = plot_title
    
    if autosize:
        layout = dict(title = title,)
    
    else:
        layout = dict(title = title,
                  height = height,
                  width = width) 
 
    fig = dict(data=data, layout=layout)    
    fig['layout'].update({
                        'font' : {'family': 'Futura LT BT, monospace', 'size': 14},
                        'title' : title,
                        'titlefont': {'size': 24},
                        'xaxis': {'title' : 'Day of Year'}, 
                        'yaxis': {'title' : 'Units'}, 
})
    if layoutupdate:
        layout.update(layoutupdate)
        
    if plot:
        py.iplot(fig,config=config)
    if asFigure:
        return fig

        
def hist(df, 
         colname,
         bins=10,
         width=800, 
         height=500,
         y_title = 'units', 
         x_title = 'Year', 
         plot_title='Hourly Plot',
         bin_start='default',
         bin_end='default',
         plot=True, 
         asFigure = False,
         layoutupdate=False):
    
    '''df hist plot'''
    
    if type(df) == pd.core.series.Series:
        df = pd.DataFrame(df)
    
    df_filt = df.copy()
    col, plt_title = colname_to_int(df, colname)
    
    # handle bin range
    if bin_start != 'default':
        df_filt = df_filt[df_filt.iloc[:, col] > bin_start]       
    elif bin_end != 'default':
        df_filt = df_filt[df_filt.iloc[:, col] < bin_end]
    else:
        bin_start = df_filt.iloc[:, col].min()
        bin_end = df_filt.iloc[:, col].max()
        
    trace = go.Histogram(x = df_filt.iloc[:,col],
                         xbins=dict(start=bin_start,end=bin_end, size = bins),
                         autobinx=False)

    if plot_title == 'default': 
        title = str(plt_title) + " Histogram"  
    else: title = plot_title
    
    layout = dict(title = title,
                  height = height,
                  width = width) 
                  
    data = [trace]    
    fig = dict(data=data, layout=layout)    

    if layoutupdate:
        layout.update(layoutupdate)
    if plot:
        py.iplot(fig,config=config)
    if asFigure:
        return fig
