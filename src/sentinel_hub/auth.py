"""
Sentinel Hub Authentication Module - Copernicus Data Space
Version avec username/password
"""

import requests
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class SentinelHubAuth:
    """Manages authentication with Copernicus Data Space API"""
    
    TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize authentication manager
        
        Args:
            username: Copernicus username/email (or set COPERNICUS_USERNAME env var)
            password: Copernicus password (or set COPERNICUS_PASSWORD env var)
        """
        self.username = username or os.getenv('COPERNICUS_USERNAME')
        self.password = password or os.getenv('COPERNICUS_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError(
                "Copernicus credentials not provided. "
                "Set COPERNICUS_USERNAME and COPERNICUS_PASSWORD in .env file"
            )
        
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        print(f"Authenticating as: {self.username}")
    
    def get_token(self) -> str:
        """
        Get valid access token (fetches new one if expired)
        
        Returns:
            Valid access token
        """
        if self._is_token_valid():
            print("Using cached token")
            return self.access_token
        
        print("Fetching new token...")
        return self._fetch_new_token()
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Add 5-minute buffer before expiry
        return datetime.now() < (self.token_expires_at - timedelta(minutes=5))
    
    def _fetch_new_token(self) -> str:
        """Fetch new access token from Copernicus Data Space"""
        payload = {
            'grant_type': 'password',
            'username': self.username,
            'password': self.password,
            'client_id': 'cdse-public'
        }
        
        try:
            response = requests.post(
                self.TOKEN_URL, 
                data=payload, 
                timeout=30,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            print(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            self.access_token = data['access_token']
            
            expires_in = data.get('expires_in', 600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"Token obtained successfully!")
            print(f"Token expires at: {self.token_expires_at.strftime('%H:%M:%S')}")
            
            return self.access_token
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error {e.response.status_code}")
            print(f"Response: {e.response.text}")
            
            if e.response.status_code == 401:
                raise Exception(
                    "Authentication failed! Check your credentials in .env file"
                )
            else:
                raise Exception(f"Failed to fetch token: {e}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while fetching token: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Test authentification Copernicus Data Space")
    print("=" * 60)
    
    try:
        auth = SentinelHubAuth()
        token = auth.get_token()
        
        print(f"\nSUCCESS!")
        print(f"Token (30 premiers caracteres): {token[:30]}...")
        print(f"Token complet: {len(token)} caracteres")
        
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("\nVerifie ton fichier .env:")
        print("  COPERNICUS_USERNAME=ton_email")
        print("  COPERNICUS_PASSWORD=ton_mot_de_passe")
        
    except Exception as e:
        print(f"\nAuthentication Error: {e}")
        print("\nSteps to fix:")
        print("1. Compte sur dataspace.copernicus.eu")
        print("2. Email confirme")
        print("3. Identifiants corrects dans .env")