from docx import Document
from docx.shared import RGBColor
from typing import List, Dict, Tuple
import re
from collections import defaultdict
import os
import subprocess
import tempfile

class TrainingAnalyzer:
    def __init__(self, training_dir: str = "training_data"):
        self.training_dir = training_dir
        self.patterns = defaultdict(list)
        self.suggestions = defaultdict(list)
        self.context_patterns = defaultdict(list)

    def analyze_training_data(self) -> Dict:
        """
        Analyze all training documents and extract patterns
        """
        if not os.path.exists(self.training_dir):
            raise FileNotFoundError(f"Training directory {self.training_dir} not found")

        for filename in os.listdir(self.training_dir):
            if filename.endswith(('.docx', '.doc')):
                file_path = os.path.join(self.training_dir, filename)
                try:
                    self._analyze_document(file_path)
                except Exception as e:
                    print(f"Warning: Could not analyze {filename}: {str(e)}")

        return self._compile_patterns()

    def _analyze_document(self, file_path: str):
        """
        Analyze a single training document
        """
        if file_path.endswith('.doc'):
            # Convert .doc to .docx using LibreOffice
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                docx_path = tmp.name
            try:
                subprocess.run([
                    'soffice',
                    '--headless',
                    '--convert-to', 'docx',
                    '--outdir', os.path.dirname(docx_path),
                    file_path
                ], check=True)
                doc = Document(docx_path)
            finally:
                if os.path.exists(docx_path):
                    os.unlink(docx_path)
        else:
            doc = Document(file_path)
        
        current_paragraph = []
        current_strikethrough = []
        current_red = []
        
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                # Check for strikethrough (original problematic text)
                if run.font.strike:
                    if current_strikethrough:  # If we already have strikethrough text
                        # Store the previous pattern
                        self._store_pattern(current_strikethrough, current_red, current_paragraph)
                        current_strikethrough = []
                        current_red = []
                    current_strikethrough.append(run.text)
                # Check for red color (suggested changes)
                elif run.font.color and run.font.color.rgb == RGBColor(255, 0, 0):
                    current_red.append(run.text)
                # Collect context (non-marked text)
                else:
                    current_paragraph.append(run.text)
            
            # If we have both strikethrough and red text, store the pattern
            if current_strikethrough and current_red:
                self._store_pattern(current_strikethrough, current_red, current_paragraph)
                current_strikethrough = []
                current_red = []
                current_paragraph = []

    def _store_pattern(self, strikethrough: List[str], red: List[str], context: List[str]):
        """
        Store a pattern from strikethrough and red text
        """
        original_text = " ".join(strikethrough).strip()
        suggested_text = " ".join(red).strip()
        context_text = " ".join(context).strip()
        
        if original_text and suggested_text:
            # Extract the pattern category
            category = self._categorize_pattern(original_text, suggested_text)
            
            # Store the pattern
            self.patterns[category].append({
                "original": original_text,
                "suggested": suggested_text,
                "context": context_text
            })
            
            # Store the suggestion pattern
            self.suggestions[category].append(suggested_text)
            
            # Store context patterns
            if context_text:
                self.context_patterns[category].append(context_text)

    def _categorize_pattern(self, original: str, suggested: str) -> str:
        """
        Categorize the pattern based on content
        """
        # Define category keywords
        categories = {
            "confidentiality": ["confidential", "secret", "proprietary", "trade secret"],
            "duration": ["perpetual", "term", "period", "duration", "expiration"],
            "scope": ["scope", "purpose", "use", "application", "all", "any"],
            "liability": ["liability", "damages", "indemnification", "warranty"],
            "intellectual_property": ["intellectual property", "ip", "patent", "copyright", "trademark"],
            "assignment": ["assign", "transfer", "convey", "license"],
            "termination": ["terminate", "termination", "end", "expire"],
            "governing_law": ["governing law", "jurisdiction", "venue", "dispute"]
        }
        
        # Check which category keywords appear in the original text
        text_lower = original.lower()
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "other"

    def _extract_common_patterns(self, texts: List[str]) -> List[str]:
        """
        Extract common patterns from a list of texts
        """
        if not texts:
            return []
            
        # Convert texts to lowercase for comparison
        texts_lower = [text.lower() for text in texts]
        
        # Find common single words
        common_words = set()
        word_counts = defaultdict(int)
        for text in texts_lower:
            words = text.split()
            for word in words:
                if len(word) > 3:  # Only consider words longer than 3 characters
                    word_counts[word] += 1
        
        # Add words that appear in at least 2 texts
        for word, count in word_counts.items():
            if count >= 2:
                common_words.add(word)
        
        # Find common phrases (2 or more words)
        common_phrases = set()
        for text in texts_lower:
            words = text.split()
            # Look for phrases of 2-4 words
            for i in range(len(words)):
                for j in range(2, min(5, len(words) - i + 1)):
                    phrase = " ".join(words[i:i+j])
                    if len(phrase) > 5 and all(phrase in t for t in texts_lower):
                        common_phrases.add(phrase)
        
        # Combine single words and phrases
        patterns = list(common_words) + list(common_phrases)
        
        # Sort by length (longer patterns first) and return
        return sorted(patterns, key=len, reverse=True)

    def _compile_patterns(self) -> Dict:
        """
        Compile the analyzed patterns into a structured format
        """
        compiled_patterns = {}
        
        for category, patterns in self.patterns.items():
            # Store all original patterns
            original_patterns = [p["original"] for p in patterns]
            
            # Store all suggestions
            suggestion_patterns = [p["suggested"] for p in patterns]
            
            # Store all context patterns
            context_patterns = [p["context"] for p in patterns if p["context"]]
            
            compiled_patterns[category] = {
                "patterns": original_patterns,
                "suggestions": suggestion_patterns,
                "context": context_patterns,
                "examples": patterns[:5]  # Keep first 5 examples
            }
        
        return compiled_patterns 