"""
Argument extraction for contextual commands
Integrates with existing NLP system
"""

import re
import os
from typing import Dict, Any, Tuple
from enum import Enum


class ArgumentType(Enum):
    URL = "url"
    FILE_PATH = "file_path"
    DIRECTORY = "directory"
    APPLICATION = "application"
    SEARCH_QUERY = "search_query"
    COMMAND = "command"


class ArgumentExtractor:
    def __init__(self, config=None):
        self.config = config

        self.system_dirs = {
            'downloads': os.path.expanduser('~/Downloads'),
            'desktop': os.path.expanduser('~/Desktop'),
            'documents': os.path.expanduser('~/Documents'),
            'pictures': os.path.expanduser('~/Pictures'),
            'music': os.path.expanduser('~/Music'),
            'videos': os.path.expanduser('~/Videos'),
            'home': os.path.expanduser('~')
        }

        self.websites = {
            'youtube': 'https://youtube.com',
            'google': 'https://google.com',
            'github': 'https://github.com',
            'gmail': 'https://gmail.com',
            'chatgpt': 'https://chat.openai.com',
            'netflix': 'https://netflix.com',
            'spotify': 'https://spotify.com'
        }

        self.patterns = {
            'url': re.compile(r'(https?://[^\s]+|www\.[^\s]+\.[^\s]+)', re.IGNORECASE),
            'file_path': re.compile(r'(~?/[^\s/][^\s]*|[\w]:\\[^\s\\][^\s]*)'),
            'search_query': re.compile(
                r'(?:search|find|google)\s+(?:for\s+)?(.+)',
                re.IGNORECASE
            )
        }

    def extract_for_intent(self, text: str, intent: str) -> Dict[str, Any]:
        intent = intent.upper()
        text_lower = text.lower()

        args = {
            'raw_text': text,
            'target': None,
            'query': None,
            'path': None,
            'url': None,
            'command': None
        }

        if intent == "OPEN_BROWSER":
            return self._extract_browser_args(text_lower)

        if intent == "OPEN_TERMINAL":
            return self._extract_terminal_args(text_lower)

        if intent == "OPEN_FILE_MANAGER":
            return self._extract_file_manager_args(text_lower)

        if intent == "SEARCH_WEB":
            return self._extract_search_args(text)

        if intent == "OPEN_FILE":
            return self._extract_file_args(text_lower)

        if intent == "LIST_FILES":
            return self._extract_list_files_args(text_lower)

        return args

    def _extract_browser_args(self, text: str) -> Dict[str, Any]:
        for name, url in self.websites.items():
            if name in text:
                return {'url': url, 'target': name}

        match = self.patterns['url'].search(text)
        if match:
            url = match.group(1)
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return {'url': url, 'target': 'custom'}

        return {'url': 'https://google.com', 'target': 'default'}

    def _extract_terminal_args(self, text: str) -> Dict[str, Any]:
        words = text.split()
        for i, word in enumerate(words):
            if word in ['terminal', 'cmd', 'bash', 'powershell'] and i + 1 < len(words):
                return {
                    'command': ' '.join(words[i + 1:]),
                    'target': 'with_command'
                }
        return {'target': 'default'}

    def _extract_file_manager_args(self, text: str) -> Dict[str, Any]:
        for name, path in self.system_dirs.items():
            if name in text:
                return {'path': path, 'target': name}

        match = self.patterns['file_path'].search(text)
        if match:
            return {
                'path': os.path.expanduser(match.group(1)),
                'target': 'custom_path'
            }

        return {'path': self.system_dirs['home'], 'target': 'home'}

    def _extract_search_args(self, text: str) -> Dict[str, Any]:
        match = self.patterns['search_query'].search(text)
        if match:
            return {'query': match.group(1).strip(), 'target': 'web_search'}
        return {}

    def _extract_file_args(self, text: str) -> Dict[str, Any]:
        for word in text.split():
            if '.' in word:
                return {'filename': word, 'target': 'named_file'}
        return {}

    def _extract_list_files_args(self, text: str) -> Dict[str, Any]:
        for name, path in self.system_dirs.items():
            if name in text:
                return {'path': path, 'target': name}
        return {'path': '.', 'target': 'current'}

    def validate_arguments(self, args: Dict[str, Any], intent: str) -> Tuple[bool, str]:
        if intent == "SEARCH_WEB" and not args.get('query'):
            return False, "Missing search query"

        if intent == "OPEN_FILE_MANAGER" and 'path' in args:
            if not os.path.exists(args['path']):
                return False, f"Path does not exist: {args['path']}"

        return True, "OK"
