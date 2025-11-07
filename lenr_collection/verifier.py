"""
DeepSeek API integration for content verification
"""

import requests
import json
from typing import Dict, List, Optional
import time
import logging

logger = logging.getLogger(__name__)


class DeepSeekVerifier:
    """Verify and score LENR papers using DeepSeek API"""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.deepseek.com/chat/completions"

    def verify_content(self, title: str, abstract: str,
                      full_text: str = "") -> Dict:
        """Verify if content is LENR-related and score relevance

        Returns:
            Dict with 'is_lenr', 'score', 'summary', 'keywords'
        """

        # Construct verification prompt
        prompt = self._create_verification_prompt(title, abstract, full_text)

        # Make API call
        response = self._api_call(prompt)

        if not response:
            return {
                'is_lenr': False,
                'score': 0.0,
                'summary': '',
                'keywords': '',
                'error': 'API call failed'
            }

        # Parse response
        return self._parse_verification_response(response)

    def _create_verification_prompt(self, title: str,
                                   abstract: str,
                                   full_text: str = "") -> str:
        """Create structured prompt for content verification"""

        prompt = f"""You are an expert in Low Energy Nuclear Reactions (LENR) and Cold Fusion research.

Analyze the following scientific paper and provide:
1. Is this paper related to LENR/Cold Fusion? (yes/no)
2. Relevance score (0.0 to 1.0)
3. Brief summary (2-3 sentences)
4. Key research keywords (comma-separated)

**Paper Title:** {title}

**Abstract:** {abstract[:1000]}

**Content Sample:** {full_text[:2000] if full_text else "Not available"}

Respond in the following JSON format:
{{
    "is_lenr": true/false,
    "score": 0.0-1.0,
    "summary": "Brief summary here",
    "keywords": "keyword1, keyword2, keyword3"
}}
"""
        return prompt

    def _api_call(self, prompt: str,
                 max_retries: int = 3) -> Optional[str]:
        """Make API call to DeepSeek with retries"""

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert LENR researcher providing structured analysis.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,  # Lower temperature for consistent responses
            'max_tokens': 1000
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )

                response.raise_for_status()

                result = response.json()
                content = result['choices'][0]['message']['content']

                logger.info(f"DeepSeek success (tokens: {result.get('usage', {}).get('total_tokens', 0)})")

                return content

            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    # Rate limit - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                else:
                    logger.error(f"API error: {e}")

            except Exception as e:
                logger.error(f"API call failed: {e}")

            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        return None

    def _parse_verification_response(self, response: str) -> Dict:
        """Parse JSON response from DeepSeek"""
        try:
            # Try to extract JSON from response
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0]
            elif '{' in response:
                json_str = response[response.index('{'):response.rindex('}')+1]
            else:
                json_str = response

            data = json.loads(json_str)

            return {
                'is_lenr': data.get('is_lenr', False),
                'score': float(data.get('score', 0.0)),
                'summary': data.get('summary', ''),
                'keywords': data.get('keywords', '')
            }

        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return {
                'is_lenr': False,
                'score': 0.0,
                'summary': '',
                'keywords': '',
                'error': 'Parse failed'
            }

    def batch_verify(self, papers: List[Dict],
                    delay: float = 1.0) -> List[Dict]:
        """Verify multiple papers with rate limiting"""
        results = []

        for i, paper in enumerate(papers):
            logger.info(f"Verifying {i+1}/{len(papers)}: {paper.get('Title', 'Unknown')}")

            verification = self.verify_content(
                title=paper.get('Title', ''),
                abstract=paper.get('Abstract', ''),
                full_text=paper.get('full_text', '')
            )

            paper['Verified'] = True
            paper['DeepSeek_Score'] = verification['score']
            paper['DeepSeek_Summary'] = verification['summary']

            if verification.get('keywords'):
                paper['Keywords'] = verification['keywords']

            results.append(paper)

            # Rate limiting
            time.sleep(delay)

        return results
