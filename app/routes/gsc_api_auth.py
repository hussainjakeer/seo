import flask
import pandas as pd
from app import app
from flask import url_for, redirect, session, request

import google.oauth2.credentials
import googleapiclient.discovery
from google_auth_oauthlib import flow as gao_flow


CLIENT_SECRETS_FILE = "web_creds.json"


SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly', 'https://www.googleapis.com/auth/webmasters',
          'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']

API_SERVICE_NAME = 'searchconsole'
API_VERSION = 'v1'

@app.route('/gsc_authorize')
def gsc_authorize():

    flow = gao_flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('gsc_oauth2callback', _external = True)
    authorization_uri, state = flow.authorization_url(access_type = "offline", include_granted_scopes = "true")
    flask.session['state'] = state
    return redirect(authorization_uri)


@app.route('/gsc_oauth2callback')
def gsc_oauth2callback():
    flow = gao_flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=session['state'])
    flow.redirect_uri = url_for('gsc_oauth2callback', _external=True)
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)

    user_info = fetch_user_info(credentials)
    session.update({
        "user_email": user_info['email'],
        "user_name": user_info['name'],
        "profile_pic": user_info.get('profile_pic', '')
    })

    return redirect(url_for('dashboard'))


## credentials to dict format
def credentials_to_dict(credentials):
    return {'token': credentials.token, 'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri, 'client_id': credentials.client_id,
            'client_secret': credentials.client_secret, 'scopes': credentials.scopes}


def fetch_user_info(credentials):
    people_service = googleapiclient.discovery.build('people', 'v1', credentials=credentials)
    user_info = people_service.people().get(resourceName='people/me', personFields='names,emailAddresses,photos').execute()
    return {
        'email': user_info['emailAddresses'][0]['value'],
        'name': user_info['names'][0]['displayName'],
        'profile_pic': user_info.get('photos', [{}])[0].get('url', '')
    }


## building webmaster service
def build_gsc_service():
    credentials = google.oauth2.credentials.Credentials(**session["credentials"])
    search_console_service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials
    )
    return search_console_service



## Fetching data from google search console
def fetch_search_console_data(webmasters_service, website_url,
                              start_date, end_date, dimensions, dimensionFilterGroups = None):
    
    all_responses = []
    start_row = 0

    # Loop until all rows have been retrieved
    while True:
        # Build the request body for the API call
        request_body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            # "dimensionFilterGroups": dimensionFilterGroups,
            "rowLimit": 25000,
            "dataState": "final",
            "startRow": start_row,
            # 'aggregationType': 'byPage'
        }

        # Call the API with the request body
        response_data = webmasters_service.searchanalytics().query(siteUrl=website_url, body=request_body).execute()
        rows = response_data.get("rows", [])
        all_responses.extend([each["keys"] + [each['clicks'], each['impressions'], each['ctr'], each['position']] for each in rows])

        start_row += len(rows)
        if len(rows) < 25000:
            break

    return pd.DataFrame(all_responses, columns=dimensions + ['Clicks', 'Impressions', 'CTR', 'Position'])
