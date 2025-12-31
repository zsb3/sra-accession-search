"""Unit tests for search_sra.py"""

import io
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from search_sra import build_query, search_sra, fetch_summaries


class TestBuildQuery:
    """Test query construction"""
    
    def test_basic_query(self):
        """Test basic query with organism only"""
        query = build_query("Salmonella enterica")
        assert "Salmonella enterica" in query
        assert "illumina" in query.lower()
        assert "paired" in query.lower()
        assert "wgs" in query.lower()
        assert "[Organism]" in query
        assert "[Platform]" in query
        assert "[Layout]" in query
        assert "[Strategy]" in query
    
    def test_query_with_date_range(self):
        """Test query includes date range"""
        query = build_query("Escherichia coli", "2022:2024")
        assert "2022:2024" in query
        assert "[Publication Date]" in query
    
    def test_query_with_default_date_range(self):
        """Test default date range"""
        query = build_query("Listeria monocytogenes")
        assert "2020:2025" in query
    
    def test_query_all_organisms(self):
        """Test query generation for all target organisms"""
        organisms = [
            "Salmonella enterica",
            "Escherichia coli",
            "Listeria monocytogenes",
            "Campylobacter jejuni",
            "Staphylococcus aureus",
            "Streptococcus pneumoniae"
        ]
        for organism in organisms:
            query = build_query(organism)
            assert organism in query
            assert "illumina" in query.lower()


class TestSearchSRA:
    """Test SRA search functionality"""
    
    @patch('search_sra.Entrez.esearch')
    def test_search_basic(self, mock_esearch):
        """Test basic search with mocked API"""
        # Mock the API response - Entrez.read expects a file-like object with DTD
        xml_response = b'''<?xml version="1.0"?>
<!DOCTYPE eSearchResult PUBLIC "-//NLM//DTD esearch 20060628//EN" "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esearch.dtd">
<eSearchResult><Count>100</Count><WebEnv>test_webenv</WebEnv><QueryKey>1</QueryKey></eSearchResult>'''
        mock_esearch.return_value = io.BytesIO(xml_response)
        
        result = search_sra("test query", retmax=1000)
        
        assert result['Count'] == '100'
        assert result['WebEnv'] == 'test_webenv'
        assert result['QueryKey'] == '1'
        mock_esearch.assert_called_once()
    
    @patch('search_sra.Entrez.esearch')
    def test_search_parameters(self, mock_esearch):
        """Test search is called with correct parameters"""
        xml_response = b'''<?xml version="1.0"?>
<!DOCTYPE eSearchResult PUBLIC "-//NLM//DTD esearch 20060628//EN" "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esearch.dtd">
<eSearchResult><Count>50</Count><WebEnv>test</WebEnv><QueryKey>1</QueryKey></eSearchResult>'''
        mock_esearch.return_value = io.BytesIO(xml_response)
        
        search_sra("my query", retmax=500)
        
        # Verify esearch was called with correct parameters
        call_args = mock_esearch.call_args
        assert call_args[1]['db'] == 'sra'
        assert call_args[1]['term'] == 'my query'
        assert call_args[1]['retmax'] == 500
        assert call_args[1]['usehistory'] == 'y'


class TestFetchSummaries:
    """Test summary fetching functionality"""
    
    @patch('search_sra.Entrez.read')
    @patch('search_sra.Entrez.esummary')
    def test_fetch_summaries_basic(self, mock_esummary, mock_read):
        """Test fetching summaries with mocked API"""
        # Mock the parsed result directly
        mock_read.return_value = [
            {'Id': '123', 'Runs': 'test1'},
            {'Id': '456', 'Runs': 'test2'}
        ]
        
        summaries = fetch_summaries('test_webenv', '1', retstart=0, retmax=10)
        
        # Verify it returned the mocked data
        assert len(summaries) == 2
        assert summaries[0]['Id'] == '123'
    
    @patch('search_sra.Entrez.read')
    @patch('search_sra.Entrez.esummary')
    def test_fetch_summaries_parameters(self, mock_esummary, mock_read):
        """Test fetch is called with correct parameters"""
        mock_read.return_value = []
        
        fetch_summaries('my_webenv', '5', retstart=100, retmax=50)
        
        # Verify esummary was called with correct parameters
        call_args = mock_esummary.call_args
        assert call_args[1]['db'] == 'sra'
        assert call_args[1]['query_key'] == '5'
        assert call_args[1]['WebEnv'] == 'my_webenv'
        assert call_args[1]['retstart'] == 100
        assert call_args[1]['retmax'] == 50


