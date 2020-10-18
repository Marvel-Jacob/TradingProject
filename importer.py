import requests
import csv, re, pickle
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime


#List of all directories to be mentioned here
historical_data_dir = "C:/Users/Admin/Desktop/Coding/Trading Project/CRYPTO IDX/data/historical/"
data_dir = "C:/Users/Admin/Desktop/Coding/Trading Project/CRYPTO IDX/data/"
model_dir = "C:/Users/Admin/Desktop/Coding/Trading Project/CRYPTO IDX/models/"
pickle_file_dir = "C:/Users/Admin/Desktop/Coding/Trading Project/CRYPTO IDX/data/pickle files/"
hourly_data_dir = "C:/Users/Admin/Desktop/Coding/Trading Project/CRYPTO IDX/data/hourly data/"

class DataImporter:
	def __init__(self, exchange):
		#exchange and assets attributes for crypto
		self.exchange = exchange
		self.all_assets = ["BTC","ETH","LTC","ZEC"]
		self.assets = ["BTC","ETH","LTC"]
		
		self.history_keys = [self.key3, self.key4, self.key5, self.key6]
		
		#extra attributes of dates(today and yesterday) to represent file names later
		self.now = re.sub('-','_',str(date.today()))
		self.yday = re.sub('-','_',str(date.today() - timedelta(days=1)))
	
	#describe the class instance
	def __repr__(self):
		pass
	
	#returns one filename of todays date to be used by scheduler.py
	def todays_filenames(self):
		path = hourly_data_dir.replace(data_dir,"")
		return f"crypto_{self.now}.csv", f"{path}crypto_{self.now}.csv"

	def _convert_to_datetime(self, date):
		date =  datetime.fromtimestamp(int(date/1000.))
		return date

	#function to convert other timezone to local timezone
	def tz_to_localtz(self, utc_date):
		utc_date = utc_date.split(".")[0]
		utc_date = datetime.strptime(utc_date.split('.')[0], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=5, minutes=30)
		return utc_date

	def _return_urls(self):
		url_btc = "https://api.gemini.com/v2/candles/btcusd/1m"
		url_eth = "https://api.gemini.com/v2/candles/ethusd/1m"
		url_ltc = "https://api.gemini.com/v2/candles/ltcusd/1m"
		return [url_btc, url_eth, url_ltc]

	#extracts data from alpaca api for the current moment and store it in current.csv
	def download_current_data(self):
		master = pd.DataFrame()
		urls = self._return_urls()
		column_names = self._return_minute_colnames()
		for i, url, colnames in zip(range(len(urls)), urls, column_names):
			response = requests.get(url)
			temp_data = pd.DataFrame(response.json())
			temp_data.columns = colnames
			if i==0:
				master = master.append(temp_data, ignore_index=True)
			else:
				master = pd.merge(master, temp_data, on="timestamp", how="inner")
		master['timestamp'] = master['timestamp'].apply(lambda x: self._convert_to_datetime(x))
		master = self._format_dataset(master.head(1))
		master.to_csv(f"{data_dir}current.csv", index=False)

	def _return_minute_colnames(self):
		btc_cols = ['timestamp', 'open(t)_btc','high(t)_btc','low(t)_btc','close(t)_btc','volume_btc']
		eth_cols = ['timestamp', 'open(t)_eth','high(t)_eth','low(t)_eth','close(t)_eth','volume_eth']
		ltc_cols = ['timestamp', 'open(t)_ltc','high(t)_ltc','low(t)_ltc','close(t)_ltc','volume_ltc']
		return [btc_cols, eth_cols, ltc_cols]

	def _return_daily_colnames(self):
		btc_cols = ['timestamp', 'open(t)_btc','high(t)_btc','low(t)_btc','close(t)_btc']
		eth_cols = ['timestamp', 'open(t)_eth','high(t)_eth','low(t)_eth','close(t)_eth']
		ltc_cols = ['timestamp', 'open(t)_ltc','high(t)_ltc','low(t)_ltc','close(t)_ltc']
		return [btc_cols, eth_cols, ltc_cols]

	#Function to collect crypto data from api and store the data in its respective directory as an everday
	#opertion
	def _CryptoData(self, hourly = False):
		if hourly:
			limit = 100
			key = self.key4
		else:
			limit = 1440
			key = self.key2
		master = pd.DataFrame()
		column_names = self._return_daily_colnames()
		for i, asset, colnames in zip(range(len(self.assets)), self.assets, column_names):
			print(f"Downloading {asset} daily dataset...", end="", flush=True)
			url = f"https://rest.coinapi.io/v1/ohlcv/{asset}/USD/latest?period_id=1MIN&limit={limit}&apikey={key}"
			response = requests.get(url)
			if int(response.status_code)==200:
				temp_data = self._transform(pd.DataFrame(response.json()))
				temp_data.columns = colnames
				if i==0:
					master = master.append(temp_data, ignore_index=True)
				else:
					master = pd.merge(master, temp_data, on="timestamp", how="inner")
				print("Completed")
			else:
				print(f"Response Error: {response.status_code}")
				return
		master = self._format_dataset(master).set_index('timestamp').resample("Min").ffill().reset_index()
		if hourly:
			master.to_csv(f"{hourly_data_dir}crypto_{self.now}.csv", index=False)
		else:
			master.to_csv(f"{data_dir}crypto_{self.now}.csv", index=False)

	def _transform(self, data):
		new_colnames = {'time_period_start':'timestamp', 'price_close':'close(t)', 'price_open':'open(t)',
		'price_high':'high(t)', 'price_low':'low(t)'}
		drop_cols = ['time_period_end','volume_traded','trades_count','time_open','time_close']
		data = data.rename(columns=new_colnames).drop(drop_cols, axis=1)
		data['timestamp'] = data['timestamp'].apply(lambda x: self.tz_to_localtz(x))
		return data

	def _format_dataset(self, master):
		numeric_cols = list(master.columns)[1:]
		datetime_col = list(master.columns)[0]
		master[numeric_cols] = master[numeric_cols].apply(lambda x: pd.to_numeric(x))
		master[datetime_col] = master[datetime_col].apply(lambda x: pd.to_datetime(x))
		master['open(t)'] = master.apply(lambda x: (x['open(t)_btc']+x['open(t)_eth']+x['open(t)_ltc'])/3, axis=1)
		master['high(t)'] = master.apply(lambda x: (x['high(t)_btc']+x['high(t)_eth']+x['high(t)_ltc'])/3, axis=1)
		master['low(t)'] = master.apply(lambda x: (x['low(t)_btc']+x['low(t)_eth']+x['low(t)_ltc'])/3, axis=1)
		master['close(t)'] = master.apply(lambda x: (x['close(t)_btc']+x['close(t)_eth']+x['close(t)_ltc'])/3, axis=1)
		master = master[['timestamp', 'open(t)','high(t)','low(t)','close(t)']]
		return master
	
	#driver function to download the data
	def download(self, hourly):
		self._CryptoData(hourly)

	
	#---------------from here on functions are created to get the historical data from apis------------#
	
	def make_pickles(self):
		for asset, api_key in zip(self.assets, self.history_keys):
			print(f"Creating pickle file for {asset}.....", end = "", flush=True)
			url = f"https://rest.coinapi.io/v1/ohlcv/{asset}/USD/latest?period_id=1MIN&limit=100000&apikey={api_key}"
			response = requests.get(url).json()
			with open(f"{pickle_file_dir}{asset}.pickle", "wb") as pickle_writer:
				pickle.dump(response, pickle_writer)
			print("Created!")

	def pickles_to_csv(self):
		for asset in self.assets:
			print(f"Converting pickle fomrat to csv format of {asset}...", end="", flush=True)
			with open(f"{pickle_file_dir}{asset}.pickle", "rb") as pickle_reader:
				data = self._transform(pd.DataFrame(pickle.load(pickle_reader)))
			data.to_csv(f"{historical_data_dir}{asset}.csv", index=False)
			print("Converted!")
		
	def merge_datasets(self):
		columns_names = self._return_daily_colnames()
		master = pd.DataFrame()
		for i, asset, col_names in zip(range(len(self.assets)),self.assets,columns_names):
			data = pd.read_csv(f"{historical_data_dir}{asset}.csv", names = col_names, skiprows=1)
			if i==0:
				master = master.append(data, ignore_index=True)
			else:
				master = pd.merge(master, data, on="timestamp", how="inner")
		master = self._format_dataset(master)
		master.to_csv(f"{data_dir}master.csv", index=False)
