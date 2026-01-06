from dotenv import load_dotenv
import os
import requests

load_dotenv()

username = os.getenv('COPERNICUS_USERNAME')
password = os.getenv('COPERNICUS_PASSWORD')

print(f"Username: {username}")
print(f"Password: {'*' * len(password) if password else 'None'}")

# Test authentication avec username/password
payload = {
    'grant_type': 'password',
    'username': username,
    'password': password,
    'client_id': 'cdse-public'  # Client public par défaut
}

url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

try:
    response = requests.post(url, data=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Authentication réussie!")
        data = response.json()
        print(f"Token: {data['access_token'][:50]}...")
        print(f"\nExpire dans: {data.get('expires_in', 'N/A')} secondes")
    else:
        print("❌ Authentication échouée!")
        print(f"Erreur: {response.text}")
        
except Exception as e:
    print(f"❌ Erreur: {e}")