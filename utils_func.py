import geopandas
import requests
from requests.auth import HTTPBasicAuth
import pprint
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv(verbose=True)
import csv
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import unidecode
import Levenshtein
from tqdm import tqdm
import time
from datetime import datetime
from sklearn.model_selection import train_test_split
import re
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, DoubleType
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima_model import ARIMA
from matplotlib.ticker import FormatStrFormatter
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from nltk import word_tokenize
nltk.download(['punkt','wordnet','stopwords'])
import spacy
spacy.cli.download("fr_core_news_md")
nlp = spacy.load('fr_core_news_md')
import re
import ssl
from drive import data_files
from io import StringIO

ssl._create_default_https_context = ssl._create_unverified_context


class Utils():
    def __init__(self):
        self.headers = {'x-api-key': os.environ.get("API_KEY")}
        self.datas = []
        self.col_names = []
        self.months_numbers = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12
        }
        self.months_numbers_fr = {
            "janvier": 1,
            "février": 2,
            "mars": 3,
            "avril": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "août": 8,
            "septembre": 9,
            "octobre": 10,
            "novembre": 11,
            "décembre": 12
        }
        self.regions_names = [
            "Auvergne-Rhône-Alpes",
            "Bourgogne-Franche-Comté",
            "Bretagne",
            "Centre-Val de Loire",
            "Corse",
            "Grand Est",
            "Hauts-de-France",
            "Île-de-France",
            "Normandie",
            "Nouvelle-Aquitaine",
            "Occitanie",
            "Pays de la Loire",
            "Provence-Alpes-Côte d'Azur"
        ]
        self.plots = []
    
    def is_leap(self, year):
        if (year % 4) == 0:
            if (year % 100) == 0:
                if (year % 400) == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False
    
    def to_bin(self, dataset, column_to_bin):
        for c in column_to_bin:
            if dataset[c].dtype == 'object':
                dataset[c] = pd.Categorical(dataset[c]) 
                catfeat = pd.get_dummies(dataset[c], prefix = c)
                dataset = dataset.drop([c], axis = 1)
                dataset = pd.concat([dataset, catfeat], axis=1)
        return dataset
    
    def generate_csv(self, url, nbr_of_lines, file_name, date_year, multiple):
        if multiple == True:
            years = [int(y) for y in date_year.split("-")]
            years = [y for y in range(min(years), max(years)+1)]
        else:
            years = [int(date_year)]
        p_years = tqdm(total=len(years), disable=False, position=0, leave=True)
        for year in years:
            #print(f"--- {year} ---")
            months = [
                {"january": 31},
                {"february": 28 if self.is_leap(year) == False else 29},
                {"march": 31},
                {"april": 30},
                {"may": 31},
                {"june": 30},
                {"july": 31},
                {"august": 31},
                {"september": 30},
                {"october": 31},
                {"november": 30},
                {"december": 31}
            ]
            for i in range(0,12):
                response = requests.get(
                    f"{url}&period=%7BD:%7Bstart:%27{year}-{i+1:02d}-01%27,end:%27{year}-{i+1:02d}-{list(months[i].values())[0]}%27%7D%7D&max-results={nbr_of_lines}&page-num=1"
                    ,auth=HTTPBasicAuth(os.environ.get("API_LOGIN"), os.environ.get("API_PASSWORD"))
                    ,headers=self.headers
                )
                #print(f"  {year} -- {list(months[i].keys())[0]}")
                results = response.json()
                month_datas = [list(r.values()) + list(months[i].keys()) + [year] for r in results['DataFeed'][0]["Rows"]]
                self.datas = self.datas + month_datas
                if i == 0 and years.index(year) == 0:
                    self.col_names = self.col_names + [c['Name'] for c in results['DataFeed'][0]['Columns']] + ["Months"] + ["Years"]
                p_years.update(0.08333333333)
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.col_names)
            for row in self.datas:
                writer.writerow(row)
        
        return file_name

    def filter_column_names(self, df, to_exclude):
        columns_names = [n for n in df.columns if to_exclude not in n]
        return df[columns_names]

    def months_to_number_dataset(self,dataset):
        def months_to_number(row):
            row = self.months_numbers[row]
            return row
        dataset = dataset.copy()
        ds = dataset.apply( lambda x : months_to_number(x) )
        return ds
    def get_months_numbers_dict(self, month):
        return self.months_numbers_fr[month]

    def sorter(self, column):
        cat = pd.Categorical(column, categories=self.months_numbers)
        return pd.Series(cat)

    def is_in_metro(self, region):
        for rn in self.regions_names:
            region_check = unidecode.unidecode(rn.lower()).replace("-", " ").strip()
            region_name = unidecode.unidecode(region.lower()).replace("-", " ").strip()
            if Levenshtein.ratio(region_check,region_name) > 0.8:
                return True
                break
            else:
                if self.regions_names.index(rn) == len(self.regions_names) - 1:
                    return False 
    
    def format_region(self, region):
        return unidecode.unidecode(region.lower()).replace("-", " ").strip()

    def categorize_region(self, region):
        for r in self.regions_names:
            if self.format_region(region) ==  self.format_region(r) and self.format_region(region) != "corse":
                return "France continentale"
                break
            else:
                if self.regions_names.index(r) == len(self.regions_names)-1 :
                    if self.format_region(region) != "corse":
                        return "Etrangers"
                        break
                    else:
                        return region
    def add_plot(self, plot):
        self.plots.append(plot)
        print(self.plots)
    
    def get_plots(self):
        return self.plots
    
    def custom_plot(self, el_to_plot, ax, title=None, xlabel=None, ylabel=None, fontsize=None, pad_title=None, labelsize=None, param_mode="default", custom_params={}):
        if param_mode == "map":
            el_to_plot.plot(
                ax = ax,
                legend=custom_params["legend"],
                cmap=custom_params["cmap"],
                edgecolor=custom_params["edgecolor"],
                column=custom_params["column"],
                legend_kwds=custom_params["legend_kwds"]
            )
        if param_mode == "pie":
            el_to_plot.plot.pie(ax=ax, autopct=custom_params["autopct"], subplots=custom_params["subplots"])
        if param_mode =="default":
            el_to_plot.plot(ax=ax)
        if type(ax) is not np.ndarray:
            ax.set_xlabel(xlabel, fontsize=fontsize)
            ax.set_ylabel(ylabel, fontsize=fontsize)
            ax.set_title(title, fontsize=fontsize, pad = pad_title)
            ax.tick_params(axis='x', labelsize=labelsize)
            ax.tick_params(axis='y', labelsize=labelsize)
        else:
            for i, a in enumerate(ax):
                for el in a :
                    el.get_legend().remove()
                    el.set_title(el.yaxis.get_label().get_text(), fontsize=fontsize, pad = pad_title)
                    el.yaxis.set_visible(False)
                    el.xaxis.set_visible(False)
    def remove_trailling(self, text):
        return " ".join([s for s in text.replace("\n", " ").split(" ") if s != " "]).strip()
    
    def get_word_count(self, text):
        words_arr = [s for s in str(text).split(" ") if len(s) > 0]
        word_count = len(words_arr)
        return word_count

    def get_char_count(self, text):
        words_arr = [s for s in str(text).split(" ") if len(s) > 0]
        char_count = np.sum([len(w) for w in words_arr])
        return char_count

    def get_sentence_count(self, text):
        sentences_arr = [s for s in str(text).split(".") if len(s) > 0]
        sentence_count = len(sentences_arr)
        return sentence_count

    def get_words_accurate(self, text):
        excluded_tags = {"SPACE","NUM","PRON","CCONJ","AUX","DET","CONJ", "VERB", "ADJ", "ADV", "ADP"}
        words_accurate = " ".join([word.text for sentence in str(text).split(".") for word in nlp(sentence) if word.pos_ not in excluded_tags])
        return words_accurate
    def get_initial_datas(self):
        url = requests.get(data_files['2015 - 2020.csv'])
        csv_raw = StringIO(url.text)
        #BASE
        tic = time.perf_counter()
        df = pd.read_csv(csv_raw)
        #df = pd.read_csv("./data/2015 - 2020.csv")
        df["Months_char"] = df["Months"]
        df["Months"] = self.months_to_number_dataset(df["Months"])
        df["Day"] = 1
        df["Date"] = pd.to_datetime(df[["Months", "Years", "Day"]])
        region = geopandas.read_file('https://france-geojson.gregoiredavid.fr/repo/regions.geojson')
        region['d_geo_region'] = region['nom'].apply(lambda g : self.format_region(g) if self.is_in_metro(g) else None)
        region['geoids'] = region.index

        reco = pd.read_csv(data_files['reco.csv'], error_bad_lines=False)
        #reco = pd.read_csv("./data/reco.csv", error_bad_lines=False)
        toc = time.perf_counter()
        #app.logger.info(f"get_initial_datas finished in {toc - tic:0.4f} seconds")
        return [df, region, reco]
            
#utils = Utils()