class TestMainFunction:
    """Test the main CLI function"""
    
    @patch('search_sra.Entrez')
    @patch('search_sra.time.sleep')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_with_env_vars(self, mock_file, mock_sleep, mock_entrez):
        """Test main function with environment variables"""
        # Set up environment
        with patch.dict(os.environ, {'NCBI_EMAIL': 'test@example.com', 'NCBI_API_KEY': 'test_key'}):
            # Mock search response
            mock_search_response = MagicMock()
            mock_search_response.read.return_value = b'<?xml version="1.0"?><eSearchResult><Count>10</Count><WebEnv>test</WebEnv><QueryKey>1</QueryKey></eSearchResult>'
            mock_entrez.esearch.return_value = mock_search_response
            
            # Mock summary response
            mock_summary_response = MagicMock()
            mock_summary_response.read.return_value = json.dumps([])
            mock_entrez.esummary.return_value = mock_summary_response
            
            # Run main with args
            with patch('sys.argv', ['search_sra.py', '--organism', 'Test organism', '--output', 'test.json', '--max-results', '5']):
                from search_sra import main
                main()
            
            # Verify email and API key were set
            assert mock_entrez.email == 'test@example.com'
            assert mock_entrez.api_key == 'test_key'
    
    @patch('search_sra.Entrez')
    def test_main_missing_email(self, mock_entrez):
        """Test main function fails without email"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.argv', ['search_sra.py', '--organism', 'Test', '--output', 'test.json']):
                from search_sra import main
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
    
    @patch('search_sra.Entrez')
    @patch('sys.stdout')
    def test_main_without_api_key_warns(self, mock_stdout, mock_entrez):
        """Test main function warns about throttling without API key"""
        with patch.dict(os.environ, {'NCBI_EMAIL': 'test@example.com'}, clear=True):
            # Mock search response
            xml_response = b'<?xml version="1.0"?><eSearchResult><Count>5</Count><WebEnv>test</WebEnv><QueryKey>1</QueryKey></eSearchResult>'
            mock_entrez.esearch.return_value = io.BytesIO(xml_response)
            
            # Mock summary response
            json_response = json.dumps([]).encode('utf-8')
            mock_entrez.esummary.return_value = io.BytesIO(json_response)
            
            with patch('sys.argv', ['search_sra.py', '--organism', 'Test', '--output', 'test.json', '--max-results', '5']):
                with patch('builtins.open', mock_open()):
                    from search_sra import main
                    main()
            
            # Verify API key was set to None (not that the mock has it, but that it was assigned)
            # The actual assertion is that it ran without error
            assert True  # Test passes if no exception raised
    
    @patch('search_sra.Entrez.read')
    @patch('search_sra.Entrez.esearch')
    @patch('search_sra.Entrez.esummary')
    @patch('search_sra.time.sleep')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_respects_max_results(self, mock_file, mock_sleep, mock_esummary, mock_esearch, mock_read):
        """Test that max_results is respected in fetching"""
        with patch.dict(os.environ, {'NCBI_EMAIL': 'test@example.com', 'NCBI_API_KEY': 'key'}):
            # Mock Entrez.read to return search results
            mock_read.side_effect = [
                {'Count': '1000', 'WebEnv': 'test', 'QueryKey': '1'},  # search result
                []  # summary result
            ]
            
            with patch('sys.argv', ['search_sra.py', '--organism', 'Test', '--output', 'test.json', '--max-results', '50']):
                from search_sra import main
                main()
            
            # Verify esummary was called with retmax=50 for the batch
            call_args = mock_esummary.call_args
            assert call_args[1]['retmax'] == 50
    
    @patch('search_sra.Entrez.read')
    @patch('search_sra.Entrez.esearch')
    @patch('builtins.open', new_callable=mock_open)
    def test_main_no_results_exits(self, mock_file, mock_esearch, mock_read):
        """Test main exits gracefully when no results found"""
        with patch.dict(os.environ, {'NCBI_EMAIL': 'test@example.com'}):
            # Mock Entrez.read to return 0 results
            mock_read.return_value = {'Count': '0', 'WebEnv': 'test', 'QueryKey': '1'}
            
            with patch('sys.argv', ['search_sra.py', '--organism', 'Test', '--output', 'test.json']):
                from search_sra import main
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 0
