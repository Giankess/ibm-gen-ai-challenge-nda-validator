from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import torch
import re
from collections import defaultdict
import numpy as np
from .training_analyzer import TrainingAnalyzer

class AIService:
    def __init__(self):
        try:
            # Initialize the model (using a smaller model for local deployment)
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load model: {str(e)}")
            self.model = None
        
        # Initialize training analyzer and load patterns
        self.training_analyzer = TrainingAnalyzer()
        try:
            self.trained_patterns = self.training_analyzer.analyze_training_data()
        except FileNotFoundError:
            print("Warning: No training data found. Using default patterns.")
            self.trained_patterns = {}
        
        # Define clause categories and their risk levels
        self.clause_categories = {
            "confidentiality": {
                "risk_level": "high",
                "keywords": ["confidential", "secret", "proprietary", "trade secret"],
                "description": "Confidentiality obligations and information protection"
            },
            "duration": {
                "risk_level": "high",
                "keywords": ["term", "duration", "period", "expiration"],
                "description": "Time period for obligations"
            },
            "scope": {
                "risk_level": "medium",
                "keywords": ["scope", "purpose", "use", "application"],
                "description": "Scope and purpose of the agreement"
            },
            "liability": {
                "risk_level": "high",
                "keywords": ["liability", "damages", "indemnification", "warranty"],
                "description": "Liability and damages provisions"
            },
            "intellectual_property": {
                "risk_level": "high",
                "keywords": ["intellectual property", "ip", "patent", "copyright", "trademark"],
                "description": "Intellectual property rights and ownership"
            }
        }
        
        # Initialize problematic patterns from training data
        self.problematic_patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> List[Dict]:
        """
        Initialize problematic patterns from training data and default patterns
        """
        patterns = []
        
        # Add patterns from training data
        for category, data in self.trained_patterns.items():
            for pattern in data["patterns"]:
                patterns.append({
                    "pattern": self._create_regex_pattern(pattern),
                    "description": f"Problematic {category} clause",
                    "suggestion": self._get_suggestion(category, pattern),
                    "risk_level": self.clause_categories.get(category, {}).get("risk_level", "medium"),
                    "category": category,
                    "context_patterns": data["context"]
                })
        
        # Add default patterns if no training data
        if not patterns:
            patterns = [
                {
                    "pattern": r"\b(?:perpetual|indefinite|forever|without\s+time\s+limit)\b",
                    "description": "Perpetual confidentiality obligations",
                    "suggestion": "Consider adding a reasonable time limit for confidentiality obligations",
                    "risk_level": "high",
                    "category": "duration",
                    "context_patterns": ["confidential", "secret", "proprietary"]
                },
                {
                    "pattern": r"\b(?:all|any|every)\s+(?:information|data|material|document)\b",
                    "description": "Overly broad confidentiality scope",
                    "suggestion": "Specify the types of information that are considered confidential",
                    "risk_level": "high",
                    "category": "scope",
                    "context_patterns": ["confidential", "secret", "proprietary"]
                }
            ]
        
        return patterns

    def _create_regex_pattern(self, text: str) -> str:
        """
        Create a regex pattern from text, handling common variations
        """
        # Replace common variations
        text = text.lower()
        text = re.sub(r'\s+', r'\\s+', text)  # Handle multiple spaces
        text = re.sub(r'[.,;]', r'[.,;]?', text)  # Handle optional punctuation
        return f"(?:{text})"

    def _get_suggestion(self, category: str, pattern: str) -> str:
        """
        Get a suggestion based on training data or default suggestions
        """
        if category in self.trained_patterns and self.trained_patterns[category]["suggestions"]:
            # Use the most common suggestion from training data
            return self.trained_patterns[category]["suggestions"][0]
        
        # Default suggestions
        suggestions = {
            "confidentiality": "Specify the types of information that are considered confidential",
            "duration": "Consider adding a reasonable time limit",
            "scope": "Narrow the scope to specific purposes",
            "liability": "Consider reasonable limitations on liability",
            "intellectual_property": "Clarify ownership and usage rights"
        }
        return suggestions.get(category, "Consider revising this clause")

    def analyze_nda(self, paragraphs: List[str]) -> Dict:
        """
        Perform comprehensive analysis of NDA text
        """
        # Initialize analysis results
        analysis = {
            "changes": [],
            "risk_assessment": defaultdict(list),
            "clause_categories": defaultdict(list),
            "overall_risk_level": "low",
            "missing_clauses": []
        }
        
        # Process each paragraph
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # Get paragraph embedding for semantic analysis
            paragraph_embedding = self.get_embedding(paragraph)
            
            # Check for problematic patterns
            changes = self._check_problematic_patterns(paragraph)
            if changes:
                analysis["changes"].extend(changes)
            
            # Categorize clauses
            clause_category = self._categorize_clause(paragraph, paragraph_embedding)
            if clause_category:
                analysis["clause_categories"][clause_category].append(paragraph)
            
            # Assess risks
            risk_level = self._assess_risk(paragraph, changes)
            if risk_level != "low":
                analysis["risk_assessment"][risk_level].append(paragraph)
        
        # Check for missing important clauses
        analysis["missing_clauses"] = self._check_missing_clauses(analysis["clause_categories"])
        
        # Determine overall risk level
        analysis["overall_risk_level"] = self._determine_overall_risk(analysis["risk_assessment"])
        
        return analysis

    def _check_problematic_patterns(self, paragraph: str) -> List[Dict]:
        """
        Check for problematic patterns in text
        """
        changes = []
        paragraph_lower = paragraph.lower()
        
        for pattern in self.problematic_patterns:
            # First check if the context patterns are present
            if pattern.get("context_patterns"):
                context_match = any(
                    context in paragraph_lower 
                    for context in pattern["context_patterns"]
                )
                if not context_match:
                    continue
            
            # Then look for the specific pattern
            matches = re.finditer(pattern["pattern"], paragraph, re.IGNORECASE)
            for match in matches:
                # Get the matched text and its surrounding context
                matched_text = match.group()
                start_pos = max(0, match.start() - 100)  # Increased context window
                end_pos = min(len(paragraph), match.end() + 100)
                context = paragraph[start_pos:end_pos].lower()
                
                # Enhanced context validation
                if pattern["category"] == "scope":
                    # For scope patterns, ensure we're in a confidentiality context
                    # and that the clause is actually defining scope (not just mentioning it)
                    if not any(word in context for word in ["confidential", "secret", "proprietary"]):
                        continue
                    # Check if this is actually a scope definition clause
                    if not any(phrase in context for phrase in ["shall include", "means", "refers to", "defined as"]):
                        continue
                elif pattern["category"] == "duration":
                    # For duration patterns, ensure we're in a confidentiality context
                    # and that the clause is actually about duration (not just mentioning time)
                    if not any(word in context for word in ["confidential", "secret", "proprietary", "term", "period"]):
                        continue
                    # Check if this is actually a duration clause
                    if not any(phrase in context for phrase in ["shall continue", "shall remain", "shall survive", "shall expire"]):
                        continue
                
                # Additional validation for specific patterns
                if "all" in matched_text.lower() or "any" in matched_text.lower():
                    # Check if there are any limiting words nearby
                    limiting_words = ["specifically", "identified", "designated", "marked", "labeled"]
                    if any(word in context for word in limiting_words):
                        continue  # Skip if there are already limiting words
                
                changes.append({
                    "original_text": matched_text,
                    "suggested_text": self._generate_suggestion(matched_text, pattern),
                    "description": pattern["description"],
                    "suggestion": pattern["suggestion"],
                    "risk_level": pattern["risk_level"],
                    "category": pattern["category"]
                })
        
        return changes

    def _categorize_clause(self, paragraph: str, embedding: torch.Tensor) -> str:
        """
        Categorize a clause using semantic similarity
        """
        best_category = None
        highest_similarity = 0.0
        
        for category, info in self.clause_categories.items():
            # Create embedding for category keywords
            category_text = " ".join(info["keywords"])
            category_embedding = self.get_embedding(category_text)
            
            # Calculate similarity
            similarity = self._cosine_similarity(embedding, category_embedding)
            
            if similarity > highest_similarity and similarity > 0.5:  # Threshold for categorization
                highest_similarity = similarity
                best_category = category
        
        return best_category

    def _assess_risk(self, paragraph: str, changes: List[Dict]) -> str:
        """
        Assess risk level of a paragraph
        """
        if not changes:
            return "low"
        
        # Count high and medium risk changes
        risk_counts = defaultdict(int)
        for change in changes:
            risk_counts[change["risk_level"]] += 1
        
        if risk_counts["high"] > 0:
            return "high"
        elif risk_counts["medium"] > 0:
            return "medium"
        return "low"

    def _check_missing_clauses(self, categorized_clauses: Dict) -> List[str]:
        """
        Check for missing important clauses
        """
        missing = []
        for category, info in self.clause_categories.items():
            if category not in categorized_clauses and info["risk_level"] == "high":
                missing.append(f"Missing {info['description']} clause")
        return missing

    def _determine_overall_risk(self, risk_assessment: Dict) -> str:
        """
        Determine overall risk level of the document
        """
        if risk_assessment["high"]:
            return "high"
        elif risk_assessment["medium"]:
            return "medium"
        return "low"

    def _cosine_similarity(self, a: torch.Tensor, b: torch.Tensor) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        return float(torch.nn.functional.cosine_similarity(a, b, dim=0))

    def _generate_suggestion(self, original_text: str, pattern: Dict) -> str:
        """
        Generate a suggestion for the problematic clause
        """
        if pattern["category"] in self.trained_patterns:
            # Use trained suggestions if available
            suggestions = self.trained_patterns[pattern["category"]]["suggestions"]
            if suggestions:
                return suggestions[0]  # Use the most common suggestion
        
        # Fall back to default suggestions with more specific alternatives
        if pattern["category"] == "duration":
            return "for a period of 5 years"
        elif pattern["category"] == "scope":
            # More specific suggestions based on context
            if "all" in original_text.lower() or "any" in original_text.lower():
                return "information that is specifically identified as confidential"
            return "specifically identified confidential information"
        elif pattern["category"] == "intellectual_property":
            return "no reverse engineering except for interoperability purposes"
        elif pattern["category"] == "liability":
            return "liability limited to direct damages"
        
        return "Consider revising this clause"

    def get_embedding(self, text: str) -> torch.Tensor:
        """
        Get the embedding for a piece of text
        """
        if self.model is None:
            # Return a zero tensor if model is not available
            return torch.zeros(384)  # 384 is the dimension of all-MiniLM-L6-v2
        # Convert numpy array to PyTorch tensor
        return torch.tensor(self.model.encode(text)) 