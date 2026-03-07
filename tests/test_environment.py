"""
Tests for Insurance Claims Environment

Run with: pytest tests/ -v
"""

import pytest
from claims_env.models import ClaimsAction, ClaimsObservation, ClaimsState
from claims_env.server.claims_environment import ClaimsEnvironment
from claims_env.server.mock_systems import (
    get_scenario_by_index,
    MockPolicyDB,
    MockFraudAPI,
    CLAIM_SCENARIOS,
)


class TestClaimsEnvironment:
    """Test the claims environment."""

    def test_reset_returns_observation(self):
        """Test that reset returns valid observation."""
        env = ClaimsEnvironment(scenario_index=0)
        obs = env.reset()

        assert isinstance(obs, ClaimsObservation)
        assert obs.claim_id != ""
        assert obs.claim_type != ""
        assert obs.claim_amount_requested > 0
        assert not obs.is_terminal
        assert len(obs.available_actions) > 0

    def test_query_policy_action(self):
        """Test query_policy action reveals policy info."""
        env = ClaimsEnvironment(scenario_index=0)
        env.reset()

        action = ClaimsAction(action_type="query_policy")
        obs = env.step(action)

        assert obs.action_success
        assert "policy" in obs.system_response.lower() or "coverage" in obs.system_response.lower()
        assert env.state.policy_queried

    def test_check_fraud_action(self):
        """Test check_fraud action returns fraud signals."""
        env = ClaimsEnvironment(scenario_index=2)  # Fraud scenario
        env.reset()

        action = ClaimsAction(action_type="check_fraud")
        obs = env.step(action)

        assert obs.action_success
        assert "fraud" in obs.system_response.lower() or "risk" in obs.system_response.lower()
        assert env.state.fraud_checked

    def test_approve_action_terminates(self):
        """Test that approve action terminates episode."""
        env = ClaimsEnvironment(scenario_index=0)
        env.reset()

        action = ClaimsAction(
            action_type="approve",
            parameters={"payout": 3000.0, "reason": "Test approval"}
        )
        obs = env.step(action)

        assert obs.is_terminal
        assert "approved" in obs.terminal_reason.lower()

    def test_deny_action_terminates(self):
        """Test that deny action terminates episode."""
        env = ClaimsEnvironment(scenario_index=0)
        env.reset()

        action = ClaimsAction(
            action_type="deny",
            parameters={"reason": "Test denial"}
        )
        obs = env.step(action)

        assert obs.is_terminal
        assert "denied" in obs.terminal_reason.lower()

    def test_correct_approval_gives_positive_reward(self):
        """Test that correct approval gives positive reward."""
        env = ClaimsEnvironment(scenario_index=0)  # Simple approve case
        env.reset()

        # Query policy first
        env.step(ClaimsAction(action_type="query_policy"))

        # Approve
        action = ClaimsAction(
            action_type="approve",
            parameters={"payout": 3000.0}
        )
        env.step(action)

        assert env.state.total_reward > 0
        assert env.state.correctness_reward > 0

    def test_fraud_detection_gives_bonus(self):
        """Test that catching fraud gives bonus reward."""
        env = ClaimsEnvironment(scenario_index=2)  # Fraud scenario
        env.reset()

        # Deny the fraudulent claim
        action = ClaimsAction(
            action_type="deny",
            parameters={"reason": "Fraud detected"}
        )
        env.step(action)

        assert env.state.fraud_detection_reward > 0

    def test_missed_fraud_gives_penalty(self):
        """Test that approving fraud gives penalty."""
        env = ClaimsEnvironment(scenario_index=2)  # Fraud scenario
        env.reset()

        # Wrongly approve the fraudulent claim
        action = ClaimsAction(
            action_type="approve",
            parameters={"payout": 12000.0}
        )
        env.step(action)

        assert env.state.fraud_detection_reward < 0

    def test_actions_increment_counters(self):
        """Test that actions increment step counters."""
        env = ClaimsEnvironment(scenario_index=0)
        env.reset()

        assert env.state.actions_taken == 0
        assert env.state.queries_made == 0

        env.step(ClaimsAction(action_type="query_policy"))
        assert env.state.actions_taken == 1
        assert env.state.queries_made == 1

        env.step(ClaimsAction(action_type="check_fraud"))
        assert env.state.actions_taken == 2
        assert env.state.queries_made == 2

    def test_invalid_action_returns_error(self):
        """Test that invalid action returns error observation."""
        env = ClaimsEnvironment(scenario_index=0)
        env.reset()

        action = ClaimsAction(action_type="invalid_action")
        obs = env.step(action)

        assert not obs.action_success
        assert "error" in obs.system_response.lower()


class TestMockSystems:
    """Test mock backend systems."""

    def test_policy_db_returns_data(self):
        """Test policy database returns expected fields."""
        scenario = get_scenario_by_index(0)
        policy_db = MockPolicyDB(scenario)

        result = policy_db.lookup_policy()

        assert "policy_id" in result
        assert "policy_status" in result
        assert "coverage_limit" in result
        assert "deductible" in result

    def test_fraud_api_returns_risk_score(self):
        """Test fraud API returns risk score."""
        scenario = get_scenario_by_index(2)  # Fraud case
        fraud_api = MockFraudAPI(scenario)

        result = fraud_api.check_fraud_signals()

        assert "risk_score" in result
        assert 0 <= result["risk_score"] <= 1
        assert "flags" in result
        assert "recommendation" in result


class TestScenarios:
    """Test scenario coverage."""

    def test_all_scenarios_load(self):
        """Test that all scenarios can be loaded."""
        for i, scenario in enumerate(CLAIM_SCENARIOS):
            env = ClaimsEnvironment(scenario_index=i)
            obs = env.reset()
            assert obs.claim_id == scenario.claim_id

    def test_scenario_diversity(self):
        """Test scenarios cover different verdicts."""
        verdicts = set(s.true_verdict for s in CLAIM_SCENARIOS)
        assert "approve" in verdicts
        assert "deny" in verdicts
        assert "partial_approve" in verdicts

        # Check fraud cases exist
        fraud_count = sum(1 for s in CLAIM_SCENARIOS if s.is_fraud)
        assert fraud_count >= 2
