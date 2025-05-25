from sentence_transformers import SentenceTransformer
from typing import List, Dict
import torch
import re

class AIService:
    def __init__(self):
        # Initialize the model (using a smaller model for local deployment)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Common problematic clauses in NDAs
        self.problematic_patterns = [
            {
                "pattern": r"perpetual|indefinite|forever",
                "description": "Perpetual confidentiality obligations",
                "suggestion": "Consider adding a reasonable time limit for confidentiality obligations"
            },
            {
                "pattern": r"all information|any information|any data",
                "description": "Overly broad confidentiality scope",
                "suggestion": "Specify the types of information that are considered confidential"
            },
            {
                "pattern": r"no reverse engineering|reverse engineer",
                "description": "Restrictive reverse engineering clause",
                "suggestion": "Consider allowing reverse engineering for interoperability purposes"
            },
            {
                "pattern": r"assign.*without consent|transfer.*without consent",
                "description": "Restrictive assignment clause",
                "suggestion": "Allow assignment to affiliates or in case of merger/acquisition"
            }
        ]

    def analyze_nda(self, paragraphs: List[str]) -> List[Dict]:
        """
        Analyze NDA text and identify problematic clauses
        """
        changes = []
        
        # Process each paragraph
        for paragraph in paragraphs:
            # Skip empty paragraphs
            if not paragraph.strip():
                continue
                
            # Check for problematic patterns
            for pattern in self.problematic_patterns:
                matches = re.finditer(pattern["pattern"], paragraph, re.IGNORECASE)
                for match in matches:
                    changes.append({
                        "original_text": match.group(),
                        "suggested_text": self._generate_suggestion(paragraph, pattern),
                        "description": pattern["description"],
                        "suggestion": pattern["suggestion"]
                    })
        
        return changes

    def _generate_suggestion(self, original_text: str, pattern: Dict) -> str:
        """
        Generate a suggestion for the problematic clause
        """
        # This is a simple replacement strategy
        # In a real implementation, you might want to use the language model
        # to generate more sophisticated suggestions
        
        if "perpetual" in original_text.lower():
            return original_text.replace("perpetual", "for a period of 5 years")
        elif "all information" in original_text.lower():
            return original_text.replace("all information", "specifically identified confidential information")
        elif "no reverse engineering" in original_text.lower():
            return original_text.replace("no reverse engineering", "no reverse engineering except for interoperability purposes")
        elif "without consent" in original_text.lower():
            return original_text.replace("without consent", "with prior written consent, not to be unreasonably withheld")
        
        return original_text

    def get_embedding(self, text: str) -> torch.Tensor:
        """
        Get the embedding for a piece of text
        """
        return self.model.encode(text) 