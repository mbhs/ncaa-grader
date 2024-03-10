from fastapi import FastAPI
from pydantic import BaseModel

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

app = FastAPI()

# Load .env file
load_dotenv()

# load CORS origins and configure middleware
origins = os.getenv("CORS_ORIGINS", ["https://mbhs.edu"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

teams = [
  'demo team',
  'demo team 2'
]

data = []

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
@repeat_every(seconds=3600)
def calculate_log_losses():
  global data
  temp_data = []

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

    # load the matchups data
    matchups = pd.read_csv('./matchup data/matchups.csv')

    # drop unnamed columns
    matchups = matchups.loc[:, ~matchups.columns.str.contains('^Unnamed')]

    log_losses = {}
    predictions = {}
    
    # for each matchup, predict the winner
    for index, row in matchups.iterrows():
      stats = pd.DataFrame(columns=features)
      stats[features] = df[df['kaggle_id'] == row['kaggle_id']][features].values - df[df['kaggle_id'] == row['kaggle_id_2']][features].values

      pred = model.predict_proba(stats[features])
      matchup_name = f"{row['team']} vs {row['team_2']}"
      predictions[matchup_name] = pred[0][1]

      if not row['outcome']:
        continue
      # calculate the log loss of the prediction
      log_loss = -1 * (row['outcome'] * np.log(pred[0][1]) + (1 - row['outcome']) * np.log(pred[0][0]))
      log_losses[matchup_name] = log_loss

    # calculate the average log loss
    avg_log_loss = np.mean(list(log_losses.values()))
    print(f"Calculated {team} avg log loss: {avg_log_loss}!")

    temp_data.append({
      'team': team,
      'image': metadata['image'],
      'members': metadata['members'],
      'log_losses': log_losses,
      'predictions': predictions,
      'avg_log_loss': avg_log_loss
    })
  
  # sort temp_data by avg log loss
  temp_data = sorted(temp_data, key=lambda x: x['avg_log_loss'])

  data = temp_data

  