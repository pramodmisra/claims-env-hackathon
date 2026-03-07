"""
Mock Enterprise Systems for Insurance Claims Processing

Simulates real insurance company backend systems:
- Policy Database
- Claims History System
- Fraud Detection API
- Document Management System

These create partial observability - agent must query to learn.
"""

import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib


@dataclass
class ClaimScenario:
    """Pre-defined claim scenario for consistent episodes."""
    claim_id: str
    claim_type: str
    claim_amount: float
    claimant_name: str
    incident_date: str
    description: str

    # Ground truth (hidden from agent)
    true_verdict: str
    correct_payout: float
    is_fraud: bool
    fraud_type: Optional[str]

    # Policy details
    policy_id: str
    policy_coverage_limit: float
    policy_deductible: float
    policy_status: str
    coverage_exclusions: List[str]

    # Complexity
    complexity: str
    requires_documents: List[str]
    requires_escalation: bool

    # Claim history
    past_claims_count: int
    past_claims_total: float
    recent_claims_30_days: int


# Pre-defined scenarios for reproducibility
CLAIM_SCENARIOS: List[ClaimScenario] = [
    # Scenario 1: Simple auto claim - approve
    ClaimScenario(
        claim_id="CLM-2024-001",
        claim_type="auto_collision",
        claim_amount=3500.0,
        claimant_name="John Smith",
        incident_date="2024-03-01",
        description="Rear-ended at stoplight. Bumper and taillight damage.",
        true_verdict="approve",
        correct_payout=3000.0,  # After $500 deductible
        is_fraud=False,
        fraud_type=None,
        policy_id="POL-AUTO-78234",
        policy_coverage_limit=50000.0,
        policy_deductible=500.0,
        policy_status="active",
        coverage_exclusions=[],
        complexity="simple",
        requires_documents=["photos"],
        requires_escalation=False,
        past_claims_count=1,
        past_claims_total=1200.0,
        recent_claims_30_days=0,
    ),

    # Scenario 2: Home water damage - partial approve (over limit)
    ClaimScenario(
        claim_id="CLM-2024-002",
        claim_type="home_water",
        claim_amount=45000.0,
        claimant_name="Sarah Johnson",
        incident_date="2024-02-28",
        description="Burst pipe caused flooding in basement. Extensive water damage.",
        true_verdict="partial_approve",
        correct_payout=24000.0,  # Limited by coverage cap minus deductible
        is_fraud=False,
        fraud_type=None,
        policy_id="POL-HOME-45123",
        policy_coverage_limit=25000.0,
        policy_deductible=1000.0,
        policy_status="active",
        coverage_exclusions=["flood_external"],
        complexity="standard",
        requires_documents=["photos", "repair_estimates"],
        requires_escalation=False,
        past_claims_count=0,
        past_claims_total=0.0,
        recent_claims_30_days=0,
    ),

    # Scenario 3: Fraud - staged accident
    ClaimScenario(
        claim_id="CLM-2024-003",
        claim_type="auto_collision",
        claim_amount=12000.0,
        claimant_name="Mike Thompson",
        incident_date="2024-03-03",
        description="T-bone collision at intersection. Major damage to driver side.",
        true_verdict="deny",
        correct_payout=0.0,
        is_fraud=True,
        fraud_type="staged_accident",
        policy_id="POL-AUTO-91827",
        policy_coverage_limit=75000.0,
        policy_deductible=500.0,
        policy_status="active",
        coverage_exclusions=[],
        complexity="fraud",
        requires_documents=["photos", "police_report"],
        requires_escalation=True,
        past_claims_count=4,
        past_claims_total=28000.0,
        recent_claims_30_days=2,
    ),

    # Scenario 4: Deny - coverage exclusion
    ClaimScenario(
        claim_id="CLM-2024-004",
        claim_type="home_water",
        claim_amount=18000.0,
        claimant_name="Emily Chen",
        incident_date="2024-03-02",
        description="Flooding from nearby river after heavy rains.",
        true_verdict="deny",
        correct_payout=0.0,
        is_fraud=False,
        fraud_type=None,
        policy_id="POL-HOME-67890",
        policy_coverage_limit=100000.0,
        policy_deductible=1000.0,
        policy_status="active",
        coverage_exclusions=["flood_external", "earthquake"],
        complexity="standard",
        requires_documents=["photos"],
        requires_escalation=False,
        past_claims_count=1,
        past_claims_total=5000.0,
        recent_claims_30_days=0,
    ),

    # Scenario 5: Complex - large claim requiring escalation
    ClaimScenario(
        claim_id="CLM-2024-005",
        claim_type="home_fire",
        claim_amount=150000.0,
        claimant_name="Robert Williams",
        incident_date="2024-02-25",
        description="Kitchen fire spread to living room. Significant structural damage.",
        true_verdict="approve",
        correct_payout=147500.0,  # After $2500 deductible
        is_fraud=False,
        fraud_type=None,
        policy_id="POL-HOME-34521",
        policy_coverage_limit=200000.0,
        policy_deductible=2500.0,
        policy_status="active",
        coverage_exclusions=["intentional_damage"],
        complexity="complex",
        requires_documents=["photos", "fire_report", "repair_estimates", "inventory_list"],
        requires_escalation=True,  # Large claims need escalation
        past_claims_count=0,
        past_claims_total=0.0,
        recent_claims_30_days=0,
    ),

    # Scenario 6: Fraud - inflated claim
    ClaimScenario(
        claim_id="CLM-2024-006",
        claim_type="auto_theft",
        claim_amount=35000.0,
        claimant_name="David Miller",
        incident_date="2024-03-04",
        description="Vehicle stolen from parking lot. Claims vehicle had $10k in upgrades.",
        true_verdict="deny",
        correct_payout=0.0,
        is_fraud=True,
        fraud_type="inflated_claim",
        policy_id="POL-AUTO-55432",
        policy_coverage_limit=40000.0,
        policy_deductible=1000.0,
        policy_status="active",
        coverage_exclusions=[],
        complexity="fraud",
        requires_documents=["police_report", "purchase_receipts"],
        requires_escalation=True,
        past_claims_count=2,
        past_claims_total=15000.0,
        recent_claims_30_days=1,
    ),

    # Scenario 7: Liability claim - approve
    ClaimScenario(
        claim_id="CLM-2024-007",
        claim_type="liability",
        claim_amount=8500.0,
        claimant_name="Jennifer Davis",
        incident_date="2024-02-20",
        description="Visitor slipped on icy walkway. Medical bills for sprained ankle.",
        true_verdict="approve",
        correct_payout=8500.0,  # No deductible for liability
        is_fraud=False,
        fraud_type=None,
        policy_id="POL-HOME-78901",
        policy_coverage_limit=100000.0,
        policy_deductible=0.0,  # Liability has no deductible
        policy_status="active",
        coverage_exclusions=[],
        complexity="standard",
        requires_documents=["medical_records", "incident_report"],
        requires_escalation=False,
        past_claims_count=0,
        past_claims_total=0.0,
        recent_claims_30_days=0,
    ),

    # Scenario 8: Deny - policy lapsed
    ClaimScenario(
        claim_id="CLM-2024-008",
        claim_type="auto_collision",
        claim_amount=5500.0,
        claimant_name="Amanda Wilson",
        incident_date="2024-03-05",
        description="Hit deer on highway. Front end damage.",
        true_verdict="deny",
        correct_payout=0.0,
        is_fraud=False,
        fraud_type=None,
        policy_id="POL-AUTO-12345",
        policy_coverage_limit=50000.0,
        policy_deductible=500.0,
        policy_status="lapsed",  # Policy not active!
        coverage_exclusions=[],
        complexity="simple",
        requires_documents=["photos"],
        requires_escalation=False,
        past_claims_count=2,
        past_claims_total=3000.0,
        recent_claims_30_days=0,
    ),
]


