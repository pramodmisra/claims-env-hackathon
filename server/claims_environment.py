"""
Insurance Claims Processing Environment

OpenEnv environment for training LLMs to process insurance claims.
Implements Statement 3.1: Professional Tasks with enterprise workflow complexity.

Key Features:
- Partial observability (agent must query to learn)
- Multi-step decision making
- Fraud detection challenges
- Business rule enforcement
- Efficiency vs accuracy trade-offs
"""

import uuid
from typing import Optional, Tuple, List
from openenv.core.env_server import Environment

# Support both package import and direct import (for HF Spaces)
try:
    from ..models import ClaimsAction, ClaimsObservation, ClaimsState
    from .mock_systems import (
        ClaimScenario,
        MockPolicyDB,
        MockClaimsHistoryDB,
        MockFraudAPI,
        MockDocumentSystem,
        MockCoverageVerifier,
        MockPayoutCalculator,
        get_random_scenario,
        get_scenario_by_index,
    )
    from .plaid_mock import MockPlaidClient, format_verification_result
except ImportError:
    from models import ClaimsAction, ClaimsObservation, ClaimsState
    from server.mock_systems import (
        ClaimScenario,
        MockPolicyDB,
        MockClaimsHistoryDB,
        MockFraudAPI,
        MockDocumentSystem,
        MockCoverageVerifier,
        MockPayoutCalculator,
        get_random_scenario,
        get_scenario_by_index,
    )
    from server.plaid_mock import MockPlaidClient, format_verification_result


