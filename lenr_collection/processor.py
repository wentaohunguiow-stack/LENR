"""
PDF processor to extract metadata and content
"""

import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Process PDFs to extract metadata and content"""

    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract comprehensive metadata from PDF"""
        metadata = {
            'title': None,
            'author': None,
            'subject': None,
            'keywords': None,
            'doi': None,
            'pages': 0
        }

        try:
            # Try pdf2doi for DOI extraction
            from pdf2doi import pdf2doi
            result = pdf2doi(str(pdf_path))
            if result and 'identifier' in result:
                metadata['doi'] = result.get('identifier')
        except ImportError:
            logger.debug("pdf2doi not available, skipping DOI extraction")
        except Exception as e:
            logger.debug(f"DOI extraction failed: {e}")

        try:
            # Extract PDF metadata
            import pymupdf
            doc = pymupdf.open(pdf_path)
            pdf_meta = doc.metadata

            metadata.update({
                'title': pdf_meta.get('title') or metadata['title'],
                'author': pdf_meta.get('author') or metadata['author'],
                'subject': pdf_meta.get('subject'),
                'keywords': pdf_meta.get('keywords'),
                'pages': doc.page_count
            })

            doc.close()
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")

        return metadata

    def extract_text(self, pdf_path: str,
                    handle_columns: bool = True) -> str:
        """Extract full text with multi-column support"""
        try:
            # Try PyMuPDF4LLM for best structure preservation
            try:
                import pymupdf4llm
                text = pymupdf4llm.to_markdown(pdf_path)
                return text
            except ImportError:
                logger.debug("pymupdf4llm not available, using standard extraction")

            # Fallback to standard extraction
            import pymupdf
            doc = pymupdf.open(pdf_path)
            all_text = []

            for page in doc:
                if handle_columns:
                    # Use blocks for better column handling
                    blocks = page.get_text("blocks", sort=True)
                    page_text = "\n".join([b[4] for b in blocks if b[6] == 0])
                else:
                    page_text = page.get_text()

                all_text.append(page_text)

            doc.close()
            return "\n\n".join(all_text)

        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install pymupdf")
            return ""
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    def extract_abstract(self, pdf_path: str) -> str:
        """Extract abstract from first page"""
        try:
            import pymupdf
            doc = pymupdf.open(pdf_path)
            page = doc[0]
            text = page.get_text()

            # Look for abstract section
            if 'Abstract' in text or 'ABSTRACT' in text:
                parts = text.split('Abstract', 1)
                if len(parts) > 1:
                    # Extract until next section (Introduction, etc.)
                    abstract = parts[1].split('\n\n', 2)[0]
                    doc.close()
                    return abstract.strip()

            doc.close()
        except ImportError:
            logger.error("PyMuPDF not installed")
        except Exception as e:
            logger.debug(f"Abstract extraction failed: {e}")

        return ""

    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """Extract tables using Camelot"""
        try:
            import camelot
            tables = camelot.read_pdf(str(pdf_path), pages='all',
                                     flavor='lattice')

            table_data = []
            for i, table in enumerate(tables):
                if table.parsing_report['accuracy'] > 80:
                    table_data.append({
                        'index': i,
                        'page': table.page,
                        'accuracy': table.parsing_report['accuracy'],
                        'dataframe': table.df
                    })

            return table_data
        except ImportError:
            logger.debug("Camelot not available, skipping table extraction")
            return []
        except Exception as e:
            logger.debug(f"Table extraction failed: {e}")
            return []

    def process_pdf(self, pdf_path: str) -> Dict:
        """Complete PDF processing pipeline"""
        logger.info(f"Processing: {pdf_path}")

        results = {
            'pdf_path': str(pdf_path),
            'metadata': self.extract_metadata(pdf_path),
            'text': self.extract_text(pdf_path),
            'abstract': self.extract_abstract(pdf_path),
            'tables_count': len(self.extract_tables(pdf_path))
        }

        return results