class MockPolicyDB:
    """Simulates policy database - agent must query to get coverage details."""

    def __init__(self, scenario: ClaimScenario):
        self.scenario = scenario

    def lookup_policy(self) -> Dict[str, Any]:
        """Returns policy information. Costs 1 query and 2 minutes."""
        return {
            "policy_id": self.scenario.policy_id,
            "policy_status": self.scenario.policy_status,
            "coverage_type": self._get_coverage_type(),
            "coverage_limit": self.scenario.policy_coverage_limit,
            "deductible": self.scenario.policy_deductible,
            "effective_date": "2023-01-01",
            "expiration_date": "2024-12-31" if self.scenario.policy_status == "active" else "2024-01-15",
        }

    def _get_coverage_type(self) -> str:
        if "auto" in self.scenario.claim_type:
            return "comprehensive_auto"
        elif "home" in self.scenario.claim_type:
            return "homeowners_standard"
        else:
            return "liability_general"


class MockClaimsHistoryDB:
    """Simulates claims history system."""

    def __init__(self, scenario: ClaimScenario):
        self.scenario = scenario

    def get_claim_history(self) -> Dict[str, Any]:
        """Returns claimant's claims history. Costs 1 query and 3 minutes."""
        return {
            "claimant_name": self.scenario.claimant_name,
            "total_past_claims": self.scenario.past_claims_count,
            "total_claimed_amount": self.scenario.past_claims_total,
            "claims_last_30_days": self.scenario.recent_claims_30_days,
            "claims_last_year": self.scenario.past_claims_count,
            "average_claim_amount": self.scenario.past_claims_total / max(1, self.scenario.past_claims_count),
            "claim_frequency": "high" if self.scenario.past_claims_count > 3 else "normal",
        }


