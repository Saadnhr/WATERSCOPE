"""
Tests pour le module Process API (Sentinel Hub)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from sentinel_hub.process_api import ProcessAPIClient
from sentinel_hub.auth import SentinelHubAuth


class TestProcessAPIClient:
    """Tests pour la classe ProcessAPIClient"""
    
    def test_init(self):
        """Test initialisation du client"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        assert client.auth == mock_auth
        assert client.PROCESS_URL == "https://sh.dataspace.copernicus.eu/api/v1/process"
    
    @patch('sentinel_hub.process_api.requests.post')
    def test_calculate_water_surface_area_success(self, mock_post):
        """Test calcul de surface d'eau avec succès"""
        # Mock de l'authentification
        mock_auth = Mock()
        mock_auth.get_token.return_value = "fake_token_123"
        
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "water_pixels": 105080
            }
        }
        mock_post.return_value = mock_response
        
        # Client
        client = ProcessAPIClient(mock_auth)
        
        # Géométrie de test
        geometry = {
            "type": "Polygon",
            "coordinates": [[[58.5, 45.0], [59.5, 45.0], [59.5, 46.0], [58.5, 46.0], [58.5, 45.0]]]
        }
        
        # Période de test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Test
        result = client.calculate_water_surface_area(
            geometry=geometry,
            time_range=(start_date, end_date),
            waterbody_id="lake_test_001",
            waterbody_name="Test Lake"
        )
        
        # Vérifications
        assert result is not None
        assert result['waterbody_id'] == "lake_test_001"
        assert result['name'] == "Test Lake"
        assert result['data_source'] == "Sentinel-2"
        assert 'timestamp' in result
        assert 'time_range' in result
        
        # Vérifier que l'API a été appelée
        mock_post.assert_called_once()
        
        # Vérifier les headers
        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['Authorization'] == 'Bearer fake_token_123'
        assert headers['Content-Type'] == 'application/json'
    
    @patch('sentinel_hub.process_api.requests.post')
    def test_calculate_water_surface_area_http_error(self, mock_post):
        """Test gestion erreur HTTP"""
        # Mock de l'authentification
        mock_auth = Mock()
        mock_auth.get_token.return_value = "fake_token_123"
        
        # Mock d'une erreur HTTP
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error 400")
        mock_post.return_value = mock_response
        
        # Client
        client = ProcessAPIClient(mock_auth)
        
        # Géométrie de test
        geometry = {
            "type": "Polygon",
            "coordinates": [[[58.5, 45.0], [59.5, 45.0], [59.5, 46.0], [58.5, 46.0], [58.5, 45.0]]]
        }
        
        # Test - doit lever une exception
        with pytest.raises(Exception):
            client.calculate_water_surface_area(
                geometry=geometry,
                time_range=(datetime(2024, 1, 1), datetime(2024, 1, 31)),
                waterbody_id="lake_test_001"
            )
    
    def test_build_payload(self):
        """Test construction du payload JSON"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        geometry = {
            "type": "Polygon",
            "coordinates": [[[58.5, 45.0], [59.5, 45.0], [59.5, 46.0], [58.5, 46.0], [58.5, 45.0]]]
        }
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        payload = client._build_payload(geometry, (start_date, end_date))
        
        # Vérifications structure
        assert 'input' in payload
        assert 'output' in payload
        assert 'evalscript' in payload
        
        # Vérifier input
        assert payload['input']['bounds']['geometry'] == geometry
        assert payload['input']['data'][0]['type'] == 'sentinel-2-l2a'
        
        # Vérifier timeRange
        time_range = payload['input']['data'][0]['dataFilter']['timeRange']
        assert time_range['from'] == "2024-01-01T00:00:00Z"
        assert time_range['to'] == "2024-01-31T23:59:59Z"
        
        # Vérifier maxCloudCoverage
        assert payload['input']['data'][0]['dataFilter']['maxCloudCoverage'] == 20
        
        # Vérifier output
        assert payload['output']['width'] == 512
        assert payload['output']['height'] == 512
        assert payload['output']['responses'][0]['format']['type'] == 'image/tiff'
    
    def test_get_ndwi_evalscript(self):
        """Test génération de l'evalscript NDWI"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        evalscript = client._get_ndwi_evalscript()
        
        # Vérifications
        assert evalscript is not None
        assert isinstance(evalscript, str)
        assert '//VERSION=3' in evalscript
        assert 'function setup()' in evalscript
        assert 'function evaluatePixel(sample)' in evalscript
        assert 'B03' in evalscript  # Bande verte
        assert 'B08' in evalscript  # Proche infrarouge
        assert 'SCL' in evalscript  # Scene Classification Layer
        assert 'ndwi' in evalscript
        assert '0.2' in evalscript  # Seuil NDWI
    
    def test_parse_response(self):
        """Test parsing de la réponse API"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        # Données de test
        api_data = {
            "data": {
                "water_pixels": 105080
            }
        }
        
        waterbody_id = "lake_test_001"
        waterbody_name = "Test Lake"
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Test
        result = client._parse_response(
            api_data,
            waterbody_id,
            waterbody_name,
            (start_date, end_date)
        )
        
        # Vérifications
        assert result['waterbody_id'] == waterbody_id
        assert result['name'] == waterbody_name
        assert result['data_source'] == 'Sentinel-2'
        assert 'timestamp' in result
        assert 'time_range' in result
        assert result['time_range']['start'] == start_date.isoformat()
        assert result['time_range']['end'] == end_date.isoformat()
        assert 'raw_response' in result
    
    def test_parse_response_without_name(self):
        """Test parsing sans nom de waterbody"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        api_data = {"data": {}}
        waterbody_id = "lake_test_001"
        
        result = client._parse_response(
            api_data,
            waterbody_id,
            None,  # Pas de nom
            (datetime(2024, 1, 1), datetime(2024, 1, 31))
        )
        
        # Si pas de nom fourni, devrait utiliser l'ID
        assert result['name'] == waterbody_id
    
    @patch('sentinel_hub.process_api.requests.post')
    def test_calculate_water_surface_area_timeout(self, mock_post):
        """Test gestion du timeout"""
        mock_auth = Mock()
        mock_auth.get_token.return_value = "fake_token_123"
        
        # Simuler une exception de type RequestException
        mock_post.side_effect = requests.exceptions.RequestException("Timeout error")
        
        client = ProcessAPIClient(mock_auth)
        
        geometry = {
            "type": "Polygon",
            "coordinates": [[[58.5, 45.0], [59.5, 45.0], [59.5, 46.0], [58.5, 46.0], [58.5, 45.0]]]
        }
        
        # Test - doit lever une exception
        with pytest.raises(Exception):
            client.calculate_water_surface_area(
                geometry=geometry,
                time_range=(datetime(2024, 1, 1), datetime(2024, 1, 31)),
                waterbody_id="lake_test_001"
            )
    
    def test_build_payload_date_formatting(self):
        """Test que les dates sont correctement formatées en ISO"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        
        # Dates spécifiques pour tester le formatting
        start_date = datetime(2024, 3, 15, 10, 30, 45)
        end_date = datetime(2024, 3, 20, 18, 45, 30)
        
        payload = client._build_payload(geometry, (start_date, end_date))
        
        time_range = payload['input']['data'][0]['dataFilter']['timeRange']
        
        # Vérifier que les heures sont mises à 00:00:00 pour start et 23:59:59 pour end
        assert time_range['from'] == "2024-03-15T00:00:00Z"
        assert time_range['to'] == "2024-03-20T23:59:59Z"
    
    def test_evalscript_contains_cloud_filtering(self):
        """Test que l'evalscript filtre bien les nuages"""
        mock_auth = Mock()
        client = ProcessAPIClient(mock_auth)
        
        evalscript = client._get_ndwi_evalscript()
        
        # Vérifier présence du filtrage des nuages
        assert 'SCL == 8' in evalscript  # Nuage probabilité moyenne
        assert 'SCL == 9' in evalscript  # Nuage probabilité haute
        assert 'SCL == 3' in evalscript  # Ombre de nuage
        assert 'isCloud' in evalscript


