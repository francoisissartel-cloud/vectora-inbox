"""
PDF Extraction Module using PyMuPDF (fitz)
Extracts text and metadata from PDF documents
"""
import logging
import pymupdf
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and metadata from PDF files using PyMuPDF"""
    
    def extract(self, pdf_content: bytes, url: str = "") -> Dict:
        """
        Extract text and metadata from PDF content
        
        Args:
            pdf_content: Raw PDF bytes
            url: Source URL for logging
            
        Returns:
            {
                'text': str,
                'metadata': {}
            }
        """
        try:
            doc = pymupdf.open(stream=pdf_content, filetype="pdf")
            
            # Extract ALL text from ALL pages
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            
            full_text = "\n".join(text_parts).strip()
            
            # Extract metadata
            metadata = doc.metadata or {}
            creation_date = self._parse_pdf_date(metadata.get('creationDate', ''))
            
            result = {
                'text': full_text,
                'metadata': {
                    'title': metadata.get('title', ''),
                    'author': metadata.get('author', ''),
                    'creation_date': creation_date,
                    'pages': doc.page_count
                }
            }
            
            doc.close()
            logger.info(f"PDF extracted: {len(full_text)} chars, {result['metadata']['pages']} pages from {url}")
            return result
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {url}: {e}")
            return {
                'text': '',
                'metadata': {
                    'title': '',
                    'author': '',
                    'creation_date': '',
                    'pages': 0
                }
            }
    
    def _parse_pdf_date(self, pdf_date: str) -> str:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS) to ISO format
        
        Args:
            pdf_date: PDF date string like "D:20240115120000+01'00'"
            
        Returns:
            ISO date string or empty string
        """
        if not pdf_date:
            return ''
        
        try:
            # Remove D: prefix and timezone info
            date_str = pdf_date.replace('D:', '').split('+')[0].split('-')[0]
            
            # Parse YYYYMMDDHHMMSS
            if len(date_str) >= 8:
                year = date_str[0:4]
                month = date_str[4:6]
                day = date_str[6:8]
                
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.debug(f"Could not parse PDF date '{pdf_date}': {e}")
        
        return ''
