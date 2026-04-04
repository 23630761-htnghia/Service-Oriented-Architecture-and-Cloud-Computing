from __future__ import annotations

from collections import defaultdict

from fastapi import FastAPI, HTTPException

from app.schemas import (
    HealthResponse,
    LivestreamAccount,
    LivestreamAccountCreate,
    PlatformAccountsGroup,
    PlatformSummary,
)

app = FastAPI(
    title="Account Service",
    version="0.2.0",
    description="Demo account and livestream configuration service.",
)

PLATFORM_DISPLAY_NAMES = {
    "tiktok": "TikTok Live",
    "facebook": "Facebook Live",
    "youtube": "YouTube Live",
}

accounts: list[LivestreamAccount] = [
    LivestreamAccount(
        account_id="tiktok-a",
        name="TikTok Fashion Room",
        platform="tiktok",
        owner_name="Linh",
        current_viewers=900,
        max_capacity=850,
        engagement_rate=0.70,
        lag_signal=0.90,
        status="warning",
    ),
    LivestreamAccount(
        account_id="tiktok-b",
        name="TikTok Accessories Hub",
        platform="tiktok",
        owner_name="Ha",
        current_viewers=510,
        max_capacity=920,
        engagement_rate=0.62,
        lag_signal=0.28,
        status="stable",
    ),
    LivestreamAccount(
        account_id="facebook-a",
        name="Facebook Beauty Live",
        platform="facebook",
        owner_name="Trang",
        current_viewers=350,
        max_capacity=900,
        engagement_rate=0.50,
        lag_signal=0.20,
        status="stable",
    ),
    LivestreamAccount(
        account_id="facebook-b",
        name="Facebook Mom & Baby",
        platform="facebook",
        owner_name="Ngan",
        current_viewers=640,
        max_capacity=980,
        engagement_rate=0.67,
        lag_signal=0.31,
        status="active",
    ),
    LivestreamAccount(
        account_id="youtube-a",
        name="YouTube Premium Stream",
        platform="youtube",
        owner_name="Khoa",
        current_viewers=420,
        max_capacity=780,
        engagement_rate=0.58,
        lag_signal=0.35,
        status="stable",
    ),
    LivestreamAccount(
        account_id="youtube-b",
        name="YouTube Gadget Showcase",
        platform="youtube",
        owner_name="Vy",
        current_viewers=280,
        max_capacity=700,
        engagement_rate=0.44,
        lag_signal=0.18,
        status="active",
    ),
]


def normalize_platform(platform: str) -> str:
    return platform.strip().lower()


def display_name_for_platform(platform: str) -> str:
    return PLATFORM_DISPLAY_NAMES.get(platform, platform.title())


def build_platform_summary(platform: str, platform_accounts: list[LivestreamAccount]) -> PlatformSummary:
    total_accounts = len(platform_accounts)
    total_viewers = sum(account.current_viewers for account in platform_accounts)
    total_capacity = sum(account.max_capacity for account in platform_accounts)
    active_accounts = sum(1 for account in platform_accounts if account.status in {"active", "stable", "warning"})
    average_lag_signal = 0.0
    if total_accounts:
        average_lag_signal = round(
            sum(account.lag_signal for account in platform_accounts) / total_accounts,
            2,
        )

    return PlatformSummary(
        platform=platform,
        display_name=display_name_for_platform(platform),
        total_accounts=total_accounts,
        active_accounts=active_accounts,
        total_viewers=total_viewers,
        total_capacity=total_capacity,
        average_lag_signal=average_lag_signal,
    )


def group_accounts_by_platform() -> list[PlatformAccountsGroup]:
    grouped: dict[str, list[LivestreamAccount]] = defaultdict(list)
    for account in accounts:
        grouped[account.platform].append(account)

    groups: list[PlatformAccountsGroup] = []
    for platform in sorted(grouped):
        platform_accounts = sorted(grouped[platform], key=lambda item: item.name)
        groups.append(
            PlatformAccountsGroup(
                platform=platform,
                display_name=display_name_for_platform(platform),
                accounts=platform_accounts,
                summary=build_platform_summary(platform, platform_accounts),
            )
        )
    return groups


def generate_account_id(platform: str) -> str:
    platform_accounts = [account for account in accounts if account.platform == platform]
    return f"{platform}-{len(platform_accounts) + 1}"


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="account-service")


@app.get("/livestream-accounts", response_model=list[LivestreamAccount])
def list_livestream_accounts() -> list[LivestreamAccount]:
    return sorted(accounts, key=lambda item: (item.platform, item.name))


@app.get("/livestream-accounts/grouped", response_model=list[PlatformAccountsGroup])
def list_grouped_livestream_accounts() -> list[PlatformAccountsGroup]:
    return group_accounts_by_platform()


@app.get("/platform-summaries", response_model=list[PlatformSummary])
def list_platform_summaries() -> list[PlatformSummary]:
    return [group.summary for group in group_accounts_by_platform()]


@app.get("/platforms/{platform}/accounts", response_model=list[LivestreamAccount])
def list_accounts_by_platform(platform: str) -> list[LivestreamAccount]:
    normalized_platform = normalize_platform(platform)
    filtered_accounts = [account for account in accounts if account.platform == normalized_platform]
    if not filtered_accounts:
        raise HTTPException(status_code=404, detail="Khong tim thay tai khoan cho nen tang nay.")
    return sorted(filtered_accounts, key=lambda item: item.name)


@app.post("/livestream-accounts", response_model=LivestreamAccount)
def create_livestream_account(payload: LivestreamAccountCreate) -> LivestreamAccount:
    normalized_platform = normalize_platform(payload.platform)
    account = LivestreamAccount(
        account_id=generate_account_id(normalized_platform),
        name=payload.name,
        platform=normalized_platform,
        owner_name=payload.owner_name,
        current_viewers=payload.current_viewers,
        max_capacity=payload.max_capacity,
        engagement_rate=payload.engagement_rate,
        lag_signal=payload.lag_signal,
        status=payload.status,
    )
    accounts.append(account)
    return account
