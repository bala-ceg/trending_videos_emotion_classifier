import streamlit as st
import tweepy
import re
import mindsdb_sdk as mdb
import pandas as pd
import os
import langid
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

MDB_EMAIL=os.environ['email']
MDB_PWD=os.environ['pwd']
MODEL_NAME=os.environ['model']

# Define function to predict emotions
def predict_from_mindsdb(df: pd.DataFrame):
    server=mdb.connect(login=MDB_EMAIL,password=MDB_PWD)
    model=server.get_project('mindsdb').get_model(MODEL_NAME)
    pred_df = pd.DataFrame(columns=['text'])
    pred_df['text'] = df['text']
    try: 
        ret_df = model.predict(pred_df)
    except Exception as e:
        print('Not able to generate predictions at the moment')
    return ret_df


# Set up YouTube API key
api_key = os.environ['youtube_api_key']
youtube = build('youtube', 'v3', developerKey=api_key)

# Define the list of regions to retrieve trending videos for
regions = ['AR', 'AU', 'AT', 'BE', 'BR', 'CA', 'CL', 'CO', 'CZ', 'DK', 'EG', 'FI', 'FR', 'DE', 'HK', 'HU', 'IN', 'ID', 'IE', 'IL', 'IT', 'JP', 'KE', 'MY', 'MX', 'MA', 'NL', 'NZ', 'NG', 'NO', 'PH', 'PL', 'PT', 'RO', 'RU', 'SA', 'SG', 'ZA', 'KR', 'ES', 'SE', 'CH', 'TW', 'TH', 'TR', 'UA', 'AE', 'GB', 'US', 'VN']

columns = ['trending_date', 'title', 'channelTitle', 'view_count', 'likes','description']
df = pd.DataFrame(columns=columns)

# To retrieve the trending videos for a given region
def get_trending_videos(region_code):
    resource = youtube.videos().list(
        part='snippet,statistics',
        chart='mostPopular',
        regionCode=region_code,
        maxResults=50
    )

    try:
        response = resource.execute()
        for video in response['items']:
            try:
                # Get the video details
                trending_date = video['snippet']['publishedAt']
                title = video['snippet']['title']
                channelTitle = video['snippet']['channelTitle']
                view_count = video['statistics'].get('viewCount', 0)
                likes = video['statistics'].get('likeCount', 0)
                description = video['snippet'].get('description', '')

                if langid.classify(title)[0] == 'en':

                  # Add the video details to the DataFrame
                  df = pd.concat([df, pd.DataFrame({
                      'trending_date': [trending_date],
                      'text': [title],
                      'channelTitle': [channelTitle],
                      'view_count': [view_count],
                      'likes': [likes],
                      'description': [description]
                  })], ignore_index=True)

            except KeyError as e:
                print(f"Skipping video with missing field: {str(e)}")
                continue

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")

    return df

# Define Streamlit app
st.title('Trending Youtube Videos Emotion Predictor - Powered by MindsDB')
st.write('Pick a region to predict the sentiment of trending videos')
# Define the region selection dropdown
selected_region = st.selectbox('Select a region:', regions)

# Retrieve the trending videos for the selected region
videos = get_trending_videos(selected_region)

# Display the videos as a table
if videos is not None:
    try:
        df = pd.DataFrame(videos)
        df2 = predict_from_mindsdb(df)
        df = pd.concat([df, df2], axis=1)
        df = df.rename(columns={'text': 'Youtube_Video_title','sentiment': 'video_sentiment'}) 
        df = df[['Youtube_Video_title', 'video_sentiment']]
        st.dataframe(df) 
    except Exception as e:
            st.error(f'Error fetching predictions: {e}åå')
else:
    st.write('No trending videos available in english for the selected region.')


