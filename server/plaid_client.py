"""
Real Plaid API Client for Purchase Verification

This module provides real Plaid integration for verifying insurance claims
against actual bank transaction data.

Setup:
1. pip install plaid-python
2. Set environment variables:
   - PLAID_CLIENT_ID
   - PLAID_SECRET
   - PLAID_ENV (sandbox/development/production)

For hackathon demo, use Sandbox environment with test credentials.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

# Import Plaid SDK
try:
    import plaid
    from plaid.api import plaid_api
    from plaid.model.transactions_sync_request import TransactionsSyncRequest
    from plaid.model.transactions_get_request import TransactionsGetRequest
    from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
    from plaid.model.products import Products
    from plaid.model.country_code import CountryCode
    PLAID_AVAILABLE = True
except ImportError:
    PLAID_AVAILABLE = False
    print("Warning: plaid-python not installed. Using mock client.")


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


class PlaidClient:
    """
    Real Plaid API client for transaction verification.

    Usage:
        client = PlaidClient()

        # First, user must link their bank account via Plaid Link
        link_token = client.create_link_token(user_id="user123")
        # ... user completes Plaid Link flow, returns public_token ...
        access_token = client.exchange_public_token(public_token)

        # Now verify purchases
        result = client.verify_purchase(
            access_token=access_token,
            claimed_amount=3500.00,
            claimed_date="2024-03-01",
            claimed_description="Auto repair"
        )
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        environment: str = "sandbox"
    ):
        """
        Initialize Plaid client.

        Args:
            client_id: Plaid client ID (or set PLAID_CLIENT_ID env var)
            secret: Plaid secret (or set PLAID_SECRET env var)
            environment: "sandbox", "development", or "production"
        """
        if not PLAID_AVAILABLE:
            raise ImportError("plaid-python not installed. Run: pip install plaid-python")

        self.client_id = client_id or os.environ.get("PLAID_CLIENT_ID")
        self.secret = secret or os.environ.get("PLAID_SECRET")
        self.environment = os.environ.get("PLAID_ENV", environment)

        if not self.client_id or not self.secret:
            raise ValueError(
                "Plaid credentials required. Set PLAID_CLIENT_ID and PLAID_SECRET "
                "environment variables or pass to constructor."
            )

        # Configure Plaid client
        env_map = {
            "sandbox": plaid.Environment.Sandbox,
            "development": plaid.Environment.Development,
            "production": plaid.Environment.Production,
        }

        configuration = plaid.Configuration(
            host=env_map.get(self.environment, plaid.Environment.Sandbox),
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )

        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def create_link_token(self, user_id: str) -> str:
        """
        Create a Link token for Plaid Link flow.

        The user uses this token to connect their bank account
        through Plaid's secure UI.

        Args:
            user_id: Unique identifier for your user

        Returns:
            Link token string to initialize Plaid Link
        """
        request = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
            client_name="Insurance Claims Verifier",
            products=[Products("transactions")],
            country_codes=[CountryCode("US")],
            language="en"
        )

        response = self.client.link_token_create(request)
        return response['link_token']

    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange public token for access token.

        After user completes Plaid Link, exchange the public_token
        for a permanent access_token.

        Args:
            public_token: Token returned from Plaid Link

        Returns:
            Access token for ongoing API access
        """
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return response['access_token']

    def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions for a date range.

        Args:
            access_token: Plaid access token
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of transaction dictionaries
        """
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date()
        )

        response = self.client.transactions_get(request)
        transactions = response['transactions']

        # Paginate through all results
        while len(transactions) < response['total_transactions']:
            options = TransactionsGetRequestOptions()
            options.offset = len(transactions)

            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                options=options
            )
            response = self.client.transactions_get(request)
            transactions.extend(response['transactions'])

        return transactions

    def sync_transactions(self, access_token: str, cursor: str = None) -> Dict[str, Any]:
        """
        Sync transactions incrementally (recommended method).

        Args:
            access_token: Plaid access token
            cursor: Cursor from previous sync (None for initial sync)

        Returns:
            Dict with 'added', 'modified', 'removed' transactions and 'next_cursor'
        """
        request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=cursor
        ) if cursor else TransactionsSyncRequest(access_token=access_token)

        response = self.client.transactions_sync(request)

        all_added = response['added']
        all_modified = response['modified']
        all_removed = response['removed']

        # Paginate
        while response['has_more']:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=response['next_cursor']
            )
            response = self.client.transactions_sync(request)
            all_added.extend(response['added'])
            all_modified.extend(response['modified'])
            all_removed.extend(response['removed'])

        return {
            'added': all_added,
            'modified': all_modified,
            'removed': all_removed,
            'next_cursor': response['next_cursor']
        }

    def verify_purchase(
        self,
        access_token: str,
        claimed_amount: float,
        claimed_date: str,
        claimed_description: str = "",
        tolerance: float = 0.15,
        date_range_days: int = 30
    ) -> TransactionMatch:
        """
        Verify a claimed purchase against bank transactions.

        This is the main method for insurance claim verification.

        Args:
            access_token: Plaid access token for user's bank
            claimed_amount: Amount claimed in insurance claim
            claimed_date: Date of claimed purchase (YYYY-MM-DD)
            claimed_description: Description of claimed item/service
            tolerance: Acceptable discrepancy percentage (default 15%)
            date_range_days: Days around claimed_date to search

        Returns:
            TransactionMatch with verification results
        """
        # Parse claimed date and create search range
        claim_dt = datetime.strptime(claimed_date, "%Y-%m-%d")
        start_date = claim_dt - timedelta(days=date_range_days)
        end_date = claim_dt + timedelta(days=date_range_days)

        try:
            transactions = self.get_transactions(access_token, start_date, end_date)
        except plaid.ApiException as e:
            return TransactionMatch(
                found=False,
                transaction_id="",
                amount=0,
                date="",
                merchant="",
                category="",
                confidence=0.0,
                discrepancy=True,
                discrepancy_reason=f"Plaid API error: {e.body}"
            )

        # Find best matching transaction
        best_match = None
        best_score = 0

        for tx in transactions:
            tx_amount = abs(tx['amount'])  # Plaid amounts can be negative

            # Calculate amount similarity (0-1)
            amount_diff = abs(tx_amount - claimed_amount) / claimed_amount
            amount_score = max(0, 1 - amount_diff)

            # Calculate date similarity (0-1)
            tx_date = datetime.strptime(tx['date'], "%Y-%m-%d")
            days_diff = abs((tx_date - claim_dt).days)
            date_score = max(0, 1 - days_diff / date_range_days)

            # Calculate description similarity (simple)
            desc_score = 0.5  # Default
            if claimed_description:
                merchant = (tx.get('merchant_name') or tx.get('name') or "").lower()
                if any(word in merchant for word in claimed_description.lower().split()):
                    desc_score = 1.0

            # Combined score
            total_score = (amount_score * 0.5) + (date_score * 0.3) + (desc_score * 0.2)

            if total_score > best_score:
                best_score = total_score
                best_match = tx

        # No match found
        if not best_match or best_score < 0.5:
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

        # Check for amount discrepancy
        matched_amount = abs(best_match['amount'])
        diff_pct = abs(matched_amount - claimed_amount) / claimed_amount
        has_discrepancy = diff_pct > tolerance

        return TransactionMatch(
            found=True,
            transaction_id=best_match['transaction_id'],
            amount=matched_amount,
            date=best_match['date'],
            merchant=best_match.get('merchant_name') or best_match.get('name', 'Unknown'),
            category=best_match['category'][0] if best_match.get('category') else 'unknown',
            confidence=best_score,
            discrepancy=has_discrepancy,
            discrepancy_reason=(
                f"Claimed ${claimed_amount:,.2f} but transaction shows ${matched_amount:,.2f}"
                if has_discrepancy else None
            )
        )


def get_plaid_client() -> 'PlaidClient':
    """
    Factory function to get Plaid client.

    Returns real client if credentials are set, otherwise raises error.
    """
    if not PLAID_AVAILABLE:
        raise ImportError("plaid-python not installed")

    return PlaidClient()


# For backwards compatibility with mock
def format_verification_result(match: TransactionMatch) -> str:
    """Format verification result for display."""
    if not match.found:
        return f"VERIFICATION FAILED: {match.discrepancy_reason}"

    status = "VERIFIED" if not match.discrepancy else "DISCREPANCY DETECTED"
    result = f"{status}: Transaction found - ${match.amount:,.2f} at {match.merchant} on {match.date}"

    if match.discrepancy:
        result += f" | WARNING: {match.discrepancy_reason}"

    return result
