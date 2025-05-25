from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
import torch
import re
from collections import defaultdict
import numpy as np

class AIService:
    def __init__(self):
        # Initialize the model (using a smaller model for local deployment)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
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
        
        # Common problematic patterns with enhanced detection
        self.problematic_patterns = [
            {
                "pattern": r"(?:perpetual|indefinite|forever|without\s+time\s+limit)",
                "description": "Perpetual confidentiality obligations",
                "suggestion": "Consider adding a reasonable time limit for confidentiality obligations",
                "risk_level": "high",
                "category": "duration"
            },
            {
                "pattern": r"(?:all|any|every)\s+(?:information|data|material|document)",
                "description": "Overly broad confidentiality scope",
                "suggestion": "Specify the types of information that are considered confidential",
                "risk_level": "high",
                "category": "scope"
            },
            {
                "pattern": r"(?:no|prohibited|restricted)\s+(?:reverse\s+engineering|decompilation|disassembly)",
                "description": "Restrictive reverse engineering clause",
                "suggestion": "Consider allowing reverse engineering for interoperability purposes",
                "risk_level": "medium",
                "category": "intellectual_property"
            },
            {
                "pattern": r"(?:assign|transfer|convey).*(?:without|prior|written)\s+consent",
                "description": "Restrictive assignment clause",
                "suggestion": "Allow assignment to affiliates or in case of merger/acquisition",
                "risk_level": "medium",
                "category": "scope"
            },
            {
                "pattern": r"(?:unlimited|uncapped|no\s+limit).*(?:liability|damages|indemnification)",
                "description": "Unlimited liability provision",
                "suggestion": "Consider reasonable limitations on liability",
                "risk_level": "high",
                "category": "liability"
            },
            {
                "pattern": r"(?:irrevocable|permanent).*(?:license|right|permission)",
                "description": "Irrevocable rights grant",
                "suggestion": "Consider adding conditions for revocation",
                "risk_level": "high",
                "category": "intellectual_property"
            }
        ]

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
        for pattern in self.problematic_patterns:
            matches = re.finditer(pattern["pattern"], paragraph, re.IGNORECASE)
            for match in matches:
                changes.append({
                    "original_text": match.group(),
                    "suggested_text": self._generate_suggestion(paragraph, pattern),
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
        if pattern["category"] == "duration":
            return original_text.replace("perpetual", "for a period of 5 years")
        elif pattern["category"] == "scope":
            return original_text.replace("all information", "specifically identified confidential information")
        elif pattern["category"] == "intellectual_property":
            return original_text.replace("no reverse engineering", "no reverse engineering except for interoperability purposes")
        elif pattern["category"] == "liability":
            return original_text.replace("unlimited liability", "liability limited to direct damages")
        
        return original_text

    def get_embedding(self, text: str) -> torch.Tensor:
        """
        Get the embedding for a piece of text
        """
        return self.model.encode(text) 