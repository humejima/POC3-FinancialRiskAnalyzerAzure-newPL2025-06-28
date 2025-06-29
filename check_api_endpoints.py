import requests
import json

def check_api_endpoints():
    """Check the API endpoints for risk data"""
    base_url = "https://cab8882f-b03a-4857-a5fa-23701902e586-00-3i28ryiq808gz.pike.replit.dev"
    ja_code = "JA002"
    year = "2025"
    
    # Check risk issues API
    issues_url = f"{base_url}/api/risk_issues?ja_code={ja_code}&year={year}"
    print(f"Checking API: {issues_url}")
    try:
        issues_response = requests.get(issues_url)
        print(f"Status Code: {issues_response.status_code}")
        if issues_response.status_code == 200:
            issues_data = issues_response.json()
            print("Response (first 500 chars):")
            print(json.dumps(issues_data, indent=2, ensure_ascii=False)[:500])
            print("...")
        else:
            print(f"Failed to get response: {issues_response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n" + "="*40 + "\n")
    
    # Check risk data API
    data_url = f"{base_url}/api/risk_data?ja_code={ja_code}&year={year}"
    print(f"Checking API: {data_url}")
    try:
        data_response = requests.get(data_url)
        print(f"Status Code: {data_response.status_code}")
        if data_response.status_code == 200:
            risk_data = data_response.json()
            print("Response:")
            print(json.dumps(risk_data, indent=2, ensure_ascii=False))
        else:
            print(f"Failed to get response: {data_response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_api_endpoints()