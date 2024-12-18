import requests
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class ArticleService:
    """Service for interacting with Internet Archive APIs to fetch and manage articles"""
    
    BASE_URL = "https://archive.org"
    METADATA_ENDPOINT = f"{BASE_URL}/metadata"
    SEARCH_ENDPOINT = f"{BASE_URL}/advancedsearch.php"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArticleService/1.0 (Educational Purpose)'
        })

    def get_article(self, identifier: str) -> Optional[Dict]:
        """
        Fetch a specific article by its Internet Archive identifier
        
        Args:
            identifier (str): The Internet Archive identifier for the article
            
        Returns:
            Dict: Article data including metadata and content
            None: If article not found or error occurs
        """
        try:
            response = self.session.get(f"{self.METADATA_ENDPOINT}/{identifier}")
            response.raise_for_status()
            
            metadata = response.json()
            if not metadata.get('metadata'):
                logger.warning(f"No metadata found for article {identifier}")
                return None
                
            # Enhance metadata with additional fields
            article_data = {
                'identifier': identifier,
                'title': metadata['metadata'].get('title'),
                'creator': metadata['metadata'].get('creator'),
                'description': metadata['metadata'].get('description'),
                'date': metadata['metadata'].get('date'),
                'language': metadata['metadata'].get('language'),
                'subjects': metadata['metadata'].get('subject', []),
                'download_links': self._extract_download_links(metadata),
                'retrieved_at': datetime.now().isoformat()
            }
            
            return article_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching article {identifier}: {str(e)}")
            return None

    def create_article(self, content: Dict) -> Dict:
        """
        Create a new article entry with provided content
        
        Args:
            content (Dict): Article content and metadata
            
        Returns:
            Dict: Created article data
        """
        # Validate required fields
        required_fields = ['title', 'content', 'source_identifier']
        if not all(field in content for field in required_fields):
            raise ValueError("Missing required fields for article creation")
            
        # Add metadata and processing timestamp
        article_data = {
            **content,
            'processed_at': datetime.now().isoformat(),
            'status': 'created'
        }
        
        return article_data

    def list_articles(self, 
                     page: int = 1, 
                     limit: int = 50, 
                     sort: str = 'date desc') -> Dict[str, Union[List, int]]:
        """
        List articles with pagination
        
        Args:
            page (int): Page number
            limit (int): Results per page
            sort (str): Sort order
            
        Returns:
            Dict containing articles list and total count
        """
        try:
            params = {
                'q': 'mediatype:texts',
                'fl[]': ['identifier', 'title', 'creator', 'date', 'description'],
                'sort[]': [sort],
                'rows': limit,
                'page': page,
                'output': 'json'
            }
            
            response = self.session.get(self.SEARCH_ENDPOINT, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'articles': data.get('response', {}).get('docs', []),
                'total': data.get('response', {}).get('numFound', 0),
                'page': page,
                'limit': limit
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing articles: {str(e)}")
            return {'articles': [], 'total': 0, 'page': page, 'limit': limit}

    def search_articles(self, 
                       query: str,
                       filters: Optional[Dict] = None,
                       page: int = 1,
                       limit: int = 50) -> Dict[str, Union[List, int]]:
        """
        Search articles using advanced query parameters
        
        Args:
            query (str): Search query
            filters (Dict): Additional search filters
            page (int): Page number
            limit (int): Results per page
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            # Construct advanced search query
            search_query = f'({quote(query)}) AND mediatype:texts'
            if filters:
                for key, value in filters.items():
                    search_query += f' AND {key}:"{quote(str(value))}"'
            
            params = {
                'q': search_query,
                'fl[]': [
                    'identifier', 'title', 'creator', 'date', 
                    'description', 'subject', 'language'
                ],
                'sort[]': ['downloads desc'],
                'rows': limit,
                'page': page,
                'output': 'json'
            }
            
            response = self.session.get(self.SEARCH_ENDPOINT, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                'results': data.get('response', {}).get('docs', []),
                'total': data.get('response', {}).get('numFound', 0),
                'page': page,
                'limit': limit,
                'query': query,
                'filters': filters
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching articles: {str(e)}")
            return {
                'results': [], 
                'total': 0, 
                'page': page, 
                'limit': limit,
                'query': query,
                'filters': filters
            }

    def get_article_metadata(self, identifier: str) -> Optional[Dict]:
        """
        Fetch detailed metadata for an article
        
        Args:
            identifier (str): Article identifier
            
        Returns:
            Dict: Article metadata
            None: If metadata not found or error occurs
        """
        try:
            response = self.session.get(f"{self.METADATA_ENDPOINT}/{identifier}")
            response.raise_for_status()
            
            data = response.json()
            if not data.get('metadata'):
                return None
                
            # Extract and structure metadata
            metadata = {
                'identifier': identifier,
                'title': data['metadata'].get('title'),
                'creator': data['metadata'].get('creator'),
                'description': data['metadata'].get('description'),
                'date': data['metadata'].get('date'),
                'language': data['metadata'].get('language'),
                'subjects': data['metadata'].get('subject', []),
                'collection': data['metadata'].get('collection', []),
                'source': data['metadata'].get('source'),
                'rights': data['metadata'].get('rights'),
                'format': data['metadata'].get('format'),
                'downloads': data['metadata'].get('downloads'),
                'files': self._process_files(data.get('files', [])),
                'retrieved_at': datetime.now().isoformat()
            }
            
            return metadata
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching metadata for {identifier}: {str(e)}")
            return None

    def validate_article_content(self, content: Dict) -> Dict[str, Union[bool, List[str]]]:
        """
        Validate article content and structure
        
        Args:
            content (Dict): Article content to validate
            
        Returns:
            Dict containing validation results
        """
        errors = []
        warnings = []
        
        # Required fields validation
        required_fields = ['title', 'content', 'source_identifier']
        for field in required_fields:
            if field not in content:
                errors.append(f"Missing required field: {field}")
        
        # Content length validation
        if 'content' in content:
            if len(content['content']) < 100:
                warnings.append("Content length is very short")
            elif len(content['content']) > 1000000:
                warnings.append("Content length exceeds recommended maximum")
        
        # Metadata validation
        if 'metadata' in content:
            if not isinstance(content['metadata'], dict):
                errors.append("Metadata must be a dictionary")
            else:
                # Validate metadata fields
                for field in ['date', 'language', 'source']:
                    if field in content['metadata'] and not content['metadata'][field]:
                        warnings.append(f"Empty metadata field: {field}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _extract_download_links(self, metadata: Dict) -> List[Dict]:
        """Extract and process download links from metadata"""
        download_links = []
        if 'files' in metadata:
            for file in metadata['files']:
                if file.get('name') and file.get('format'):
                    download_links.append({
                        'name': file['name'],
                        'format': file['format'],
                        'size': file.get('size'),
                        'url': f"{self.BASE_URL}/download/{metadata['metadata']['identifier']}/{file['name']}"
                    })
        return download_links

    def _process_files(self, files: List[Dict]) -> List[Dict]:
        """Process and structure file information"""
        processed_files = []
        for file in files:
            if file.get('name'):
                processed_files.append({
                    'name': file['name'],
                    'format': file.get('format'),
                    'size': file.get('size'),
                    'mtime': file.get('mtime'),
                    'crc32': file.get('crc32'),
                    'md5': file.get('md5'),
                    'sha1': file.get('sha1')
                })
        return processed_files
