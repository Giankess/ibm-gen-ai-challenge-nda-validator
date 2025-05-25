from docx import Document
from docx.shared import RGBColor
from typing import List, Dict, Tuple
import re
from collections import defaultdict
import os

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
                self._analyze_document(file_path)

        return self._compile_patterns()

    def _analyze_document(self, file_path: str):
        """
        Analyze a single training document
        """
        doc = Document(file_path)
        
        for paragraph in doc.paragraphs:
            original_text = ""
            suggested_text = ""
            context = []
            
            for run in paragraph.runs:
                # Check for strikethrough (original problematic text)
                if run.font.strike:
                    original_text += run.text
                # Check for red color (suggested changes)
                elif run.font.color and run.font.color.rgb == RGBColor(255, 0, 0):
                    suggested_text += run.text
                # Collect context (non-marked text)
                else:
                    context.append(run.text)
            
            if original_text and suggested_text:
                # Extract the pattern category
                category = self._categorize_pattern(original_text, suggested_text)
                
                # Store the pattern
                self.patterns[category].append({
                    "original": original_text,
                    "suggested": suggested_text,
                    "context": " ".join(context)
                })
                
                # Store the suggestion pattern
                self.suggestions[category].append(suggested_text)
                
                # Store context patterns
                if context:
                    self.context_patterns[category].append(" ".join(context))

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

    def _compile_patterns(self) -> Dict:
        """
        Compile the analyzed patterns into a structured format
        """
        compiled_patterns = {}
        
        for category, patterns in self.patterns.items():
            # Extract common patterns in original text
            original_patterns = self._extract_common_patterns([p["original"] for p in patterns])
            
            # Extract common patterns in suggestions
            suggestion_patterns = self._extract_common_patterns([p["suggested"] for p in patterns])
            
            # Extract common context patterns
            context_patterns = self._extract_common_patterns([p["context"] for p in patterns])
            
            compiled_patterns[category] = {
                "patterns": original_patterns,
                "suggestions": suggestion_patterns,
                "context": context_patterns,
                "examples": patterns[:5]  # Keep first 5 examples
            }
        
        return compiled_patterns

    def _extract_common_patterns(self, texts: List[str]) -> List[str]:
        """
        Extract common patterns from a list of texts
        """
        if not texts:
            return []
            
        # Convert texts to lowercase for comparison
        texts_lower = [text.lower() for text in texts]
        
        # Find common phrases (2 or more words)
        common_phrases = set()
        for text in texts_lower:
            words = text.split()
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                if all(phrase in t for t in texts_lower):
                    common_phrases.add(phrase)
        
        return list(common_phrases) 