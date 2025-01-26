import logging
from flask import Flask, render_template, request, jsonify, Response
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import os
import xml
import json
import xmltodict

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# OAuth configuration
client_id = 'ZTIzYTA1NWQtMjhmOC00MDlmLWE0ZmEtYjg2YjVjM2UyZTIy'
client_secret = 'l68p1zbj3yg94j6tw0mk1itakv8n4lzwzsbywf41m3ezntmpzh95os5uhmzdps73hzst497j334v05wfh35qayeye2tvsh1wioa'
token_url = 'https://wd5-impl-services1.workday.com/ccx/oauth2/avalonbay2/token'
workday_api_url = 'https://wd5-impl-services1.workday.com/ccx/service/avalonbay2/Human_Resources/v42.0'

# The refresh token should be securely stored
refresh_token = os.getenv('WORKDAY_REFRESH_TOKEN', 'xfflryyf1j4zmua5nux8m4xbs1jzyjziwnnkuqb9ghold24acecrnm3ef4s0ok7jrku19pxhigf06776j5v97agjrg9p62vs5uk')

# OAuth2 session setup (client credentials flow + refresh token management)
client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)

# Function to get a new access token using the refresh token
def get_oauth_token():
    logging.debug('Attempting to refresh OAuth token...')
    try:
        if refresh_token:
            token = oauth.refresh_token(token_url, client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)
            logging.debug(f"OAuth token obtained: {token['access_token']}")
            return token
        else:
            logging.error('Refresh token is missing!')
            return None
    except Exception as e:
        logging.error(f"Error during OAuth token refresh: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Get input values from the form
        employee_id = request.form['employee_id']
        as_of_date = request.form['as_of_date']
        
        logging.debug(f"Form input received: employee_id={employee_id}, as_of_date={as_of_date}")

        # Step 1: Get OAuth token using the refresh token
        token = get_oauth_token()
        if not token:
            logging.error('OAuth authentication failed, unable to refresh token.')
            return jsonify({'error': 'OAuth authentication failed, unable to refresh token.'}), 400

        # Step 2: Build the Workday request body (SOAP request)
        request_body = f"""
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
              xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <env:Body>
        <wd:Employee_Get xmlns:wd="urn:com.workday/bsvc"
                         wd:As_Of_Date="{as_of_date}"
                         wd:version="v42.0">
            <wd:Employee_Reference>
                <wd:Integration_ID_Reference>
                    <wd:ID wd:System_ID="WD-EMPLID">{employee_id}</wd:ID>
                </wd:Integration_ID_Reference>
            </wd:Employee_Reference>
        </wd:Employee_Get>
    </env:Body>
</env:Envelope>
"""

        logging.debug(f"SOAP request body constructed: {request_body}")

        # Step 3: Send the SOAP request to Workday API
        headers = {
            'Content-Type': 'application/xml', 
            'Authorization': f'Bearer {token["access_token"]}'
        }
        logging.debug('Sending SOAP request to Workday...')
        response = requests.post(workday_api_url, data=request_body, headers=headers)

        logging.debug(f"Response Status Code: {response.status_code}")
        logging.debug(f"Response Content: {response.text}")

        if response.status_code != 200:
            logging.error(f'Error submitting request: {response.text}')
            return jsonify({'error': f'Error submitting request: {response.text}'}), 500

        # Step 4: Process response 
        # Return the XML content as a response
        return Response(response.text, content_type='application/xml')

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
