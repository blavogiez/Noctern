"""
LaTeX error analyzer using LLM for intelligent suggestions.
Integrate with Ollama system to provide context-aware error analysis.
"""

import json
import re
from typing import Optional, Dict, Any, List
from utils import debug_console
from debug_system.core import AnalysisEngine, AnalysisResult, DebugContext, QuickFix


class LLMAnalyzer(AnalysisEngine):
    """LaTeX error analyzer using LLM for intelligent suggestions."""
    
    def __init__(self):
        """Initialize analyzer with cache for repeated analysis."""
        self._analysis_cache: Dict[str, AnalysisResult] = {}
        debug_console.log("LLM analyzer initialized", level='DEBUG')
    
    def analyze_errors(self, context: DebugContext) -> AnalysisResult:
        """Analyze errors and provide suggestions."""
        if not self.is_available():
            return AnalysisResult(
                explanation="LLM analysis not available",
                confidence=0.0
            )
        
        # Use diff if available, otherwise analyze errors directly
        if context.diff_content:
            return self._analyze_diff(context.diff_content, context.log_content or "")
        else:
            return self._analyze_errors_directly(context)
    
    def is_available(self) -> bool:
        """Check if LLM analysis is available."""
        try:
            from llm import state as llm_state
            return (
                llm_state._root_window is not None and
                llm_state._global_default_prompts is not None and
                "debug_latex_diff" in llm_state._global_default_prompts and
                llm_state.model_debug is not None
            )
        except ImportError:
            return False
        except Exception as e:
            debug_console.log(f"LLM availability check failed: {e}", level='WARNING')
            return False
    
    def _analyze_diff(self, diff_content: str, log_content: str) -> AnalysisResult:
        """Analyze diff content using LLM."""
        if not diff_content.strip():
            return AnalysisResult(
                explanation="No changes to analyze",
                confidence=0.0
            )
        
        # Check cache first
        cache_key = self._create_cache_key(diff_content, log_content)
        if cache_key in self._analysis_cache:
            debug_console.log("Using cached analysis result", level='DEBUG')
            return self._analysis_cache[cache_key]
        
        debug_console.log("Starting LLM analysis of diff", level='INFO')
        
        try:
            # Call LLM system
            analysis_text = self._call_llm_system(diff_content, log_content)
            
            if not analysis_text:
                return AnalysisResult(
                    explanation="LLM analysis failed",
                    confidence=0.0
                )
            
            # Parse the analysis
            result = self._parse_llm_response(analysis_text, diff_content)
            
            # Cache the result
            self._analysis_cache[cache_key] = result
            
            debug_console.log(f"LLM analysis completed with confidence {result.confidence:.1%}", level='INFO')
            return result
            
        except Exception as e:
            debug_console.log(f"Error during LLM analysis: {e}", level='ERROR')
            return AnalysisResult(
                explanation=f"Analysis error: {str(e)}",
                confidence=0.0
            )
    
    def _analyze_errors_directly(self, context: DebugContext) -> AnalysisResult:
        """Analyze errors directly when no diff is available."""
        if not context.errors:
            return AnalysisResult(
                explanation="No errors to analyze",
                confidence=0.0
            )
        
        # Create error summary for analysis
        error_summary = "\\n".join([
            f"Line {error.line_number}: {error.message}"
            for error in context.errors
        ])
        
        return self._analyze_diff(error_summary, context.log_content or "")
    
    def _call_llm_system(self, diff_content: str, log_content: str) -> Optional[str]:
        """Call LLM system for analysis."""
        try:
            from llm import state as llm_state, api_client
            
            prompt_template = llm_state._global_default_prompts.get("debug_latex_diff")
            if not prompt_template:
                debug_console.log("debug_latex_diff prompt template not found", level='ERROR')
                return None
            
            # Extract added lines from diff
            added_lines = self._extract_added_lines(diff_content)
            if not added_lines.strip():
                added_lines = diff_content
            
            # Format prompt
            full_prompt = prompt_template.format(
                diff_content=diff_content,
                added_lines=added_lines
            )
            
            debug_console.log("Sending request to LLM", level='DEBUG')
            
            # Make debug-specific LLM request
            response_generator = api_client.generate_with_task_profile(
                full_prompt,
                model_name=llm_state.model_debug,
                stream=False,
                task_type="debug"
            )
            response = next(response_generator)
            
            if response.get("success"):
                analysis_text = response.get("data", "")
                debug_console.log(f"LLM response received ({len(analysis_text)} chars)", level='DEBUG')
                return analysis_text
            else:
                error_msg = response.get("error", "Unknown LLM error")
                debug_console.log(f"LLM request failed: {error_msg}", level='ERROR')
                return None
                
        except Exception as e:
            debug_console.log(f"Error calling LLM system: {e}", level='ERROR')
            return None
    
    def _extract_added_lines(self, diff_content: str) -> str:
        """Extract added lines from diff content."""
        added_lines = []
        for line in diff_content.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])  # Remove the + prefix
        return '\\n'.join(added_lines)
    
    def _parse_llm_response(self, analysis_text: str, diff_content: str) -> AnalysisResult:
        """Parse LLM response into structured result."""
        debug_console.log(f"Parsing LLM response ({len(analysis_text)} chars)", level='DEBUG')
        
        try:
            # Try to extract JSON
            json_data = self._extract_json_from_text(analysis_text)
            
            if json_data:
                explanation = json_data.get("explanation", json_data.get("analysis", "No explanation provided"))
                corrected_code = json_data.get("corrected_code", json_data.get("fixed_code", ""))
                confidence = self._calculate_confidence(json_data, analysis_text)
                
                # Generate quick fixes
                quick_fixes = self._generate_quick_fixes(json_data, diff_content)
                
                return AnalysisResult(
                    explanation=explanation,
                    suggested_fix=corrected_code if corrected_code else None,
                    confidence=confidence,
                    quick_fixes=quick_fixes,
                    corrected_code=corrected_code if corrected_code else None,
                    raw_analysis=analysis_text
                )
            else:
                # Fallback to plain text parsing
                debug_console.log("No JSON found, using plain text analysis", level='INFO')
                
                explanation = self._extract_explanation_from_text(analysis_text)
                corrected_code = self._extract_code_from_text(analysis_text)
                
                return AnalysisResult(
                    explanation=explanation,
                    suggested_fix=corrected_code if corrected_code else None,
                    confidence=0.5 if explanation else 0.3,
                    quick_fixes=self._generate_text_based_fixes(analysis_text),
                    corrected_code=corrected_code if corrected_code else None,
                    raw_analysis=analysis_text
                )
                
        except Exception as e:
            debug_console.log(f"Error parsing LLM response: {e}", level='ERROR')
            return AnalysisResult(
                explanation=f"Analysis available but parsing failed. Raw response: {analysis_text[:200]}...",
                confidence=0.1,
                raw_analysis=analysis_text
            )
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text response."""
        # Try code block JSON first
        json_match = re.search(r'```(?:json)?\\s*({.*?})\\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find any JSON object
        json_match = re.search(r'{[^{}]*(?:"[^"]*"[^{}]*)*}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _calculate_confidence(self, json_data: Dict[str, Any], analysis_text: str) -> float:
        """Calculate confidence score for analysis."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if corrected code is provided
        if json_data.get("corrected_code"):
            confidence += 0.3
        
        # Increase confidence if explanation is detailed
        explanation = json_data.get("explanation", "")
        if len(explanation) > 100:
            confidence += 0.1
        
        # Increase confidence if specific fixes are mentioned
        if "fix" in analysis_text.lower() or "correct" in analysis_text.lower():
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_quick_fixes(self, json_data: Dict[str, Any], diff_content: str) -> List[QuickFix]:
        """Generate quick fixes from LLM analysis."""
        quick_fixes = []
        
        corrected_code = json_data.get("corrected_code", "")
        explanation = json_data.get("explanation", "")
        
        if corrected_code:
            quick_fixes.append(QuickFix(
                title="Apply LLM Correction",
                description="Apply the complete correction suggested by the AI",
                fix_type="replace",
                new_text=corrected_code,
                confidence=0.8,
                auto_applicable=False
            ))
        
        # Generate fixes for common patterns
        if "missing" in explanation.lower() and "}" in explanation:
            quick_fixes.append(QuickFix(
                title="Add Missing Closing Brace",
                description="Add missing '}' character",
                fix_type="insert",
                new_text="}",
                confidence=0.9,
                auto_applicable=True
            ))
        
        if "package" in explanation.lower() and "usepackage" in explanation:
            package_match = re.search(r'\\\\usepackage\\{([^}]+)\\}', explanation)
            if package_match:
                package_name = package_match.group(1)
                quick_fixes.append(QuickFix(
                    title=f"Add Package {package_name}",
                    description=f"Add \\\\usepackage{{{package_name}}} to preamble",
                    fix_type="insert",
                    target_line=1,
                    new_text=f"\\\\usepackage{{{package_name}}}",
                    confidence=0.8,
                    auto_applicable=False
                ))
        
        return quick_fixes
    
    def _extract_explanation_from_text(self, text: str) -> str:
        """Extract explanation from plain text response."""
        lines = text.split('\\n')
        explanation_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('```') and not line.startswith('{'):
                explanation_lines.append(line)
        
        explanation = ' '.join(explanation_lines)
        return explanation[:500] if explanation else "AI analysis completed"
    
    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract code blocks from plain text response."""
        # Look for LaTeX code blocks
        code_match = re.search(r'```(?:latex|tex)?\\s*(.*?)\\s*```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Look for LaTeX-like content
        latex_patterns = [
            r'(\\\\documentclass.*?\\\\end\\{document\\})',
            r'(\\\\begin\\{.*?\\}.*?\\\\end\\{.*?\\})',
        ]
        
        for pattern in latex_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _generate_text_based_fixes(self, text: str) -> List[QuickFix]:
        """Generate quick fixes from plain text analysis."""
        fixes = []
        text_lower = text.lower()
        
        if "missing" in text_lower and ("brace" in text_lower or "}" in text):
            fixes.append(QuickFix(
                title="Add Missing Brace",
                description="Add missing closing brace",
                fix_type="insert",
                new_text="}",
                confidence=0.7,
                auto_applicable=True
            ))
        
        if "package" in text_lower and "usepackage" in text_lower:
            fixes.append(QuickFix(
                title="Check Package Requirements",
                description="Review package dependencies mentioned in analysis",
                fix_type="manual",
                confidence=0.6,
                auto_applicable=False
            ))
        
        return fixes
    
    def _create_cache_key(self, diff_content: str, log_content: str) -> str:
        """Create cache key for analysis results."""
        import hashlib
        content = diff_content + log_content
        return hashlib.md5(content.encode()).hexdigest()[:16]