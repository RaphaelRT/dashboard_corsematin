import sys
import os
sys.path.insert(0, os.environ.get("BASENAME") + 'apps/callbacks')
from trafics import trafic_callbacks
from home import home_callbacks
from reco import reco_callbacks
import dash
import pandas as pd
from utils_func import Utils
from flask_caching import Cache
import time
from dash_app import app



cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})


TIMEOUT = 30
utils = Utils()
#@cache.memoize(timeout=TIMEOUT)
initial_datas = utils.get_initial_datas()

df = initial_datas[0]
region = initial_datas[1]

home_callbacks(cache, TIMEOUT, region, df)
trafic_callbacks(cache, TIMEOUT, region, df)
reco_callbacks(cache, TIMEOUT, region, df)

