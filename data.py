import pandas as pd
import numpy as np
import tensorflow as tf
import keras
import os
import base64
import json
import argparse
from dotenv import load_dotenv
from requests import post,get

token = ''
output = pd.DataFrame()
count = 0

def get_env():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    return client_id,client_secret
    

def get_token():
    client_id,client_secret = get_env()
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes),'utf-8')

    url = "https://accounts.spotify.com/api/token"
    header = {
        "Authorization" : "Basic " + auth_base64,
        "Content-Type" : "application/x-www-form-urlencoded"
    }
    data = {"grant_type" : "client_credentials"}
    result = post(url,headers=header,data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization" : "Bearer " + token}

def get_track_features(track_id):
    global token
    url = "https://api.spotify.com/v1/audio-features"
    header = get_auth_header(token)
    query = f"{track_id}"
    query_url = url + '/' + query
    result = get(query_url,headers=header)
    json_result = json.loads(result.content)
    return(json_result)

def get_track_info(track_id):
    global token
    url = "https://api.spotify.com/v1/tracks"
    header = get_auth_header(token)
    query = f"{track_id}"
    query_url = url + '/' + query
    result = get(query_url,headers=header)
    track_info = json.loads(result.content)
    return(track_info)

def get_track_id(album_id,total_track,release_date):
    global token
    global output
    global count

    url = "https://api.spotify.com/v1/albums"
    header = get_auth_header(token)
    query = f"{album_id}"
    query_url = url + '/' + query
    result = get(query_url,headers=header)
    json_result = json.loads(result.content)
    if('error' in json_result.keys()):
        print('error album')
        return None
    # print(json_result)
    if len(json_result) == 0:
        print("no result")
        return None
    
    year,month,day = release_date.split('-')
    
    for i,track in enumerate(json_result['tracks']['items']):
        print('track id : ',track['id'])
        track_features = get_track_features(track['id'])
        if('error' in track_features.keys()):
            print('error feature')
            continue
        track_info = get_track_info(track['id'])
        if('error' in track_info.keys()):
            print('error track')
            continue
        artist_count = len(track_info['artists'])
        artist_name = ''
        for i in range(artist_count):
            artist_name += track_info['artists'][i]['name']
            if i != artist_count-1:
                artist_name+= ' & '


        track_dict = {'track_name':track['name'],'track_id':track['id'],'artist(s)_name':artist_name,
                      'artist_count':artist_count,'released_year':year,'released_month':month,'released_day':day,
                      'popularity':track_info['popularity'],'acousticness_%':track_features['acousticness']*100,
                      'danceability_%':track_features['danceability']*100,'duration_ms':track_features['duration_ms'],
                      'energy_%':track_features['energy']*100,'instrumentalness_%':track_features['instrumentalness']*100,
                      'key':track_features['key'],'liveness_%':track_features['liveness']*100,'loudness':track_features['loudness'],
                      'mode':track_features['mode'],'speechiness_%':track_features['speechiness']*100,'tempo(bpm)':track_features['tempo'],
                      'time_signature':track_features['time_signature'],'valence_%':track_features['valence']}
        # print(track_dict)
        output.loc[len(output.index)] = track_dict
        count+=1
        print('count track: ',count)
        


def search_for_year_album(start_year, end_year):
    global token
    for i in range(start_year,end_year+1):
        url = "https://api.spotify.com/v1/search"
        header = get_auth_header(token)
        query = f"q=year:{i}&type=album&limit=50"
        query_url = url + '?' + query
        result = get(query_url,headers=header)
        json_result = json.loads(result.content)
        if('error' in json_result.keys()):
            print(json_result)
            print('error search\n\n\n')
            continue
        if len(json_result) == 0:
            print("no result")
            return None
        # print(json_result['albums']['items'])
        global output

        for i,album in enumerate(json_result['albums']['items']):
            print('album id : ',album['id'])
            get_track_id(album['id'],album['total_tracks'],album['release_date'])

    output.to_csv('spotify_api.csv',index=False)
    # return json_result[0]
def search_for_year_track(start_year, end_year, turn):
    global token
    global output
    global count

    if os.path.exists('spotify_api_'+str(start_year)+'.csv'):
        file = 'spotify_api_'+str(start_year)+'.csv'
        output = pd.read_csv(file)

    for i in range(start_year,end_year+1):
        url = "https://api.spotify.com/v1/search"
        header = get_auth_header(token)
        query = f"q=year:{i}&type=track&limit=50&offset={50*turn}"
        query_url = url + '?' + query
        result = get(query_url,headers=header)
        json_result = json.loads(result.content)
        if('error' in json_result.keys()):
            print(json_result)
            print('error search\n\n\n')
            continue

        # print(json_result['albums']['items'])
        

        for i,track in enumerate(json_result['tracks']['items']):
            print('track id : ',track['id'])
            track_info = get_track_info(track['id'])
            if('error' in track_info.keys()):
                print(track_info)
                continue

            track_features = get_track_features(track['id'])
            if('error' in track_features.keys()):
                print(track_features)
                continue

            artist_count = len(track_info['artists'])
            artist_name = ''
            for i in range(artist_count):
                artist_name += track_info['artists'][i]['name']
                if i != artist_count-1:
                    artist_name+= ' & '
            date_precision = track_info['album']['release_date_precision']
            release_date = track_info['album']['release_date']
            if date_precision == 'day':
                year,month,day = release_date.split('-')
            elif date_precision == 'month':
                year,month = release_date.split('-')
                day = None
            elif date_precision == 'year':
                year = release_date
                month = None
                day = None
            track_dict = {'track_name':track['name'],'track_id':track['id'],'artist(s)_name':artist_name,
                        'artist_count':artist_count,'released_year':year,'released_month':month,'released_day':day,
                      'popularity':track_info['popularity'],'acousticness_%':track_features['acousticness']*100,
                      'danceability_%':track_features['danceability']*100,'duration_ms':track_features['duration_ms'],
                      'energy_%':track_features['energy']*100,'instrumentalness_%':track_features['instrumentalness']*100,
                      'key':track_features['key'],'liveness_%':track_features['liveness']*100,'loudness':track_features['loudness'],
                      'mode':track_features['mode'],'speechiness_%':track_features['speechiness']*100,'tempo(bpm)':track_features['tempo'],
                      'time_signature':track_features['time_signature'],'valence_%':track_features['valence']}
            output.loc[len(output.index)] = track_dict
            count+=1
            print('count track: ',count)
            # get_track_id(album['id'],album['total_tracks'],album['release_date'])

    output.to_csv('spotify_api_'+str(start_year)+'.csv',index=False)
    # return json_result[0]

def  read_csv():
    # raw_data = pd.read_csv("spotify-2023.csv",encoding='ISO-8859-1')
    # print(raw_data.info)
    pass

def main():
    global token 
    global output
    output = pd.DataFrame(columns=['track_name','track_id','artist(s)_name','artist_count','released_year',
                                   'released_month','released_day','popularity','acousticness_%',
                                   'danceability_%','duration_ms','energy_%','instrumentalness_%','key','liveness_%',
                                   'loudness','mode','speechiness_%','tempo(bpm)','time_signature','valence_%'
                                   ])
    token = get_token()

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-y','--year', type=int,default=2020,
                        help='search year')
    parser.add_argument('-t','--turn', type=int,default=0,
                        help='offset*50')
    args = parser.parse_args()
    search_for_year_track(args.year,args.year,args.turn)

def test_track():
    url = "https://api.spotify.com/v1/tracks"
    header = get_auth_header(token)
    query = f"08dz3ygXyFur6bL7Au8u8J"
    query_url = url + '/' + query
    result = get(query_url,headers=header)
    track_info = json.loads(result.content)
    print(track_info)
    artist_count = len(track_info['artists'])
    artist_name = ''
    for i in range(artist_count):
        artist_name += track_info['artists'][i]['name']
        if i != artist_count-1:
            artist_name+= ' & '

def test_album():
    url = "https://api.spotify.com/v1/albums"
    header = get_auth_header(token)
    query = f"4MZnolldq7ciKKlbVDzLm5"
    query_url = url + '/' + query
    result = get(query_url,headers=header)
    json_result = json.loads(result.content)
    print(json_result)
    if('error' in json_result.keys()):
        print('error album')
        return None


if __name__ == "__main__":
    main()
    # test_track()
    # test_album()