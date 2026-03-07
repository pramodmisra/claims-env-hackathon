"""
Mock Plaid API for Purchase Verification

This simulates Plaid transaction verification for insurance claims.
In production, this would connect to actual Plaid API.

For hackathon: This is a mock that demonstrates the concept.
Real integration would use: pip install plaid-python
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import random


@dataclass
class TransactionMatch:
    """Represents a matched transaction from Plaid."""
    found: bool
    transaction_id: str
    amount: float
    date: str
    merchant: str
    category: str
    confidence: float
    discrepancy: bool
    discrepancy_reason: Optional[str]


class MockPlaidClient:
    """
    Mock Plaid client for transaction verification.

    In production, initialize with:
        from plaid.api import plaid_api
        from plaid.model import *

        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox,
            api_key={'clientId': PLAID_CLIENT_ID, 'secret': PLAID_SECRET}
        )
    """

    def __init__(self):
        # Mock transaction database
        self._mock_transactions = {
            "CLM-2024-001": {  # Simple auto claim
                "found": True,
                "amount": 3400.0,  # Close to $3500 claimed
                "merchant": "Auto Body Shop",
                "date": "2024-03-02",
                "category": "automotive_repair"
            },
            "CLM-2024-003": {  # Fraud case - no matching transaction
                "found": False,
                "amount": 0,
                "merchant": None,
                "date": None,
                "category": None
            },
            "CLM-2024-006": {  # Inflated claim fraud
                "found": True,
                "amount": 22000.0,  # Claims $35000 but only $22k transaction
                "merchant": "Car Dealership",
                "date": "2024-01-15",
                "category": "automotive_purchase"
            },
        }

    def verify_purchase(
        self,
        claim_id: str,
        claimed_amount: float,
        claimed_description: str,
        tolerance: float = 0.15  # 15% tolerance
    ) -> TransactionMatch:
        """
        Verify a claimed purchase against bank transactions.

        Args:
            claim_id: The claim being verified
            claimed_amount: Amount claimed
            claimed_description: Description of claimed item/service
            tolerance: Acceptable discrepancy percentage

        Returns:
            TransactionMatch with verification results
        """
        # Check mock database
        if claim_id in self._mock_transactions:
            tx = self._mock_transactions[claim_id]

            if not tx["found"]:
                return TransactionMatch(
                    found=False,
                    transaction_id="",
                    amount=0,
                    date="",
                    merchant="",
                    category="",
                    confidence=0.0,
                    discrepancy=True,
                    discrepancy_reason="No matching transaction found in bank records"
                )

            # Calculate discrepancy
            diff_pct = abs(tx["amount"] - claimed_amount) / claimed_amount
            has_discrepancy = diff_pct > tolerance

            return TransactionMatch(
                found=True,
                transaction_id=f"tx_{claim_id}_{random.randint(1000, 9999)}",
                amount=tx["amount"],
                date=tx["date"],
                merchant=tx["merchant"],
                category=tx["category"],
                confidence=0.95 if not has_discrepancy else 0.6,
                discrepancy=has_discrepancy,
                discrepancy_reason=f"Claimed ${claimed_amount:,.2f} but transaction shows ${tx['amount']:,.2f}" if has_discrepancy else None
            )

        # Default: simulate random result for unknown claims
        found = random.random() > 0.3  # 70% chance of finding transaction

        if not found:
            return TransactionMatch(
                found=False,
                transaction_id="",
                amount=0,
                date="",
                merchant="",
                category="",
                confidence=0.0,
                discrepancy=True,
                discrepancy_reason="No matching transaction found"
            )

        # Simulate matched transaction
        matched_amount = claimed_amount * random.uniform(0.85, 1.05)
        has_discrepancy = abs(matched_amount - claimed_amount) / claimed_amount > tolerance

        return TransactionMatch(
            found=True,
            transaction_id=f"tx_sim_{random.randint(10000, 99999)}",
            amount=matched_amount,
            date="2024-02-15",
            merchant="Verified Merchant",
            category="purchase",
            confidence=0.85,
            discrepancy=has_discrepancy,
            discrepancy_reason=f"Amount discrepancy detected" if has_discrepancy else None
        )


def format_verification_result(match: TransactionMatch) -> str:
    """Format verification result for display."""
    if not match.found:
        return f"VERIFICATION FAILED: {match.discrepancy_reason}"

    status = "VERIFIED" if not match.discrepancy else "DISCREPANCY DETECTED"
    result = f"{status}: Transaction found - ${match.amount:,.2f} at {match.merchant} on {match.date}"

    if match.discrepancy:
        result += f" | WARNING: {match.discrepancy_reason}"

    return result


# Example usage for future real Plaid integration:
"""
# Real Plaid integration would look like:

import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest

class RealPlaidClient:
    def __init__(self, client_id: str, secret: str, env: str = "sandbox"):
        configuration = plaid.Configuration(
            host=plaid.Environment.Sandbox if env == "sandbox" else plaid.Environment.Production,
            api_key={
                'clientId': client_id,
                'secret': secret,
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def get_transactions(self, access_token: str, start_date: str, end_date: str):
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        response = self.client.transactions_get(request)
        return response['transactions']

    def verify_purchase(self, access_token: str, claimed_amount: float, date_range: tuple):
        transactions = self.get_transactions(access_token, date_range[0], date_range[1])

        # Find matching transaction
        for tx in transactions:
            if abs(tx['amount'] - claimed_amount) / claimed_amount < 0.15:
                return TransactionMatch(
                    found=True,
                    transaction_id=tx['transaction_id'],
                    amount=tx['amount'],
                    date=tx['date'],
                    merchant=tx['merchant_name'],
                    category=tx['category'][0] if tx['category'] else 'unknown',
                    confidence=0.9,
                    discrepancy=False,
                    discrepancy_reason=None
                )

        return TransactionMatch(found=False, ...)
"""
