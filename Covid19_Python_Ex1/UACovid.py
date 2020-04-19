
# UACovid class definition
# Implemented by example of NYTCovid.py by Dr. Tirthajyoti Sarkar, Fremont, CA
# Sergey Kozachenko
# April 2020

import numpy as np
import pandas as pd
import io
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import time
import datetime

class UACovid:
  def __init__(self):
    self.df = None
    self.last_update_date = None
    self.totals = {
      'suspected': 0,
      'confirmed': 0,
      'sick': 0,
      'deaths': 0,
      'recoveries': 0
    }
    self.area_list = None
    self.area_dict = {}

    self.daily_df = None
    self.loaded = False
    self.processed = False
  
  def load(self,
           url="https://raw.githubusercontent.com/VasiaPiven/covid19_ua/master/dataset.csv"):
    url = url
    # download csv data
    s=requests.get(url).content
    # parse CSV into pandas data frame
    self.df = pd.read_csv(io.StringIO(s.decode('utf-8')))
    # convert each row.date string to datetime obj
    #self.df['zvit_date'] =  pd.to_datetime(self.df['zvit_date'], format='%Y-%m-%d')
    
    # save last update date, assumes data is sorted by zvit_date desc
    self.last_update_date = pd.to_datetime(self.df.iloc[0]['zvit_date'], format='%Y-%m-%d')
    print("Data loaded, last update:", self.last_update_date.date())
    self.loaded = True
  
  def print_top_5_rows(self):
    if self.loaded:
      print("First 5 rows of the data")
      print("="*50)
      print(self.daily_df.head())

  def print_totals(self):
    if self.processed:
      print("Totals:")
      print("="*50)
      print(self.totals)

  def print_date_stats(self, date = '2020-04-15'):
    if self.processed:
      print(self.daily_df.loc[date])

  # doesn't work using area_dict
  # def print_date_and_area_stats(self, date = '2020-04-15', area = 'Харківська'):
  #   if self.processed:
  #     print(self.daily_df.loc[[area]])

  def print_area_stats(self,
                       area = 'Харківська',
                       last_30_days = True):
    if self.processed:
      if last_30_days:
        print(self.area_dict[area])
      else:
        print(self.area_dict[area])

  # def get_cumulative_totals(df):
  #   totals = {}
  #   totals['suspected'] = self.df['new_susp'].sum()
  #   totals['confirmed'] = self.df['new_confirm'].sum()
  #   # doesn't look right - 49920, probably it's accumulated value
  #   totals['sick'] = self.df['active_confirm'].sum()
  #   totals['deaths'] = self.df['new_death'].sum()
  #   totals['recoveries'] = self.df['new_recover'].sum()
  
  def process(self):
    pd.set_option('mode.chained_assignment', None)
    self.statedict= {}
    self.countydict= {}
    print("Processing...")
    t1 = time.time()
    if self.loaded:
      # TODO: Optimize by using for loop 1 traverse
      #for index, row in self.df.iterrows():
        #print(row['c1'], row['c2'])
        # totals

      # calc totals
      self.totals['suspected'] = self.df['new_susp'].sum()
      self.totals['confirmed'] = self.df['new_confirm'].sum()
      # get the last date and sum all active confirm
      self.totals['sick'] = self.df[self.df['zvit_date'] == str(self.last_update_date.date())]['active_confirm'].sum()
      self.totals['deaths'] = self.df['new_death'].sum()
      self.totals['recoveries'] = self.df['new_recover'].sum()

      print("totals", self.totals)

      # print("top 5 sorted by active_confirm")
      # print(self.df.sort_values(by='active_confirm', ascending=False).head())

      # calc daily_stats
      self.daily_df = self.df.groupby('zvit_date').agg(
        date = ('zvit_date', min),
        area = ('registration_area', min), 
        new_suspected = ('new_susp', sum),
        new_confirmed = ('new_confirm', sum),
        sick = ('active_confirm', sum),
        new_deaths = ('new_death', sum),
        new_recoveries = ('new_recover', sum),
      )
      # gets unique areas into list
      self.area_list = list(self.df['registration_area'].unique())
      # go through each unique area
      for area in self.area_list:
        area_df = self.df[self.df['registration_area'] == area].groupby('zvit_date').agg(
          new_suspected = ('new_susp', sum),
          new_confirmed = ('new_confirm', sum),
          sick = ('active_confirm', sum),
          new_deaths = ('new_death', sum),
          new_recoveries = ('new_recover', sum),
        ).reset_index()
        area_df['suspected'] = area_df['new_suspected'].cumsum()
        area_df['confirmed'] = area_df['new_confirmed'].cumsum()
        area_df['deaths'] = area_df['new_deaths'].cumsum()
        area_df['recoveries'] = area_df['new_recoveries'].cumsum()
        # save it in dictionary per area as a key
        self.area_dict[area] = area_df
    self.processed = True
    t2 = time.time()
    delt = round(t2-t1,3)
    print("Finished. Took {} seconds".format(delt))
  

  def plot_state(self,
                  area='Харківська',
                  last_30_days=False):
      """
      Plots statewise data
      """
      if self.processed==False:
        print("Data not processed yet. Cannot plot statewise.")
        return None
      
      s = str(area)
      assert s in self.area_list,"Input does not appear in the list of areas. Possibly wrong name/spelling"
      df = self.area_dict[s]
      
      dates = df['zvit_date']
      cases = df['cases']
      deaths = df['deaths']
      newcases = df['newcases']
      newdeaths = df['newdeaths']
      
      if last_30_days:
          dates = df['date'][-31:-1]
          cases = df['cases'][-31:-1]
          deaths = df['deaths'][-31:-1]
          newcases = df['newcases'][-31:-1]
          newdeaths = df['newdeaths'][-31:-1]
      
      plt.figure(figsize=(14,4))
      if last_30_days:
          plt.title("Cumulative cases in {}, for last 30 days".format(s),fontsize=18)
      else:
          plt.title("Cumulative cases in {}".format(s),fontsize=18)
      plt.bar(x=dates,height=cases,color='blue',edgecolor='k')
      plt.xticks(rotation=45,fontsize=14)
      plt.show()
      
      print()
      
      plt.figure(figsize=(14,4))
      if last_30_days:
          plt.title("Cumulative deaths in {}, for last 30 days".format(s),fontsize=18)
      else:
          plt.title("Cumulative deaths in {}".format(s),fontsize=18)
      plt.bar(x=dates,height=deaths,color='red',edgecolor='k')
      plt.xticks(rotation=45,fontsize=14)
      plt.show()
      
      print()
      
      plt.figure(figsize=(14,4))
      if last_30_days:
          plt.title("New cases in {}, for last 30 days".format(s),fontsize=18)
      else:
          plt.title("New cases in {}".format(s),fontsize=18)
      plt.bar(x=dates,height=newcases,color='yellow',edgecolor='k')
      plt.xticks(rotation=45,fontsize=14)
      plt.show()
      
      print()
      
      plt.figure(figsize=(14,4))
      if last_30_days:
          plt.title("New deaths in {}, for last 30 days".format(s),fontsize=18)
      else:
          plt.title("New deaths in {}".format(s),fontsize=18)
      plt.bar(x=dates,height=newdeaths,color='orange',edgecolor='k')
      plt.xticks(rotation=45,fontsize=14)
      plt.show()
      
  def plot_multi_state(self, 
                        states = ['California','Michigan','New York'],
                        last_30_days=False):
      """
      Plots multiple states data in a single plot for comparison
      """
      states = states
      plt.figure(figsize=(14,4))
      if last_30_days:
          plt.title("Cumulative cases, for last 30 days",fontsize=18)
          colors=[]
          for s in states:
              color = tuple(np.round(np.random.random(3),2))
              colors.append(color)
              plt.plot(self.statedict[s]['date'][-31:-1],
                      self.statedict[s]['cases'][-31:-1],
                      color=color,
                      linewidth=2)
              plt.xticks(rotation=45,fontsize=14)
          plt.legend(states,fontsize=14)
          plt.show()
      else:
          plt.title("Cumulative cases",fontsize=18)
          colors=[]
          for s in states:
              color = tuple(np.round(np.random.random(3),2))
              colors.append(color)
              plt.plot(self.statedict[s]['date'],
                      self.statedict[s]['cases'],
                      color=color,
                      linewidth=2)
              plt.xticks(rotation=45,fontsize=14)
          plt.legend(states,fontsize=14)
          plt.show()
  
  def rankState(self,
                N=5,
                daterank=None):
      """
      Ranks the states in a bar chart
      Arguments:
          N: Top N states to be ranked
          date: Date at which the ranking is done. 
                Must be a string in the form '2020-3-27'
      """
      from datetime import date

      cases = {}
      deaths = {}
      newcases = {}
      newdeaths = {}

      if daterank==None:
          d = self.statedf.iloc[-1]['date'].date()
      else:
          d = datetime.datetime.strptime(daterank,'%Y-%m-%d').date()

      for s in self.statedict:
          df=self.statedict[s]
          for i in range(len(df)):
              if df['date'].iloc[i].date()==d:
                  cases[s]=df.iloc[i]['cases']
                  deaths[s]=df.iloc[i]['deaths']
                  newcases[s]=df.iloc[i]['newcases']
                  newdeaths[s]=df.iloc[i]['newdeaths']

      sorted_cases = sorted(((value, key) for (key,value) in cases.items()),reverse=True)
      sorted_cases = sorted_cases[:N]
      sorted_deaths = sorted(((value, key) for (key,value) in deaths.items()),reverse=True)
      sorted_deaths = sorted_deaths[:N]
      sorted_newcases = sorted(((value, key) for (key,value) in newcases.items()),reverse=True)
      sorted_newcases = sorted_newcases[:N]
      sorted_newdeaths = sorted(((value, key) for (key,value) in newdeaths.items()),reverse=True)
      sorted_newdeaths = sorted_newdeaths[:N]

      _,axs = plt.subplots(2,2,figsize=(15,9))
      axs = axs.ravel()
      axs[0].bar(x=[val[1] for val in sorted_cases],
              height=[val[0] for val in sorted_cases],
              color='blue',edgecolor='k')
      axs[0].set_title("Cumulative cases on {}".format(str(d)),
                      fontsize=15)
      axs[1].bar(x=[val[1] for val in sorted_deaths],
              height=[val[0] for val in sorted_deaths],
              color='red',edgecolor='k')
      axs[1].set_title("Cumulative deaths on {}".format(str(d)),
                      fontsize=15)
      axs[2].bar(x=[val[1] for val in sorted_newcases],
              height=[val[0] for val in sorted_newcases],
              color='yellow',edgecolor='k')
      axs[2].set_title("New cases on {}".format(str(d)),
                      fontsize=15)
      axs[3].bar(x=[val[1] for val in sorted_newdeaths],
              height=[val[0] for val in sorted_newdeaths],
              color='orange',edgecolor='k')
      axs[3].set_title("New deaths on {}".format(str(d)),
                      fontsize=15)
      plt.show()