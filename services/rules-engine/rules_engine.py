"""
Rules Engine
Evaluates rules on vital signs and determines alert severity
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger(__name__)


class RuleResult:
    """Result of a rule evaluation"""
    def __init__(self, rule_id: str, triggered: bool, severity: str, message: str):
        self.rule_id = rule_id
        self.triggered = triggered
        self.severity = severity
        self.message = message


class RulesEngine:
    """Engine for evaluating rules on vital signs"""
    
    def __init__(self):
        self.hr_max = settings.hr_max
        self.spo2_min = settings.spo2_min
        self.temp_max = settings.temp_max
        self.hr_very_high = settings.hr_very_high
        self.spo2_low = settings.spo2_low
    
    def evaluate_rules(self, vitals: Dict[str, Any]) -> Tuple[str, List[RuleResult]]:
        """
        Evaluate all rules on vital signs.
        
        Returns:
            Tuple of (overall_severity, list of triggered rules)
        """
        rules_triggered: List[RuleResult] = []
        
        # Extract vital values
        hr_value = self._get_vital_value(vitals, "heart_rate")
        spo2_value = self._get_vital_value(vitals, "oxygen_saturation")
        temp_value = self._get_vital_value(vitals, "temperature")
        
        # Rule 1: HR > hr_max => warning
        if hr_value is not None and hr_value > self.hr_max:
            rules_triggered.append(RuleResult(
                rule_id="hr_max_exceeded",
                triggered=True,
                severity="warning",
                message=f"Heart rate {hr_value} exceeds maximum threshold {self.hr_max}"
            ))
            logger.info(f"Rule triggered: HR {hr_value} > {self.hr_max} (warning)")
        
        # Rule 2: SpO2 < spo2_min => critical
        if spo2_value is not None and spo2_value < self.spo2_min:
            rules_triggered.append(RuleResult(
                rule_id="spo2_min_below",
                triggered=True,
                severity="critical",
                message=f"SpO2 {spo2_value} below minimum threshold {self.spo2_min}"
            ))
            logger.warning(f"Rule triggered: SpO2 {spo2_value} < {self.spo2_min} (critical)")
        
        # Rule 3: Temp > temp_max => warning
        if temp_value is not None:
            # Convert to Fahrenheit if needed
            temp_f = self._to_fahrenheit(temp_value, vitals.get("temperature", {}).get("unit", "fahrenheit"))
            if temp_f > self.temp_max:
                rules_triggered.append(RuleResult(
                    rule_id="temp_max_exceeded",
                    triggered=True,
                    severity="warning",
                    message=f"Temperature {temp_f}°F exceeds maximum threshold {self.temp_max}°F"
                ))
                logger.info(f"Rule triggered: Temp {temp_f}°F > {self.temp_max}°F (warning)")
        
        # Rule 4: Combined - HR very high AND SpO2 low => critical
        if hr_value is not None and spo2_value is not None:
            if hr_value > self.hr_very_high and spo2_value < self.spo2_low:
                rules_triggered.append(RuleResult(
                    rule_id="hr_high_spo2_low_combined",
                    triggered=True,
                    severity="critical",
                    message=f"Critical combination: Heart rate {hr_value} very high (> {self.hr_very_high}) AND SpO2 {spo2_value} low (< {self.spo2_low})"
                ))
                logger.error(f"Combined rule triggered: HR {hr_value} > {self.hr_very_high} AND SpO2 {spo2_value} < {self.spo2_low} (critical)")
        
        # Determine overall severity
        overall_severity = self._determine_overall_severity(rules_triggered)
        
        return overall_severity, rules_triggered
    
    def _get_vital_value(self, vitals: Dict[str, Any], vital_name: str) -> Optional[float]:
        """Extract numeric value from vital sign"""
        vital = vitals.get(vital_name)
        if vital is None:
            return None
        
        if isinstance(vital, dict):
            return vital.get("value")
        
        return None
    
    def _to_fahrenheit(self, value: float, unit: str) -> float:
        """Convert temperature to Fahrenheit"""
        unit_lower = unit.lower()
        if "celsius" in unit_lower or "c" == unit_lower:
            return (value * 9/5) + 32
        elif "fahrenheit" in unit_lower or "f" == unit_lower:
            return value
        else:
            # Assume Fahrenheit if unknown
            logger.warning(f"Unknown temperature unit: {unit}, assuming Fahrenheit")
            return value
    
    def _determine_overall_severity(self, rules_triggered: List[RuleResult]) -> str:
        """Determine overall severity from triggered rules"""
        if not rules_triggered:
            return "OK"
        
        # Check for critical severity
        if any(rule.severity == "critical" for rule in rules_triggered):
            return "critical"
        
        # Check for warning severity
        if any(rule.severity == "warning" for rule in rules_triggered):
            return "warning"
        
        return "OK"