class ClaimsEnvironment(Environment):
    """
    Insurance Claims Processing Environment.

    Agent must process insurance claims by:
    1. Gathering information through queries
    2. Detecting potential fraud
    3. Verifying coverage
    4. Making approve/deny/escalate decisions

    Rewards are based on:
    - Decision correctness
    - Fraud detection
    - Processing efficiency
    """

    VALID_ACTIONS = [
        "query_policy",
        "query_claim_history",
        "check_fraud",
        "request_documents",
        "verify_coverage",
        "verify_purchase",  # Plaid-powered transaction verification
        "calculate_payout",
        "approve",
        "deny",
        "escalate",
    ]

    # Time costs for each action (simulated minutes)
    ACTION_TIME_COSTS = {
        "query_policy": 2,
        "query_claim_history": 3,
        "check_fraud": 5,
        "request_documents": 10,
        "verify_coverage": 2,
        "verify_purchase": 8,  # Plaid API call takes time
        "calculate_payout": 3,
        "approve": 1,
        "deny": 1,
        "escalate": 5,
    }

    def __init__(self, scenario_index: Optional[int] = None):
        """
        Initialize environment.

        Args:
            scenario_index: If provided, use specific scenario (for testing).
                          If None, random scenario each reset.
        """
        super().__init__()
        self.scenario_index = scenario_index
        self._state: Optional[ClaimsState] = None
        self._scenario: Optional[ClaimScenario] = None
        self._mock_systems: dict = {}
        self._last_reward: float = 0.0

    def reset(self) -> ClaimsObservation:
        """
        Reset environment with a new claim to process.

        Returns initial observation with claim details (partial info only).
        """
        # Select scenario
        if self.scenario_index is not None:
            self._scenario = get_scenario_by_index(self.scenario_index)
        else:
            self._scenario = get_random_scenario()

        # Initialize mock systems
        self._mock_systems = {
            "policy": MockPolicyDB(self._scenario),
            "history": MockClaimsHistoryDB(self._scenario),
            "fraud": MockFraudAPI(self._scenario),
            "documents": MockDocumentSystem(self._scenario),
            "coverage": MockCoverageVerifier(self._scenario),
            "payout": MockPayoutCalculator(self._scenario),
            "plaid": MockPlaidClient(),  # Transaction verification
        }

        # Initialize state
        self._state = ClaimsState(
            episode_id=str(uuid.uuid4()),
            claim_id=self._scenario.claim_id,
            claim_type=self._scenario.claim_type,
            claim_amount_requested=self._scenario.claim_amount,
            true_verdict=self._scenario.true_verdict,
            correct_payout=self._scenario.correct_payout,
            is_fraud=self._scenario.is_fraud,
            fraud_type=self._scenario.fraud_type,
            policy_coverage_limit=self._scenario.policy_coverage_limit,
            policy_deductible=self._scenario.policy_deductible,
            policy_status=self._scenario.policy_status,
            coverage_exclusions=self._scenario.coverage_exclusions,
            complexity=self._scenario.complexity,
            requires_documents=self._scenario.requires_documents,
            requires_escalation=self._scenario.requires_escalation,
        )

        self._last_reward = 0.0

        # Return initial observation (partial info)
        return ClaimsObservation(
            claim_id=self._scenario.claim_id,
            claim_type=self._scenario.claim_type,
            claim_amount_requested=self._scenario.claim_amount,
            claimant_name=self._scenario.claimant_name,
            incident_date=self._scenario.incident_date,
            description=self._scenario.description,
            system_response="New claim received. Begin processing.",
            action_success=True,
            revealed_info={},
            available_actions=self.VALID_ACTIONS.copy(),
            time_elapsed_minutes=0,
            queries_made=0,
            is_terminal=False,
            reward=0.0,  # Initial observation has no reward
        )

    def step(self, action: ClaimsAction) -> ClaimsObservation:
        """
        Execute an action and return the resulting observation.

        Args:
            action: The action to take

        Returns:
            Observation after action, including reward info
        """
        if self._state is None or self._scenario is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        # Validate action
        if action.action_type not in self.VALID_ACTIONS:
            return self._create_error_observation(
                f"Invalid action: {action.action_type}. Valid: {self.VALID_ACTIONS}"
            )

        # Update state
        self._state.actions_taken += 1
        self._state.time_elapsed_minutes += self.ACTION_TIME_COSTS.get(action.action_type, 1)

        # Execute action
        observation, reward = self._execute_action(action)

        # Store reward for retrieval
        self._last_reward = reward
        self._state.total_reward += reward

        # Set reward and done on observation for OpenEnv serialization
        # OpenEnv's serialize_observation() expects observation.reward and observation.done
        observation.reward = reward
        observation.done = observation.is_terminal

        return observation

    def _execute_action(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Execute action and return observation + reward."""

        action_handlers = {
            "query_policy": self._handle_query_policy,
            "query_claim_history": self._handle_query_history,
            "check_fraud": self._handle_check_fraud,
            "request_documents": self._handle_request_documents,
            "verify_coverage": self._handle_verify_coverage,
            "verify_purchase": self._handle_verify_purchase,
            "calculate_payout": self._handle_calculate_payout,
            "approve": self._handle_approve,
            "deny": self._handle_deny,
            "escalate": self._handle_escalate,
        }

        handler = action_handlers.get(action.action_type)
        if handler:
            return handler(action)
        else:
            return self._create_error_observation(f"No handler for {action.action_type}"), 0.0

    def _handle_query_policy(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Query policy database."""
        self._state.queries_made += 1
        self._state.policy_queried = True

        result = self._mock_systems["policy"].lookup_policy()
        self._state.revealed_info = {**getattr(self._state, 'revealed_info', {}), "policy": result}

        return self._create_observation(
            f"Policy lookup complete. Status: {result['policy_status']}, "
            f"Coverage limit: ${result['coverage_limit']:,.2f}, "
            f"Deductible: ${result['deductible']:,.2f}",
            revealed_update={"policy": result}
        ), -0.1  # Small cost for query

    def _handle_query_history(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Query claims history."""
        self._state.queries_made += 1
        self._state.history_queried = True

        result = self._mock_systems["history"].get_claim_history()

        return self._create_observation(
            f"Claims history retrieved. Past claims: {result['total_past_claims']}, "
            f"Total claimed: ${result['total_claimed_amount']:,.2f}, "
            f"Recent (30 days): {result['claims_last_30_days']}",
            revealed_update={"claim_history": result}
        ), -0.1

    def _handle_check_fraud(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Run fraud detection."""
        self._state.queries_made += 1
        self._state.fraud_checked = True

        result = self._mock_systems["fraud"].check_fraud_signals()

        flags_str = ", ".join(result["flags"]) if result["flags"] else "None"

        return self._create_observation(
            f"Fraud analysis complete. Risk score: {result['risk_score']:.2f}, "
            f"Flags: {flags_str}, Recommendation: {result['recommendation']}",
            revealed_update={"fraud_analysis": result}
        ), -0.2  # Higher cost for fraud check

    def _handle_request_documents(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Request and verify documents."""
        self._state.queries_made += 1
        self._state.documents_requested = True

        doc_types = action.parameters.get("doc_types", ["photos"])
        if isinstance(doc_types, str):
            doc_types = [doc_types]

        result = self._mock_systems["documents"].request_documents(doc_types)

        missing = result.get("missing_documents", [])
        missing_str = f" Missing: {', '.join(missing)}" if missing else ""

        return self._create_observation(
            f"Documents processed. All required received: {result['all_required_received']}.{missing_str}",
            revealed_update={"documents": result}
        ), -0.5  # Documents are slow/expensive

    def _handle_verify_coverage(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Verify coverage for damage type."""
        self._state.queries_made += 1
        self._state.coverage_verified = True

        damage_type = action.parameters.get("damage_type", self._scenario.claim_type)
        result = self._mock_systems["coverage"].verify_coverage(damage_type)

        return self._create_observation(
            f"Coverage check for '{damage_type}': {'COVERED' if result['is_covered'] else 'NOT COVERED'}. "
            f"Reason: {result['reason']}",
            revealed_update={"coverage_verification": result}
        ), -0.1

    def _handle_verify_purchase(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Verify purchase via Plaid transaction data."""
        self._state.queries_made += 1

        claimed_amount = action.parameters.get("amount", self._scenario.claim_amount)
        description = action.parameters.get("description", self._scenario.description)

        result = self._mock_systems["plaid"].verify_purchase(
            claim_id=self._scenario.claim_id,
            claimed_amount=claimed_amount,
            claimed_description=description
        )

        # Build response
        verification_result = format_verification_result(result)

        # Reward for finding discrepancy (helps catch fraud)
        reward = -0.3  # Base cost for API call
        if result.discrepancy:
            reward += 2.0  # Bonus for finding discrepancy

        return self._create_observation(
            f"Plaid Verification: {verification_result}",
            revealed_update={"purchase_verification": {
                "found": result.found,
                "amount": result.amount,
                "merchant": result.merchant,
                "discrepancy": result.discrepancy,
                "discrepancy_reason": result.discrepancy_reason,
                "confidence": result.confidence,
            }}
        ), reward

    def _handle_calculate_payout(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Calculate payout amount."""
        self._state.queries_made += 1
        self._state.payout_calculated = True

        amount = action.parameters.get("amount", self._scenario.claim_amount)
        result = self._mock_systems["payout"].calculate_payout(amount)

        return self._create_observation(
            f"Payout calculated: ${result['final_payout']:,.2f}. "
            f"(Claimed: ${result['claimed_amount']:,.2f}, "
            f"Deductible: ${result['deductible_applied']:,.2f}, "
            f"Limit: ${result['coverage_limit']:,.2f})",
            revealed_update={"payout_calculation": result}
        ), -0.1

    def _handle_approve(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Approve the claim."""
        payout = action.parameters.get("payout", self._scenario.claim_amount)
        reason = action.parameters.get("reason", "Claim approved")

        self._state.agent_decision = "approve"
        self._state.agent_payout = payout
        self._state.decision_reason = reason

        reward = self._calculate_terminal_reward("approve", payout)

        return self._create_terminal_observation(
            f"CLAIM APPROVED. Payout: ${payout:,.2f}. Reason: {reason}",
            "approved"
        ), reward

    def _handle_deny(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Deny the claim."""
        reason = action.parameters.get("reason", "Claim denied")

        self._state.agent_decision = "deny"
        self._state.agent_payout = 0.0
        self._state.decision_reason = reason

        reward = self._calculate_terminal_reward("deny", 0.0)

        return self._create_terminal_observation(
            f"CLAIM DENIED. Reason: {reason}",
            "denied"
        ), reward

    def _handle_escalate(self, action: ClaimsAction) -> Tuple[ClaimsObservation, float]:
        """Escalate to senior adjuster."""
        reason = action.parameters.get("reason", "Escalated for review")

        self._state.agent_decision = "escalate"
        self._state.decision_reason = reason

        reward = self._calculate_terminal_reward("escalate", 0.0)

        return self._create_terminal_observation(
            f"CLAIM ESCALATED. Reason: {reason}",
            "escalated"
        ), reward

    def _calculate_terminal_reward(self, decision: str, payout: float) -> float:
        """
        Calculate final reward based on decision quality.

        Reward components:
        1. Correctness: Did agent make right decision?
        2. Fraud detection: Did agent catch fraud?
        3. Payout accuracy: How close to correct payout?
        4. Efficiency: How many steps/time taken?
        """
        reward = 0.0

        # 1. CORRECTNESS REWARD (+10 / -5)
        correct_decision = self._is_correct_decision(decision)
        if correct_decision:
            reward += 10.0
            self._state.correctness_reward = 10.0
        else:
            reward -= 5.0
            self._state.correctness_reward = -5.0

        # 2. FRAUD DETECTION REWARD (+5 / -10)
        if self._scenario.is_fraud:
            if decision == "deny":
                reward += 5.0  # Caught fraud!
                self._state.fraud_detection_reward = 5.0
            elif decision == "approve":
                reward -= 10.0  # Missed fraud - big penalty
                self._state.fraud_detection_reward = -10.0
            else:  # escalate
                reward += 2.0  # Partial credit for escalating suspicious case
                self._state.fraud_detection_reward = 2.0
        else:
            self._state.fraud_detection_reward = 0.0

        # 3. PAYOUT ACCURACY (for approvals)
        if decision == "approve" and self._scenario.true_verdict in ["approve", "partial_approve"]:
            payout_diff = abs(payout - self._scenario.correct_payout)
            payout_accuracy = max(0, 1 - (payout_diff / max(1, self._scenario.correct_payout)))
            accuracy_reward = payout_accuracy * 3.0  # Up to +3 for perfect payout
            reward += accuracy_reward

        # 4. EFFICIENCY REWARD
        # Penalize excessive steps
        if self._state.actions_taken > 8:
            efficiency_penalty = -0.2 * (self._state.actions_taken - 8)
            reward += efficiency_penalty
            self._state.efficiency_reward = efficiency_penalty
        elif self._state.actions_taken <= 4:
            # Bonus for quick processing (if correct)
            if correct_decision:
                reward += 1.0
                self._state.efficiency_reward = 1.0
        else:
            self._state.efficiency_reward = 0.0

        # 5. ESCALATION APPROPRIATENESS
        if decision == "escalate":
            if self._scenario.requires_escalation:
                reward += 3.0  # Correct to escalate
            else:
                reward -= 2.0  # Unnecessary escalation

        return reward

    def _is_correct_decision(self, decision: str) -> bool:
        """Check if decision matches ground truth."""
        if decision == "escalate":
            return self._scenario.requires_escalation
        elif decision == "approve":
            return self._scenario.true_verdict in ["approve", "partial_approve"]
        elif decision == "deny":
            return self._scenario.true_verdict == "deny"
        return False

    def _create_observation(
        self,
        system_response: str,
        revealed_update: dict = None
    ) -> ClaimsObservation:
        """Create a non-terminal observation."""
        # Update revealed info
        current_revealed = getattr(self, '_revealed_info', {})
        if revealed_update:
            current_revealed.update(revealed_update)
        self._revealed_info = current_revealed

        return ClaimsObservation(
            claim_id=self._scenario.claim_id,
            claim_type=self._scenario.claim_type,
            claim_amount_requested=self._scenario.claim_amount,
            claimant_name=self._scenario.claimant_name,
            incident_date=self._scenario.incident_date,
            description=self._scenario.description,
            system_response=system_response,
            action_success=True,
            revealed_info=current_revealed,
            available_actions=self.VALID_ACTIONS.copy(),
            time_elapsed_minutes=self._state.time_elapsed_minutes,
            queries_made=self._state.queries_made,
            is_terminal=False,
        )

    def _create_terminal_observation(
        self,
        system_response: str,
        terminal_reason: str
    ) -> ClaimsObservation:
        """Create a terminal observation."""
        return ClaimsObservation(
            claim_id=self._scenario.claim_id,
            claim_type=self._scenario.claim_type,
            claim_amount_requested=self._scenario.claim_amount,
            claimant_name=self._scenario.claimant_name,
            incident_date=self._scenario.incident_date,
            description=self._scenario.description,
            system_response=system_response,
            action_success=True,
            revealed_info=getattr(self, '_revealed_info', {}),
            available_actions=[],  # No more actions available
            time_elapsed_minutes=self._state.time_elapsed_minutes,
            queries_made=self._state.queries_made,
            is_terminal=True,
            terminal_reason=terminal_reason,
        )

    def _create_error_observation(self, error_message: str) -> ClaimsObservation:
        """Create an error observation."""
        return ClaimsObservation(
            claim_id=self._scenario.claim_id if self._scenario else "",
            claim_type=self._scenario.claim_type if self._scenario else "",
            claim_amount_requested=self._scenario.claim_amount if self._scenario else 0,
            claimant_name=self._scenario.claimant_name if self._scenario else "",
            incident_date=self._scenario.incident_date if self._scenario else "",
            description=self._scenario.description if self._scenario else "",
            system_response=f"ERROR: {error_message}",
            action_success=False,
            revealed_info=getattr(self, '_revealed_info', {}),
            available_actions=self.VALID_ACTIONS.copy(),
            time_elapsed_minutes=self._state.time_elapsed_minutes if self._state else 0,
            queries_made=self._state.queries_made if self._state else 0,
            is_terminal=False,
        )

    @property
    def state(self) -> ClaimsState:
        """Return current state."""
        if self._state is None:
            return ClaimsState()
        return self._state

    @property
    def reward(self) -> float:
        """Return last reward."""
        return self._last_reward
