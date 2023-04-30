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
regions = {
    'AR': 'Argentina',
    'AU': 'Australia',
    'AT': 'Austria',
    'BE': 'Belgium',
    'BR': 'Brazil',
    'CA': 'Canada',
    'CL': 'Chile',
    'CO': 'Colombia',
    'CZ': 'Czech Republic',
    'DK': 'Denmark',
    'EG': 'Egypt',
    'FI': 'Finland',
    'FR': 'France',
    'DE': 'Germany',
    'HK': 'Hong Kong',
    'HU': 'Hungary',
    'IN': 'India',
    'ID': 'Indonesia',
    'IE': 'Ireland',
    'IL': 'Israel',
    'IT': 'Italy',
    'JP': 'Japan',
    'KE': 'Kenya',
    'MY': 'Malaysia',
    'MX': 'Mexico',
    'MA': 'Morocco',
    'NL': 'Netherlands',
    'NZ': 'New Zealand',
    'NG': 'Nigeria',
    'NO': 'Norway',
    'PH': 'Philippines',
    'PL': 'Poland',
    'PT': 'Portugal',
    'RO': 'Romania',
    'RU': 'Russia',
    'SA': 'Saudi Arabia',
    'SG': 'Singapore',
    'ZA': 'South Africa',
    'KR': 'South Korea',
    'ES': 'Spain',
    'SE': 'Sweden',
    'CH': 'Switzerland',
    'TW': 'Taiwan',
    'TH': 'Thailand',
    'TR': 'Turkey',
    'UA': 'Ukraine',
    'AE': 'United Arab Emirates',
    'GB': 'United Kingdom',
    'US': 'United States',
    'VN': 'Vietnam'
}



def get_trending_videos(region_code):
    # Define the resource we want to get (trending videos in this case)
    resource = youtube.videos().list(
        part='snippet,statistics',
        chart='mostPopular',
        regionCode=region_code,
        maxResults=50
    )

    videos = []
    try:
        # Execute the request and extract the required information from the API response
        response = resource.execute()
        for video in response['items']:
            try:
                # Get the video details
                trending_date = video['snippet']['publishedAt']
                title = video['snippet']['title']
                channelTitle = video['snippet']['channelTitle']
                view_count = video['statistics'].get('viewCount', 0)
                likes = video['statistics'].get('likeCount', 0)
                dislikes = video['statistics'].get('dislikeCount', 0)
                
                if langid.classify(title)[0] == 'en':
                    # Add the video details to the list of videos
                    videos.append({
                        'Trending Date': trending_date,
                        'text': title,
                        'Channel Title': channelTitle,
                        'Views': view_count,
                        'Likes': likes,
                        'Dislikes': dislikes
                    })

            except KeyError as e:
                print(f"Skipping video with missing field: {str(e)}")
                continue

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return None

    return videos

# Define Streamlit app
st.title('Trending Youtube Videos Emotion Predictor - Powered by MindsDB')
st.write('Pick a region to predict the sentiment of trending videos')
# Define the region selection dropdown
region_selected = st.selectbox('Select a region:', list(regions.values()))
selected_region = list(regions.keys())[list(regions.values()).index(region_selected)]

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
