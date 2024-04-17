from fastapi import FastAPI

from pydantic import BaseModel
import requests
from io import StringIO
import time

# environment variables
from dotenv import load_dotenv
import os

# fastapi utils
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

# data science libs
import json
import pandas as pd
from sklearn.linear_model import LogisticRegression
import numpy as np
import math

app = FastAPI()

# Load .env file
load_dotenv()

# load CORS origins and configure middleware
origins = os.getenv("CORS_ORIGINS", ["https://ncaa.mbhs.edu"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

teams = [
  'hackastat',
  'march sadness',
  'kaggle ids',
  'lebron james',
  'le bon bon',
  'we\'re cooked',
  'tom brady',
  'ball don\'t log',
  'jump shot jokers',
  'march madness masters (triple m)',
  'sake and bake',
  'slam dunkin donuts',
  'stand on our money, tall as edey',
  "stat dunkers",
  'the goat',
  'clickbait',
  'kaggle ids 2',
  'tom brady 2',
  'lebron james 2',
  'lebron james 3',
  'stand on our money, tall as edey 2',
  'jump shot jokers 2',
  'stat dunkers 2'
]

data = []
matchups = pd.DataFrame(columns=['outcome'])

class Data(BaseModel):
  team: str
  image: str | None = None
  members: str
  log_losses: dict[str, float]
  predictions: dict[str, float]
  avg_log_loss: float

@app.get("/data")
def read_root() -> list[Data]:
    return data

@app.on_event("startup")
@repeat_every(seconds=30)
def calculate_log_losses():
  global data
  global matchups
  temp_data = []

  # load the matchups data
  raw_matchup_data = requests.get(f'https://docs.google.com/spreadsheets/d/1i-2i5E2I-M7uCjcSS1TLW1v2n5dbZQfVQIK16kx5-94/gviz/tq?tqx=out:csv&sheet=Matchups').text
  new_matchups = pd.read_csv(StringIO(raw_matchup_data))

  # drop unnamed columns
  new_matchups = new_matchups.loc[:, ~new_matchups.columns.str.contains('^Unnamed')]
  
  print("Loaded Matchups data!")

  def filterNan(x):
    if (math.isnan(x)):
      return False
    return True

  if (list(filter(filterNan, new_matchups['outcome'])) == list(filter(filterNan, matchups['outcome']))):
    print("No update in matchups data!")
    return
  else:
    print('New matchups data found!')
    matchups = new_matchups

  for team in teams:
    try: 
      with open(f'./team data/{team}/metadata.json') as json_file:
        metadata = json.load(json_file)
    except:
      print(f"Error loading {team} metadata file")
      continue
    
    try:
      df = pd.read_csv(f'./team data/{team}/data.csv')
    except:
      print(f"Error loading {team} data file")
      continue

    print(f"Loaded {team} files!")

    # create a sklearn Logistic Regression model using coefs from metadata
    model = LogisticRegression(fit_intercept=False) 
    features = list(metadata['coefs'].keys())

    # create blank training dataframes
    blank_train_x = pd.DataFrame(columns=features)
    blank_train_x.loc[0] = 0
    blank_train_x.loc[1] = 1

    blank_train_y = pd.DataFrame(columns=['outcome'])
    blank_train_y.loc[0] = 0
    blank_train_y.loc[1] = 1

    # fit the model against blank outcome data
    model.fit(blank_train_x[features], blank_train_y['outcome'])

    # set the coefs to the ones from the metadata
    model.coef_ = np.array([list(metadata['coefs'].values())])

    print(f"Generated {team} model!")

    log_losses = {}
    predictions = {}

    start = time.time()
    
    # generarate all the possible matchups and use the difference in stats to create a mean and standard deviation to create a z-score standartization function
    all_matchups = pd.DataFrame(columns=features)
    for index, row in df.iterrows():
      # get all the possible matchups that are possible if this team's kaggle_id is lower, making it the home team
      for index_2, row_2 in df[df['kaggle_id'] > row['kaggle_id']].iterrows():
        try:
          all_matchups.loc[len(all_matchups.index)] = row[features] - row_2[features]
        except Exception as e:
          print(e)
          continue

    means = all_matchups.mean()
    stds = all_matchups.std()

    # for each features in df calculate the z-score
    for feature in features:
      df[feature] = (df[feature] - means[feature]) / stds[feature]

    end = time.time()
    print(f"Standardizied {team} data using z-scores in {end - start} seconds!")

    for index, row in matchups.iterrows():
      stats = pd.DataFrame(columns=features)
      try:
        stats[features] = df[df['kaggle_id'] == row['kaggle_id']][features].values - df[df['kaggle_id'] == row['kaggle_id_2']][features].values
      except Exception as e:
        print(e)
        
      try:
        pred = model.predict_proba(stats[features])
      except Exception as e:
        print(e)
        continue

      matchup_name = f"{row['team']} vs {row['team_2']}"
      if (metadata.get('cap') != None or metadata.get('floor') != None):
        if (pred[0][1] > metadata['cap']):
          pred[0][1] = metadata['cap']
          pred[0][0] = 1 - metadata['cap']
        elif (pred[0][1] < metadata['floor']):
          pred[0][1] = metadata['floor']
          pred[0][0] = 1 - metadata['floor']

      predictions[matchup_name] = pred[0][1]

      # skip unplayed games
      if str(row['outcome']) == 'nan':
        continue

      # calculate the log loss of the prediction
      log_loss = -1 * (row['outcome'] * np.log(pred[0][1]) + (1 - row['outcome']) * np.log(pred[0][0]))
      log_losses[matchup_name] = log_loss

    # calculate the average log loss
    if len(log_losses) == 0:
      avg_log_loss = -1
    else:
      avg_log_loss = np.mean(list(log_losses.values()))
    print(f"Calculated {team} avg log loss: {avg_log_loss}!")

    temp_data.append({
      'team': metadata['name'],
      'image': metadata['image'],
      'members': metadata['members'],
      'log_losses': log_losses,
      'predictions': predictions,
      'avg_log_loss': avg_log_loss
    })
  
  # sort temp_data by avg log loss
  temp_data = sorted(temp_data, key=lambda x: x['avg_log_loss'])

  data = temp_data

  