"""
Tests pour le client Elasticsearch
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time 

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from elasticsearch_client.client import WaterScopeESClient


class TestWaterScopeESClient:
    """Tests pour la classe WaterScopeESClient"""
    
    @patch('elasticsearch_client.client.Elasticsearch')
    def test_init_connexion_success(self, mock_es_class):
        """Test initialisation avec connexion réussie"""
        # Mock du client Elasticsearch
        mock_es = Mock()
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = False
        mock_es.indices.create.return_value = {'acknowledged': True}
        mock_es_class.return_value = mock_es
        
        # Test
        client = WaterScopeESClient(host="http://localhost:9200")
        
        # Vérifications
        assert client.host == "http://localhost:9200"
        mock_es.ping.assert_called()
        mock_es.indices.create.assert_called_once()
    
    
    @patch('elasticsearch_client.client.Elasticsearch')
    def test_init_connexion_echec(self, mock_es_class):
        """Test initialisation avec échec de connexion"""
        # Mock qui échoue à chaque tentative de ping
        mock_es = Mock()
        mock_es.ping.side_effect = Exception("Connection refused")
        mock_es_class.return_value = mock_es
    
        # Test - devrait lever une exception après 3 tentatives
        with pytest.raises(Exception, match="Cannot connect"):
            WaterScopeESClient(host="http://localhost:9200")
    
    @patch('elasticsearch_client.client.Elasticsearch')
    def test_index_waterbody_stat(self, mock_es_class):
        """Test indexation d'un document"""
        # Mock
        mock_es = Mock()
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = True
        mock_es.index.return_value = {'_id': 'test_doc_id_123'}
        mock_es_class.return_value = mock_es
        
        client = WaterScopeESClient()
        
        # Document de test
        doc = {
            "waterbody_id": "lake_test_001",
            "name": "Test Lake",
            "timestamp": "2024-01-01T00:00:00Z",
            "surface_area_hectares": 1050.8
        }
        
        # Test
        doc_id = client.index_waterbody_stat(doc)
        
        # Vérifications
        assert doc_id == 'test_doc_id_123'
        mock_es.index.assert_called_once_with(
            index="waterbody_stats",
            document=doc
        )
    
    @patch('elasticsearch_client.client.Elasticsearch')
    def test_get_waterbody_timeseries(self, mock_es_class):
        """Test récupération de séries temporelles"""
        # Mock
        mock_es = Mock()
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = True
        
        # Mock de la réponse de recherche
        mock_es.search.return_value = {
            'hits': {
                'hits': [
                    {
                        '_source': {
                            'waterbody_id': 'lake_001',
                            'timestamp': '2024-01-01T00:00:00Z',
                            'surface_area_hectares': 1000.0
                        }
                    },
                    {
                        '_source': {
                            'waterbody_id': 'lake_001',
                            'timestamp': '2024-02-01T00:00:00Z',
                            'surface_area_hectares': 950.0
                        }
                    }
                ]
            }
        }
        mock_es_class.return_value = mock_es
        
        client = WaterScopeESClient()
        
        # Test
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        results = client.get_waterbody_timeseries(
            waterbody_id="lake_001",
            start_date=start_date,
            end_date=end_date
        )
        
        # Vérifications
        assert len(results) == 2
        assert results[0]['waterbody_id'] == 'lake_001'
        assert results[0]['surface_area_hectares'] == 1000.0
        mock_es.search.assert_called_once()
    
    @patch('elasticsearch_client.client.Elasticsearch')
    def test_health_check(self, mock_es_class):
        """Test vérification de santé du cluster"""
        # Mock
        mock_es = Mock()
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = True
        mock_es.cluster.health.return_value = {
            'status': 'green',
            'number_of_nodes': 1,
            'active_shards': 10
        }
        mock_es_class.return_value = mock_es
        
        client = WaterScopeESClient()
        
        # Test
        health = client.health_check()
        
        # Vérifications
        assert health['status'] == 'green'
        assert health['number_of_nodes'] == 1
        assert health['active_shards'] == 10
        assert 'index_exists' in health


@pytest.fixture
def mock_es_client():
    """Fixture pour créer un client Elasticsearch mocké"""
    with patch('elasticsearch_client.client.Elasticsearch') as mock_es_class:
        mock_es = Mock()
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = True
        mock_es_class.return_value = mock_es
        
        yield WaterScopeESClient()


# Tests d'intégration
@pytest.mark.integration
class TestWaterScopeESClientIntegration:
    """Tests d'intégration avec vrai Elasticsearch"""
    
    def test_connexion_reelle(self):
        """Test connexion à Elasticsearch réel (nécessite Docker)"""
        try:
            client = WaterScopeESClient(host="http://localhost:9200")
            health = client.health_check()
            assert health['status'] in ['green', 'yellow']
        except Exception:
            pytest.skip("Elasticsearch non disponible")


if __name__ == "__main__":
    pytest.main([__file__, '-v'])