class MockFraudAPI:
    """Simulates fraud detection system with ML-based risk scoring."""

    def __init__(self, scenario: ClaimScenario):
        self.scenario = scenario

    def check_fraud_signals(self) -> Dict[str, Any]:
        """
        Returns fraud analysis. Costs 1 query and 5 minutes.
        Note: Has false positives/negatives to make it realistic.
        """
        flags = []
        risk_score = 0.1  # Base risk

        # Generate realistic fraud signals
        if self.scenario.recent_claims_30_days > 0:
            flags.append("multiple_claims_30_days")
            risk_score += 0.2

        if self.scenario.past_claims_count > 3:
            flags.append("high_claim_frequency")
            risk_score += 0.15

        if self.scenario.claim_amount > self.scenario.policy_coverage_limit * 0.8:
            flags.append("near_coverage_limit")
            risk_score += 0.1

        if self.scenario.is_fraud:
            # True fraud cases have higher signals
            flags.append("pattern_match_known_fraud")
            risk_score += 0.4
            if self.scenario.fraud_type == "staged_accident":
                flags.append("inconsistent_damage_pattern")
            elif self.scenario.fraud_type == "inflated_claim":
                flags.append("claim_amount_anomaly")
        else:
            # Some false positives for realism
            if random.random() < 0.1:
                flags.append("minor_documentation_gap")
                risk_score += 0.05

        risk_score = min(0.95, risk_score)  # Cap at 0.95

        return {
            "risk_score": round(risk_score, 2),
            "flags": flags,
            "recommendation": self._get_recommendation(risk_score),
            "confidence": 0.85 if self.scenario.is_fraud else 0.75,
        }

    def _get_recommendation(self, risk_score: float) -> str:
        if risk_score > 0.7:
            return "deny_high_risk"
        elif risk_score > 0.4:
            return "manual_review_required"
        else:
            return "proceed_normal"


class MockDocumentSystem:
    """Simulates document management - slow but provides evidence."""

    def __init__(self, scenario: ClaimScenario):
        self.scenario = scenario

    def request_documents(self, doc_types: List[str]) -> Dict[str, Any]:
        """
        Request and verify documents. Costs 1 query and 10 minutes.
        Returns what documents were received and their status.
        """
        results = {}

        for doc_type in doc_types:
            if doc_type in self.scenario.requires_documents:
                # Document is required and available
                results[doc_type] = {
                    "status": "received",
                    "verified": True,
                    "notes": f"{doc_type.replace('_', ' ').title()} verified and matches claim."
                }
            else:
                # Document not required but requested
                results[doc_type] = {
                    "status": "not_required",
                    "verified": False,
                    "notes": f"{doc_type.replace('_', ' ').title()} not required for this claim type."
                }

        # Add fraud-specific document issues
        if self.scenario.is_fraud and "photos" in doc_types:
            results["photos"]["notes"] = "Photos received but metadata shows inconsistencies."
            results["photos"]["verified"] = False

        return {
            "documents": results,
            "all_required_received": all(
                doc in doc_types for doc in self.scenario.requires_documents
            ),
            "missing_documents": [
                doc for doc in self.scenario.requires_documents
                if doc not in doc_types
            ],
        }