@pytest.fixture
def mock_auth_instance():
    """Fixture pour créer un mock d'authentification"""
    mock = Mock()
    mock.get_token.return_value = "test_token_123"
    return mock


@pytest.fixture
def process_client(mock_auth_instance):
    """Fixture pour créer un client Process API"""
    return ProcessAPIClient(mock_auth_instance)


@pytest.fixture
def sample_geometry():
    """Fixture pour géométrie de test"""
    return {
        "type": "Polygon",
        "coordinates": [[[58.5, 45.0], [59.5, 45.0], [59.5, 46.0], [58.5, 46.0], [58.5, 45.0]]]
    }


@pytest.fixture
def sample_time_range():
    """Fixture pour période de test"""
    return (datetime(2024, 1, 1), datetime(2024, 1, 31))


# Tests d'intégration
@pytest.mark.integration
class TestProcessAPIClientIntegration:
    """Tests d'intégration avec vraie API (nécessite credentials)"""
    
    @pytest.mark.skip(reason="Nécessite credentials réels et peut être lent")
    def test_real_api_call(self):
        """Test avec vraie API Sentinel Hub"""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        if not os.getenv('COPERNICUS_USERNAME'):
            pytest.skip("Credentials non configurées")
        
        # Authentification réelle
        from sentinel_hub.auth import SentinelHubAuth
        auth = SentinelHubAuth()
        
        # Client réel
        client = ProcessAPIClient(auth)
        
        # Géométrie simple (petit carré)
        geometry = {
            "type": "Polygon",
            "coordinates": [[[58.5, 45.0], [58.6, 45.0], [58.6, 45.1], [58.5, 45.1], [58.5, 45.0]]]
        }
        
        # Période récente
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Test
        result = client.calculate_water_surface_area(
            geometry=geometry,
            time_range=(start_date, end_date),
            waterbody_id="test_real_api"
        )
        
        # Vérifications basiques
        assert result is not None
        assert 'waterbody_id' in result


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
