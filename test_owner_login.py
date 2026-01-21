import requests
import re

# First, get the CSRF token
session = requests.Session()
response = session.get('http://localhost:8000/owner-login/')

# Extract CSRF token from the response
csrf_token_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', response.text)
if csrf_token_match:
    csrf_token = csrf_token_match.group(1)
    print(f"✓ Got CSRF token: {csrf_token}")
    
    # Now test the login
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'phone': '07700000000',
        'password': 'admin123456',
        'owner_key': 'OWNER2025'
    }
    
    login_response = session.post('http://localhost:8000/owner-login/', data=login_data)
    print(f"✓ Login response status: {login_response.status_code}")
    print(f"✓ Login response URL: {login_response.url}")
    
    # Check if we got redirected (which means login was successful)
    if login_response.status_code == 200 and 'dashboard' in login_response.url:
        print("✓ Login successful! Redirected to dashboard")
        
        # Test if we're actually logged in by accessing a protected page
        dashboard_response = session.get('http://localhost:8000/dashboard/')
        print(f"✓ Dashboard access status: {dashboard_response.status_code}")
        
        if 'تم تسجيل دخول المالك بنجاح' in login_response.text or dashboard_response.status_code == 200:
            print("✓ Owner login is working correctly!")
        else:
            print("✗ Dashboard access failed")
            
    elif login_response.status_code == 302:
        print("✓ Login successful! (302 redirect)")
    else:
        print("✗ Login failed")
        print("Response content:", login_response.text[:500])
else:
    print("✗ Could not find CSRF token")
    print("Response content:", response.text[:500])
