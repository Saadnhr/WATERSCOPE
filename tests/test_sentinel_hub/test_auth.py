"""
Tests pour le module d'authentification Sentinel Hub
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import os

# Import du module à tester
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from sentinel_hub.auth import SentinelHubAuth


class TestSentinelHubAuth:
    """Tests pour la classe SentinelHubAuth"""
    
    def test_init_avec_credentials(self):
        """Test initialisation avec credentials fournis"""
        auth = SentinelHubAuth(
            username="test@example.com",
            password="test_password"
        )
        
        assert auth.username == "test@example.com"
        assert auth.password == "test_password"
        assert auth.access_token is None
        assert auth.token_expires_at is None
    
    def test_init_sans_credentials(self):
        """Test initialisation sans credentials (devrait lever ValueError)"""
        # Sauvegarder les vraies valeurs
        old_username = os.environ.get('COPERNICUS_USERNAME')
        old_password = os.environ.get('COPERNICUS_PASSWORD')
        
        # Supprimer temporairement
        if 'COPERNICUS_USERNAME' in os.environ:
            del os.environ['COPERNICUS_USERNAME']
        if 'COPERNICUS_PASSWORD' in os.environ:
            del os.environ['COPERNICUS_PASSWORD']
        
        # Test
        with pytest.raises(ValueError):
            SentinelHubAuth()
        
        # Restaurer
        if old_username:
            os.environ['COPERNICUS_USERNAME'] = old_username
        if old_password:
            os.environ['COPERNICUS_PASSWORD'] = old_password
    
    @patch('sentinel_hub.auth.requests.post')
    def test_fetch_new_token_success(self, mock_post):
        """Test récupération d'un nouveau token avec succès"""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'fake_token_123',
            'expires_in': 600
        }
        mock_post.return_value = mock_response
        
        # Test
        auth = SentinelHubAuth(
            username="test@example.com",
            password="test_password"
        )
        token = auth.get_token()
        
        # Vérifications
        assert token == 'fake_token_123'
        assert auth.access_token == 'fake_token_123'
        assert auth.token_expires_at is not None
        
        # Vérifier que l'API a été appelée
        mock_post.assert_called_once()
    
    @patch('sentinel_hub.auth.requests.post')
    def test_fetch_new_token_echec_401(self, mock_post):
        """Test échec d'authentification (401)"""
        # Mock de la réponse API avec erreur
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = Exception("401 Error")
        mock_post.return_value = mock_response
        
        # Test
        auth = SentinelHubAuth(
            username="wrong@example.com",
            password="wrong_password"
        )
        
        with pytest.raises(Exception):
            auth.get_token()
    
    def test_is_token_valid_pas_de_token(self):
        """Test validation quand il n'y a pas de token"""
        auth = SentinelHubAuth(
            username="test@example.com",
            password="test_password"
        )
        
        assert auth._is_token_valid() is False
    
    def test_is_token_valid_token_expire(self):
        """Test validation avec un token expiré"""
        auth = SentinelHubAuth(
            username="test@example.com",
            password="test_password"
        )
        
        # Simuler un token expiré
        auth.access_token = "fake_token"
        auth.token_expires_at = datetime.now() - timedelta(minutes=10)
        
        assert auth._is_token_valid() is False
    
    def test_is_token_valid_token_valide(self):
        """Test validation avec un token valide"""
        auth = SentinelHubAuth(
            username="test@example.com",
            password="test_password"
        )
        
        # Simuler un token valide
        auth.access_token = "fake_token"
        auth.token_expires_at = datetime.now() + timedelta(minutes=10)
        
        assert auth._is_token_valid() is True
    
    @patch('sentinel_hub.auth.requests.post')
    def test_get_token_utilise_cache(self, mock_post):
        """Test que get_token utilise le cache si le token est encore valide"""
        # Premier appel - mock de la réponse
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'fake_token_123',
            'expires_in': 600
        }
        mock_post.return_value = mock_response
        
        auth = SentinelHubAuth(
            username="test@example.com",
            password="test_password"
        )
        
        # Premier appel
        token1 = auth.get_token()
        
        # Deuxième appel (devrait utiliser le cache)
        token2 = auth.get_token()
        
        # Vérifications
        assert token1 == token2
        # L'API ne devrait être appelée qu'une seule fois
        assert mock_post.call_count == 1


# Fixtures pytest
@pytest.fixture
def auth_instance():
    """Fixture pour créer une instance d'authentification pour les tests"""
    return SentinelHubAuth(
        username="test@example.com",
        password="test_password"
    )


# Tests d'intégration (nécessitent de vraies credentials)
@pytest.mark.integration
class TestSentinelHubAuthIntegration:
    """Tests d'intégration (nécessitent vraies credentials)"""
    
    def test_authentification_reelle(self):
        """Test avec de vraies credentials (skip si pas configuré)"""
        # Ce test sera skippé si les credentials ne sont pas configurées
        if not os.getenv('COPERNICUS_USERNAME'):
            pytest.skip("Credentials non configurées")
        
        auth = SentinelHubAuth()
        token = auth.get_token()
        
        assert token is not None
        assert len(token) > 0


if __name__ == "__main__":
    # Lancer les tests
    pytest.main([__file__, '-v'])