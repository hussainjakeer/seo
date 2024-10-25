import os
import re
from app import app
import pandas as pd
from app.features import *
import googleapiclient.discovery
import google.oauth2.credentials
from datetime import datetime, timedelta
from app.routes.gsc_api_auth import API_SERVICE_NAME, API_VERSION
from flask import render_template, request, url_for, redirect, session, template_rendered
from app.routes.gsc_api_auth import build_gsc_service, fetch_search_console_data


# @app.route('/')
# def index():
#     # Read the CSV file
#     df = pd.read_csv('data.csv')
#     # Convert the DataFrame to a dictionary
#     data_dict = df.to_dict(orient='records')
#     return render_template('index.html', data=data_dict)

@app.route('/', methods = ["GET", "POST"])
@app.route("/dashboard", methods = ["GET", "POST"])
def dashboard():
    # Check if user is authenticated
    if "credentials" not in session:
        return redirect(url_for('gsc_authorize'))
    
    # Retrieve user information and setup form URL
    user_name = session["user_name"]
    user_email = session["user_email"]
    profile_pic = session["profile_pic"]
    
    # Initialize selected property and date range variables
    selected_property = session.get('selected_property')
    start_date = session.get('start_date')
    end_date = session.get('end_date')
    site_list_sorted = session.get("site_list_sorted")
    
    all_dimensions = {
        "date": ["DATE"],
        "query": ["QUERY"],
        "country": ["COUNTRY"],
        "device": ["DEVICE"],
        "page": ["PAGE"],
        "all_dimensions_table" : ["QUERY", "PAGE", "COUNTRY", "DEVICE", "DATE"]
        }
    
    # Handle POST request for data fetching
    if request.method == "POST":
        try:
            # Retrieve selected property and date range from form
            selected_property = request.form.get("projects-ids")
            start_date = request.form.get("startDate")
            end_date = request.form.get("endDate")
            
            # Store selected values in session
            session['selected_property'] = selected_property
            session['start_date'] = start_date
            session['end_date'] = end_date
            
            # Fetching data from Google Search Console
            webmasters_service = build_gsc_service()
            
            # Clear existing DataFrames from the session
            if "data_dataframe" in session:
                for key in all_dimensions:
                    session.pop(f'{key}_dataframe', None)
            
            # Fetch data for each dimension and store in session
            for key, value in all_dimensions.items():
                results_df = fetch_search_console_data(webmasters_service, selected_property, start_date, end_date, value)
                session[f'{key}_dataframe'] = results_df.to_dict()
            
            # Convert date DataFrame to calculate metrics
            date_dataframe = pd.DataFrame(session["date_dataframe"])
            click_sum = sum_finder(date_dataframe, 'Clicks')
            impression_sum = sum_finder(date_dataframe, 'Impressions')
            ctr_sum = (date_dataframe["Clicks"].sum() / date_dataframe["Impressions"].sum()) * 100 if date_dataframe["Impressions"].sum() > 0 else 0
            ctr_sum = f"{ctr_sum:.2f}%"
            
            
            return render_template("dashboard.html", site_list = site_list_sorted, selected_property = selected_property,
                               start_date = session["start_date"], end_date = session["end_date"],
                               click_sum = click_sum, ctr_sum = ctr_sum, impression_sum = impression_sum,
                               data = date_dataframe.to_dict(orient='records'))
            
        except Exception as e:
            return f"""<h1>{e}</h1>"""
    
    try:
        # If no property is selected, fetch the list of properties
        if not selected_property:
            credentials = google.oauth2.credentials.Credentials(**session['credentials'])
            search_console_service = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

            # Retrieve the list of properties from Google Search Console
            site_list = search_console_service.sites().list().execute()
            try:
                site_list = site_list["siteEntry"]
            except Exception as e:
                return "<h1>Please add Projects to your search console.</h1>"
            
            site_list_sorted = [site["siteUrl"] for site in site_list  if site['permissionLevel'] != 'siteUnverifiedUser']
            site_list_sorted = sorted(site_list_sorted)
            session["site_list_sorted"] = site_list_sorted
            
            # Set the first property as selected
            selected_property = site_list_sorted[0]
            session['selected_property'] = selected_property
            
            # Set the date range
            today = datetime.today()
            start_month = today.month - 6
            start_year = today.year
            if start_month <= 0:
                start_month += 12
                start_year -= 1
            start_date = datetime(start_year, start_month, 1)
            session['start_date'] = start_date.strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'
            session['end_date'] = today.strftime('%Y-%m-%d')
            start_date, end_date = session['start_date'], session["end_date"]
            
            # Fetch initial data for all dimensions
            for key, value in all_dimensions.items():
                results_df = fetch_search_console_data(search_console_service, selected_property, session['start_date'], session['end_date'], value)
                session[f'{key}_dataframe'] = results_df.to_dict()
            
        # Convert date DataFrame to calculate metrics
        date_dataframe = pd.DataFrame(session["date_dataframe"])
        click_sum = sum_finder(date_dataframe, 'Clicks')
        impression_sum = sum_finder(date_dataframe, 'Impressions')
        ctr_sum = (date_dataframe["Clicks"].sum() / date_dataframe["Impressions"].sum()) * 100 if date_dataframe["Impressions"].sum() > 0 else 0
        ctr_sum = f"{ctr_sum:.2f}%"
        print(date_dataframe.columns)
        return render_template("dashboard.html", site_list = site_list_sorted, selected_property = selected_property,
                               start_date = session["start_date"], end_date = session["end_date"],
                               click_sum = click_sum, ctr_sum = ctr_sum, impression_sum = impression_sum,
                               data = date_dataframe.to_dict(orient='records'))
    
    except Exception as e:
            return f"""<h1>{e}</h1>"""

