from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Workday OAuth credentials and endpoints
CLIENT_ID = "ZTIzYTA1NWQtMjhmOC00MDlmLWE0ZmEtYjg2YjVjM2UyZTIy"
CLIENT_SECRET = "l68p1zbj3yg94j6tw0mk1itakv8n4lzwzsbywf41m3ezntmpzh95os5uhmzdps73hzst497j334v05wfh35qayeye2tvsh1wioa"
REFRESH_TOKEN = "xfflryyf1j4zmua5nux8m4xbs1jzyjziwnnkuqb9ghold24acecrnm3ef4s0ok7jrku19pxhigf06776j5v97agjrg9p62vs5uk"
TOKEN_URL = "https://wd5-impl-services1.workday.com/ccx/oauth2/avalonbay2/token"
WORKDAY_API_URL = "https://wd5-impl-services1.workday.com/ccx/service/avalonbay2/Human_Resources/v42.0"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    username = request.form.get("username")
    user_group = request.form.get("user_group")

    # Step 1: OAuth Authentication
    try:
        token = get_oauth_token()
    except Exception as e:
        return jsonify({"status": "error", "message": f"OAuth Authentication Failed: {str(e)}"})

    # Step 2: Build SOAP/XML Request
    try:
        soap_request = build_soap_request(username, user_group)
        print("SOAP Request Built:")
        print(soap_request)  # Print the built SOAP request here
    except Exception as e:
        return jsonify({"status": "error", "message": f"SOAP Request Build Failed: {str(e)}"})

    # Step 3: Submit Request to Workday
    try:
        response = submit_to_workday(token, soap_request)
        return jsonify({"status": "success", "message": "Request Submitted Successfully", "response": response})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Workday Request Failed: {str(e)}"})

def get_oauth_token():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        error_message = response.json().get("error_description", "Unknown error")
        raise Exception(f"Failed to get access token: {error_message}")

def build_soap_request(username, user_group):
    if not username or not user_group:
        raise ValueError("Both username and user_group must be provided.")

    soap_request = f"""
    <?xml version="1.0" encoding="UTF-8"?>
    <env:Envelope 
        xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">        
        <env:Body>
            <wd:Update_User-Based_Security_Group_Assignments_Request
                xmlns:wd="urn:com.workday/bsvc"
                wd:version="v42.0">
                <wd:Update_User-Based_Security_Group_Assignments_Data>
                    <wd:Workday_Account_Reference>
                        <wd:ID wd:type="WorkdayUserName">{username}</wd:ID>
                    </wd:Workday_Account_Reference>
                    <wd:Add_User-Based_Security_Group_Reference>
                        <wd:ID wd:type="Tenant_Security_Group_ID">{user_group}</wd:ID>
                    </wd:Add_User-Based_Security_Group_Reference>
                    <wd:Comment>Assigning user to security group</wd:Comment>
                </wd:Update_User-Based_Security_Group_Assignments_Data>
            </wd:Update_User-Based_Security_Group_Assignments_Request>
        </env:Body>
    </env:Envelope>
    """
    return soap_request

def submit_to_workday(token, soap_request):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/xml"
    }

    # Print the endpoint and HTTP method being used
    print(f"\nRequest Method: PUT")
    print(f"Request Endpoint: {WORKDAY_API_URL}")
    
    # Print headers, request body, and token for debugging before sending the request
    print("\nAuthorization Header:")
    print(f"Authorization: Bearer {token}")
    
    print("\nSOAP Request Sent to Workday:")
    print(soap_request)  # Print the SOAP request body
    
    print("\nHeaders Sent to Workday:")
    print(headers)  # Print the headers

    # Make the POST request to Workday
    response = requests.post(WORKDAY_API_URL, data=soap_request, headers=headers)
    
    # Log the response for debugging
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.text}")  # Print full response for debugging
    
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Workday Request Failed: {response.text}")



if __name__ == "__main__":
    app.run(debug=True)