# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask, render_template
import fitbit
import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util

# Fitbit stuff
FITBIT_CLIENT_ID = '???'
FITBIT_CLIENT_SECRET = '???'

# Spotify stuff
SPOTIFY_CLIENT_ID = '???'
SPOTIFY_CLIENT_SECRET = '???'
spotify_username = 't_mnguyen'
redirect_uri = 'https://developer.spotify.com/dashboard/applications/2b7aa645d7b4400d95380a252017b3da'
scope = 'user-library-read playlist-modify-public playlist-read-private'

ACCESS_TOKEN = '???'
REFRESH_TOKEN = '???'

# Fitbit client
auth2_client = fitbit.Fitbit(FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN)

# Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id = SPOTIFY_CLIENT_ID, client_secret = SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager =  client_credentials_manager)
token = util.prompt_for_user_token(spotify_username, scope, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, redirect_uri)
if token:
   sp = spotipy.Spotify(auth=token)

# Start and end should be the start and end times of yesterday's workout, in strings.
def get_fit_statsHR(start, end):
    yesterday = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"))
    yesterday2 = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    today = str(datetime.datetime.now().strftime("%Y%m%d"))
    # Getting heart rate stuff from yesterday.
    fit_statsHR = auth2_client.intraday_time_series('activities/heart', base_date=yesterday2, detail_level='1min', start_time=start, end_time=end)
    return fit_statsHR

def get_yesterdays_bpm():
    yesterdays_bpm = []
    for bpm in fit_statsHR['activities-heart-intraday']['dataset']:
        yesterdays_bpm.append(bpm['value'])
    return yesterdays_bpm

# playlist_id should be a string id.
def get_playlist(playlist_id):
    return sp.user_playlist(spotify_username, playlist_id)

def get_song_ids(playlist):
    return [song['track']['id'] for song in playlist['tracks']['items']]

def get_song_features(playlist):
    return [sp.audio_features(song['track']['id']) for song in playlist['tracks']['items']]

# features returned from get_song_features.
def get_song_tempos(playlist, features):
    song_tempos = {}
    song_ids = get_song_ids(playlist)
    for i in range(len(song_ids)):
        song_tempos[song_ids[i]] = features[i][0]['tempo']
    return song_tempos

# Should get a list of song ids that correspond with the pace of yesterday's workout.
def get_songs_pace_filtered(workout_bpm, song_tempos):
    song_ids = []
    song_added = False
    for bpm in workout_bpm:
        song_added = False
        for (song_id, tempo) in song_tempos.items():
            if (bpm - 5) <= tempo <= (bpm + 5):
                song_ids.append(song_id)
                # Don't reuse the song in the playlist.
                del song_tempos[song_id]
                song_added = True
                break
        # If none of the songs match that bpm, we'll just skip over it.
    return song_ids

fit_statsHR = get_fit_statsHR("7:38", "8:05")

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    # print(fit_statsHR)
    # return fit_statsHR
    # return str(fit_statsHR)
    # return str(get_yesterdays_bpm())
    liked_playlist = get_playlist('7dURqGU9FfEAV6FtpHhGMn?si=9Cx7dV8PQ0-NDmGNwR9N2Q')
    liked_song_features = get_song_features(liked_playlist)
    tempos = get_song_tempos(liked_playlist, liked_song_features)
    bpm = get_yesterdays_bpm()
    # tempos = get_song_tempos(liked_playlist, get_song_features(liked_playlist))
    # return bpm
    # return str(get_song_tempos(liked_playlist, liked_song_features))
    return str(get_songs_pace_filtered(bpm, tempos))


# @app.route('/fitbit-auth')
# def user_authorized():
#     """Return a friendly HTTP greeting."""
#     return render_template('authorized.html', name='authorized')


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python37_app]
