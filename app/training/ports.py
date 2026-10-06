from datetime import date
from typing import Protocol

from app.core.features import AffiliateRawData
from app.repositories.referral_repository import ReferralCounts


class AffiliateDataPort(Protocol):
    def get_raw_data(self, affiliate_id: int, reference_date: date) -> AffiliateRawData:
        ...


class WalletActivityPort(Protocol):
    def get_last_transaction_date(self, affiliate_id: int, reference_date: date) -> date | None:
        ...


class ReferralPort(Protocol):
    def count_direct_referrals_by_status(self, affiliate_id: int) -> ReferralCounts:
        ...


class SubscriptionExpirationPort(Protocol):
    def get_days_since_expiration_by_subscription(
        self, affiliate_id: int, reference_date: date
    ) -> list[int | None]:
        ...