class MockCoverageVerifier:
    """Verifies if specific damage types are covered."""

    def __init__(self, scenario: ClaimScenario):
        self.scenario = scenario

    def verify_coverage(self, damage_type: str) -> Dict[str, Any]:
        """
        Check if damage type is covered. Costs 1 query and 2 minutes.
        """
        # Map claim types to expected damage types
        covered_damages = {
            "auto_collision": ["collision", "vehicle_damage", "property_damage"],
            "auto_theft": ["theft", "stolen_vehicle", "stolen_contents"],
            "home_water": ["water_damage", "pipe_burst", "plumbing"],
            "home_fire": ["fire", "smoke_damage", "structural"],
            "liability": ["bodily_injury", "property_damage", "medical"],
        }

        # Check exclusions
        if damage_type in self.scenario.coverage_exclusions:
            return {
                "damage_type": damage_type,
                "is_covered": False,
                "reason": f"Excluded by policy: {damage_type}",
                "exclusion_clause": f"Section 4.{self.scenario.coverage_exclusions.index(damage_type) + 1}",
            }

        # Check if damage type matches claim type
        expected_damages = covered_damages.get(self.scenario.claim_type, [])
        is_covered = damage_type.lower() in [d.lower() for d in expected_damages]

        return {
            "damage_type": damage_type,
            "is_covered": is_covered,
            "reason": "Covered under policy" if is_covered else "Not covered under this policy type",
            "coverage_section": "Section 2.1" if is_covered else None,
        }


class MockPayoutCalculator:
    """Calculates correct payout based on policy terms."""

    def __init__(self, scenario: ClaimScenario):
        self.scenario = scenario

    def calculate_payout(self, claimed_amount: float) -> Dict[str, Any]:
        """
        Calculate payout. Costs 1 query and 3 minutes.
        Returns breakdown of payout calculation.
        """
        # Start with claimed amount
        base_amount = claimed_amount

        # Apply deductible
        after_deductible = max(0, base_amount - self.scenario.policy_deductible)

        # Apply coverage limit
        final_payout = min(after_deductible, self.scenario.policy_coverage_limit)

        # Check policy status
        if self.scenario.policy_status != "active":
            final_payout = 0

        return {
            "claimed_amount": claimed_amount,
            "deductible_applied": self.scenario.policy_deductible,
            "after_deductible": after_deductible,
            "coverage_limit": self.scenario.policy_coverage_limit,
            "final_payout": final_payout,
            "payout_breakdown": {
                "base": base_amount,
                "deductible": -self.scenario.policy_deductible,
                "limit_adjustment": min(0, self.scenario.policy_coverage_limit - after_deductible),
            },
            "notes": self._get_notes(final_payout, after_deductible),
        }

    def _get_notes(self, final: float, after_ded: float) -> str:
        if self.scenario.policy_status != "active":
            return "Policy is not active. No payout eligible."
        elif final < after_ded:
            return f"Payout capped at coverage limit of ${self.scenario.policy_coverage_limit:,.2f}"
        else:
            return "Standard calculation applied."


def get_random_scenario(seed: Optional[int] = None) -> ClaimScenario:
    """Get a random scenario, optionally with seed for reproducibility."""
    if seed is not None:
        random.seed(seed)
    return random.choice(CLAIM_SCENARIOS)


def get_scenario_by_id(claim_id: str) -> Optional[ClaimScenario]:
    """Get a specific scenario by claim ID."""
    for scenario in CLAIM_SCENARIOS:
        if scenario.claim_id == claim_id:
            return scenario
    return None


def get_scenario_by_index(index: int) -> ClaimScenario:
    """Get scenario by index (for deterministic testing)."""
    return CLAIM_SCENARIOS[index % len(CLAIM_SCENARIOS)]
