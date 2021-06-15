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
from tqdm import tqdm
import time
from datetime import datetime
from sklearn.model_selection import train_test_split
import re
from bs4 import BeautifulSoup
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, DoubleType
import random
from utils_func import Utils

utils = Utils()

schema_pages = StructType() \
     .add("d_site",StringType(),True) \
     .add("d_page",StringType(),True) \
     .add("d_l2",StringType(),True) \
     .add("m_visits",IntegerType(),True) \
     .add("m_visitors",IntegerType(),True) \
     .add("m_page_loads",IntegerType(),True) \
     .add("m_time_spent_per_pages_loads",DoubleType(),True) \
     .add("m_time_spent_per_pages_visits",DoubleType(),True) \
     .add("Months",StringType(),True) \
     .add("Years",IntegerType(),True)

#df_pages = pd.read_csv("2015-2020_pages.csv")
spark = SparkSession.builder.master("local[*]") \
                    .appName('SparkCorseMatin') \
                    .config('spark.driver.host','127.0.0.1')\
                    .getOrCreate()
sc = spark.sparkContext

print('Spark is ready with CPU usage :', sc.defaultParallelism)

def init_soup(url):
    A = ("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
       "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
       )
    agent = A[random.randrange(len(A))]
    headers = {'user-agent': agent}
    html_text = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup

def get_url(keywords):
    try:
        keywords = re.sub(r'[^0-9a-zA-Z]+', ' ', keywords).strip()
        url = f"https://www.corsematin.com/recherche?query={keywords.replace(' ', '+')}"
        soup = init_soup(url)
        heading_object=soup.select("div.content>a")
        results_links = {" ".join(info["href"].replace("https://www.corsematin.com/articles/", "").split("-")[:-1]): info["href"] for info in heading_object}
        if keywords in results_links:
            return results_links[keywords]
        else: 
            return None
    except:
        print("error with "+ f"https://www.corsematin.com/recherche?query={keywords.replace(' ', '+')}")

def get_infos(soup, type_of_data):
    try:
        informations_container = soup.select("section.page-title div.informations>div")
        text = ""
        #print(informations_container)
        if type_of_data == "geo":
            return soup.select("section.page-title span.badges>a")[0].getText()
        if type_of_data == "title":
            return soup.select("section.page-title h1")[0].getText()
        if type_of_data == "author" :
            return informations_container[0].getText().replace("Par: ", "")
        if type_of_data == "date":
            return informations_container[1].getText().replace("Publié le: ", "").split(" à ")[0]
        if type_of_data == "hours":
            return informations_container[1].getText().replace("Publié le: ", "").split(" à ")[-1]
        if type_of_data == "section":
            return informations_container[2].getText().replace("Dans: ", "")
        if type_of_data == "content":
            for res in soup.select("div.contenu"):
                text = text +  "\n " + res.text
            return text
        if type_of_data == "nbr_of_comments":
            return soup.select("section#commentaires h1")[0].getText().split(" ")[0]
        if type_of_data == "nbr_of_del_comments":
            return len(soup.select("section.commentaire.moderated"))
    except:
        return None

df_pages = spark.read.option("delimiter", ",").option("header","true").schema(schema_pages).csv(os.environ.get("BASENAME") + "data/2015-2021_pages.csv").repartition(36)
df_pages_RDD = df_pages.rdd
df_pages_RDD = df_pages_RDD\
    .filter(lambda x: ((len(re.findall('-', str(x[1]))) > 3) & ("App" not in x[0])))\
    .persist()
len_RDD = len(df_pages_RDD.collect())
print(len_RDD)

now = datetime.now()
counter = 0
tic = time.perf_counter()
current_time = now.strftime("%H:%M:%S")
print("Launch at :", current_time)
def add_content(iterator):
    try:
        global counter
        final_iterator = []
        geo = None
        title = None
        author = None
        date = None
        hours = None
        section_name = None
        content = None
        nbr_of_comments = None
        nbr_of_del_comments = None
        words_accurate = None
        word_count = None
        char_count = None
        sentence_count = None
        avg_word_length = None
        avg_sentence_lenght = None
        #print(get_url(f"https://www.google.com/search?q={x[1].split('::')[-1].replace('-', '+')}"))
        for x in iterator:
            url = get_url(x[1].split('::')[-1])
            if url:
                try:
                    print("--------")
                    soup = init_soup(url)
                    print(f"url: {url}")
                    geo = get_infos(soup, "geo")
                    print(f"geo:{geo}")
                    title = get_infos(soup, "title")
                    print(f"title:{title}")
                    author = get_infos(soup, "author")
                    print(f"author:{author}")
                    date = str(get_infos(soup, "date")).split(" ")
                    print(f"dateArr: {date}")
                    date = f"{date[0]}-{utils.get_months_numbers_dict(date[1]):02d}-{date[2]} {get_infos(soup, 'hours')}"
                    print(f"date: {date}")
                    section_name = get_infos(soup, "section")
                    content = utils.remove_trailling(get_infos(soup, "content"))
                    nbr_of_comments = get_infos(soup, "nbr_of_comments")
                    nbr_of_del_comments = get_infos(soup, "nbr_of_del_comments")
                    words_accurate = utils.get_words_accurate(content)
                    word_count = int(utils.get_word_count(content))
                    char_count = int(utils.get_char_count(content))
                    sentence_count = utils.get_sentence_count(content)
                    avg_word_length = float(char_count / word_count)
                    avg_sentence_lenght = float(word_count / sentence_count)
                    word_count_title = int(utils.get_word_count(title))
                    char_count_title = int(utils.get_char_count(title))
                    print("--------")
                except Exception as e:
                    print("error")
                    print(e)
                counter = counter + 1
                #print(f"{counter} / {len_RDD}")
                print(x[8], x[9])
            #print(get_url(f"https://www.google.com/search?q={x[1].split('::')[-1].replace('-', '+')}"))
            final_iterator.append((
                x[0],
                x[1],
                x[2],
                x[3], 
                x[4],
                x[5], 
                x[6], 
                x[7], 
                x[8], 
                x[9], 
                url, 
                geo, 
                title, 
                author, 
                date, 
                section_name, 
                content, 
                nbr_of_comments, 
                nbr_of_del_comments,
                words_accurate,
                word_count,
                char_count,
                sentence_count,
                avg_word_length,
                avg_sentence_lenght,
                word_count_title,
                char_count_title
                ))
    except:
        print("error append")
    return iter(final_iterator)
columns_name = ["d_site",
                "d_page",
                "d_l2",
                "m_visits",
                "m_visitors", 
                "m_page_loads",
                "m_time_spent_per_pages_loads",
                "m_time_spent_per_pages_visits",
                "months",
                "years",
                "url",
                "geo",
                "title",
                "author",
                "date",
                "section_name",
                "content",
                "nbr_of_comments",
                "nbr_of_del_comments",
                "content_words_accurate",
                "word_count",
                "char_count",
                "sentence_count",
                "avg_word_length",
                "avg_sentence_lenght",
                "word_count_title",
                "char_count_title"
               ]

df_pages_RDD = df_pages_RDD.mapPartitions(add_content).persist()

df_pages = df_pages_RDD.toDF()
print(df_pages.count())
df_pages.show(1)
toc = time.perf_counter()
print(f"Finished in {toc - tic:0.4f} seconds")

#df_pages.coalesce(1).write.csv(path='./test_spark/output', mode='overwrite', filename= "test.csv")
with open("./data/output.csv", 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(columns_name)
    for row in df_pages.coalesce(1).collect():
        writer.writerow(row)