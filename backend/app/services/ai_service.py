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
        
        print("Initializing patterns from training data...")  # Debug log
        
        # Add patterns from training data
        for category, data in self.trained_patterns.items():
            print(f"Processing category: {category}")  # Debug log
            print(f"Number of patterns in category: {len(data['patterns'])}")  # Debug log
            
            for i, pattern in enumerate(data["patterns"]):
                suggestion = data["suggestions"][i] if i < len(data["suggestions"]) else self._get_suggestion(category, pattern)
                context = data["context"][i] if i < len(data["context"]) else []
                
                # Create both exact and regex patterns
                if pattern:  # Only add if pattern is not empty
                    patterns.append({
                        "pattern": pattern,  # Exact pattern
                        "description": f"Problematic {category} clause",
                        "suggestion": suggestion,
                        "risk_level": self.clause_categories.get(category, {}).get("risk_level", "medium"),
                        "category": category,
                        "context_patterns": [context] if context else []
                    })
                    
                    # Add regex pattern for more flexible matching
                    regex_pattern = self._create_regex_pattern(pattern)
                    patterns.append({
                        "pattern": re.compile(regex_pattern, re.IGNORECASE),  # Regex pattern
                        "description": f"Problematic {category} clause (regex)",
                        "suggestion": suggestion,
                        "risk_level": self.clause_categories.get(category, {}).get("risk_level", "medium"),
                        "category": category,
                        "context_patterns": [context] if context else []
                    })
        
        # Add default patterns if no training data or as additional patterns
        print("Adding default patterns")
        default_patterns = [
            # Duration patterns
            {
                "pattern": r"\b(?:perpetual|indefinite|forever|without\s+time\s+limit)\b",
                "description": "Perpetual confidentiality obligations",
                "suggestion": "Consider adding a reasonable time limit for confidentiality obligations",
                "risk_level": "high",
                "category": "duration",
                "context_patterns": ["confidential", "secret", "proprietary"]
            },
            {
                "pattern": r"\b(?:during|throughout|for\s+the\s+duration\s+of)\s+(?:the|this)\s+(?:agreement|nda|contract)\b",
                "description": "Unclear duration of obligations",
                "suggestion": "Specify a clear time period for obligations",
                "risk_level": "high",
                "category": "duration",
                "context_patterns": ["obligation", "duty", "responsibility"]
            },
            
            # Scope patterns
            {
                "pattern": r"\b(?:all|any|every)\s+(?:information|data|material|document)\b",
                "description": "Overly broad confidentiality scope",
                "suggestion": "Specify the types of information that are considered confidential",
                "risk_level": "high",
                "category": "scope",
                "context_patterns": ["confidential", "secret", "proprietary"]
            },
            {
                "pattern": r"\b(?:use|utilize|exploit)\s+(?:for|in)\s+(?:any|all)\s+(?:purpose|way|manner)\b",
                "description": "Unrestricted use of information",
                "suggestion": "Limit the use of information to specific purposes",
                "risk_level": "high",
                "category": "scope",
                "context_patterns": ["information", "data", "material"]
            },
            
            # Liability patterns
            {
                "pattern": r"\b(?:unlimited|no\s+limit|without\s+limitation)\s+(?:liability|damages|indemnification)\b",
                "description": "Unlimited liability clause",
                "suggestion": "Consider reasonable limitations on liability",
                "risk_level": "high",
                "category": "liability",
                "context_patterns": ["liable", "damages", "indemnify"]
            },
            {
                "pattern": r"\b(?:consequential|indirect|special|incidental)\s+(?:damages|losses)\b",
                "description": "Broad damage claims",
                "suggestion": "Limit damage claims to direct damages",
                "risk_level": "high",
                "category": "liability",
                "context_patterns": ["damages", "losses", "claims"]
            },
            
            # Intellectual Property patterns
            {
                "pattern": r"\b(?:all|any)\s+(?:rights|title|interest)\s+(?:in|to)\s+(?:intellectual\s+property|ip)\b",
                "description": "Overly broad IP rights transfer",
                "suggestion": "Specify which IP rights are being transferred",
                "risk_level": "high",
                "category": "intellectual_property",
                "context_patterns": ["intellectual property", "ip", "rights"]
            },
            {
                "pattern": r"\b(?:assign|transfer|convey)\s+(?:all|any)\s+(?:rights|title|interest)\b",
                "description": "Unrestricted IP assignment",
                "suggestion": "Limit IP assignment to specific rights",
                "risk_level": "high",
                "category": "intellectual_property",
                "context_patterns": ["assign", "transfer", "convey"]
            },
            
            # Confidentiality patterns
            {
                "pattern": r"\b(?:disclose|share|reveal)\s+(?:to|with)\s+(?:any|all)\s+(?:third\s+party|person|entity)\b",
                "description": "Unrestricted disclosure rights",
                "suggestion": "Limit disclosure to specific authorized parties",
                "risk_level": "high",
                "category": "confidentiality",
                "context_patterns": ["disclose", "share", "reveal"]
            },
            {
                "pattern": r"\b(?:no|without)\s+(?:obligation|duty)\s+(?:to|of)\s+(?:maintain|preserve|protect)\s+(?:confidentiality|secrecy)\b",
                "description": "Lack of confidentiality obligations",
                "suggestion": "Add clear confidentiality obligations",
                "risk_level": "high",
                "category": "confidentiality",
                "context_patterns": ["confidential", "secret", "proprietary"]
            },
            
            # Additional patterns for common problematic clauses
            {
                "pattern": r"\b(?:solicit|hire|employ)\s+(?:any|all)\s+(?:employee|personnel|staff)\b",
                "description": "Broad non-solicitation clause",
                "suggestion": "Limit non-solicitation to key employees and reasonable time period",
                "risk_level": "high",
                "category": "scope",
                "context_patterns": ["solicit", "hire", "employ"]
            },
            {
                "pattern": r"\b(?:reverse\s+engineer|decompile|disassemble)\b",
                "description": "Broad reverse engineering prohibition",
                "suggestion": "Allow reverse engineering for interoperability purposes",
                "risk_level": "high",
                "category": "intellectual_property",
                "context_patterns": ["reverse engineer", "decompile", "disassemble"]
            },
            {
                "pattern": r"\b(?:no|without)\s+(?:warranty|guarantee|assurance)\b",
                "description": "Complete lack of warranties",
                "suggestion": "Include basic warranties for accuracy and ownership",
                "risk_level": "high",
                "category": "liability",
                "context_patterns": ["warranty", "guarantee", "assurance"]
            },
            
            # New patterns for additional problematic clauses
            {
                "pattern": r"\b(?:exclusive|sole)\s+(?:right|license|ownership)\b",
                "description": "Exclusive rights or ownership",
                "suggestion": "Consider non-exclusive rights or shared ownership",
                "risk_level": "high",
                "category": "intellectual_property",
                "context_patterns": ["right", "license", "ownership"]
            },
            {
                "pattern": r"\b(?:irrevocable|permanent)\s+(?:license|right|assignment)\b",
                "description": "Irrevocable rights or assignments",
                "suggestion": "Consider revocable rights with reasonable conditions",
                "risk_level": "high",
                "category": "intellectual_property",
                "context_patterns": ["license", "right", "assignment"]
            },
            {
                "pattern": r"\b(?:waive|waiver)\s+(?:of|for)\s+(?:all|any)\s+(?:rights|claims|remedies)\b",
                "description": "Broad waiver of rights",
                "suggestion": "Limit waiver to specific rights and circumstances",
                "risk_level": "high",
                "category": "liability",
                "context_patterns": ["waive", "waiver", "rights"]
            },
            {
                "pattern": r"\b(?:no|without)\s+(?:recourse|remedy|redress)\b",
                "description": "No recourse or remedies",
                "suggestion": "Include reasonable remedies and recourse options",
                "risk_level": "high",
                "category": "liability",
                "context_patterns": ["recourse", "remedy", "redress"]
            },
            {
                "pattern": r"\b(?:unlimited|no\s+limit)\s+(?:access|use|right)\b",
                "description": "Unlimited access or use rights",
                "suggestion": "Limit access and use to specific purposes and time periods",
                "risk_level": "high",
                "category": "scope",
                "context_patterns": ["access", "use", "right"]
            }
        ]
        
        # Add default patterns
        patterns.extend(default_patterns)
        
        print(f"Total number of patterns initialized: {len(patterns)}")  # Debug log
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
        
        print(f"\nChecking paragraph: {paragraph_lower[:100]}...")
        print(f"Number of patterns to check: {len(self.problematic_patterns)}")
        
        for pattern in self.problematic_patterns:
            # Then look for the specific pattern
            pattern_text = pattern["pattern"]
            
            # Handle both string and regex patterns
            if isinstance(pattern_text, str):
                # Try exact match first
                if pattern_text.lower() in paragraph_lower:
                    print(f"Found exact match for pattern: {pattern_text}")
                    start_pos = paragraph_lower.find(pattern_text.lower())
                    end_pos = start_pos + len(pattern_text)
                    context = paragraph[max(0, start_pos - 100):min(len(paragraph), end_pos + 100)]
                    
                    changes.append({
                        "original_text": pattern_text,
                        "suggested_text": pattern["suggestion"],
                        "description": pattern["description"],
                        "suggestion": pattern["suggestion"],
                        "risk_level": pattern["risk_level"],
                        "category": pattern["category"]
                    })
                else:
                    # Try partial match if exact match fails
                    words = pattern_text.lower().split()
                    if len(words) > 0:  # Changed from 1 to 0 to catch single-word patterns
                        # Check if most words from the pattern are present in the paragraph
                        matching_words = sum(1 for word in words if word in paragraph_lower)
                        if matching_words >= len(words) * 0.5:  # Lowered threshold from 0.6 to 0.5
                            print(f"Found partial match for pattern: {pattern_text}")
                            changes.append({
                                "original_text": pattern_text,
                                "suggested_text": pattern["suggestion"],
                                "description": pattern["description"],
                                "suggestion": pattern["suggestion"],
                                "risk_level": pattern["risk_level"],
                                "category": pattern["category"]
                            })
            else:  # Handle regex patterns
                matches = re.finditer(pattern_text, paragraph_lower)
                for match in matches:
                    print(f"Found regex match: {match.group()}")
                    changes.append({
                        "original_text": match.group(),
                        "suggested_text": pattern["suggestion"],
                        "description": pattern["description"],
                        "suggestion": pattern["suggestion"],
                        "risk_level": pattern["risk_level"],
                        "category": pattern["category"]
                    })
        
        print(f"Found {len(changes)} changes")
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
            
            if similarity > highest_similarity and similarity > 0.4:  # Lowered threshold from 0.5 to 0.4
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