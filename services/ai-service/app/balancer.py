from __future__ import annotations

from math import floor

from app.schemas import (
    TransferSuggestion,
    ViewerAllocation,
    ViewerBalancingRequest,
    ViewerBalancingResponse,
)


def classify_lag_risk(viewers: int, weighted_capacity: int, lag_signal: float) -> str:
    if weighted_capacity <= 0:
        return "critical"

    utilization = viewers / weighted_capacity
    adjusted_utilization = utilization + lag_signal * 0.4

    if adjusted_utilization >= 1.05:
        return "critical"
    if adjusted_utilization >= 0.9:
        return "high"
    if adjusted_utilization >= 0.7:
        return "medium"
    return "low"


def compute_weighted_capacity(account, protect_high_engagement_streams: bool) -> int:
    lag_penalty = 1 - (account.lag_signal * 0.35)
    engagement_bonus = 1.0
    if protect_high_engagement_streams:
        engagement_bonus += account.engagement_rate * 0.15

    raw_capacity = account.max_capacity * lag_penalty * engagement_bonus * account.manual_priority
    weighted_capacity = max(1, floor(raw_capacity))
    return min(weighted_capacity, floor(account.max_capacity * 1.2))


def choose_entry_account(allocations: list[ViewerAllocation]) -> str:
    best = min(
        allocations,
        key=lambda item: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}[item.lag_risk],
            item.projected_viewers / max(item.weighted_capacity, 1),
            -item.weighted_capacity,
        ),
    )
    return best.account_id


def build_recommendation(viewer_delta: int, lag_risk: str) -> str:
    if lag_risk in {"critical", "high"} and viewer_delta < 0:
        return "Giam tai ngay, ha bitrate hoac chuyen mot phan nguoi xem sang kenh khac."
    if viewer_delta > 0:
        return "Co the tiep tuc nhan them nguoi xem trong cua so tiep theo."
    if viewer_delta < 0:
        return "Nen dieu huong bot nguoi xem de tranh tang do tre."
    return "Giu on dinh phien livestream hien tai."


def apportion_targets(capacities: list[int], total_viewers: int) -> list[int]:
    capacity_sum = sum(capacities)
    if capacity_sum <= 0:
        return [0 for _ in capacities]

    raw_targets = [(total_viewers * capacity) / capacity_sum for capacity in capacities]
    targets = [floor(value) for value in raw_targets]
    remainder = total_viewers - sum(targets)

    ranked = sorted(
        enumerate(raw_targets),
        key=lambda item: item[1] - floor(item[1]),
        reverse=True,
    )
    for index, _ in ranked[:remainder]:
        targets[index] += 1
    return targets


def build_transfer_plan(allocations: list[ViewerAllocation]) -> list[TransferSuggestion]:
    sources: list[tuple[str, int]] = []
    targets: list[tuple[str, int]] = []

    for item in allocations:
        if item.viewer_delta < 0:
            sources.append((item.account_id, abs(item.viewer_delta)))
        elif item.viewer_delta > 0:
            targets.append((item.account_id, item.viewer_delta))

    transfer_plan: list[TransferSuggestion] = []
    source_index = 0
    target_index = 0

    while source_index < len(sources) and target_index < len(targets):
        source_account, source_capacity = sources[source_index]
        target_account, target_need = targets[target_index]
        moved = min(source_capacity, target_need)

        if moved > 0:
            transfer_plan.append(
                TransferSuggestion(
                    from_account_id=source_account,
                    to_account_id=target_account,
                    viewers_to_shift=moved,
                    reason="Can bang tai giua cac tai khoan de giam nguy co lag.",
                )
            )

        source_capacity -= moved
        target_need -= moved
        sources[source_index] = (source_account, source_capacity)
        targets[target_index] = (target_account, target_need)

        if source_capacity == 0:
            source_index += 1
        if target_need == 0:
            target_index += 1

    return transfer_plan


def balance_viewers(request: ViewerBalancingRequest) -> ViewerBalancingResponse:
    weighted_capacities = [
        compute_weighted_capacity(account, request.protect_high_engagement_streams)
        for account in request.accounts
    ]
    total_projected_viewers = sum(account.current_viewers for account in request.accounts) + request.incoming_viewers
    target_viewers = apportion_targets(weighted_capacities, total_projected_viewers)

    allocations: list[ViewerAllocation] = []
    for account, weighted_capacity, target in zip(request.accounts, weighted_capacities, target_viewers):
        delta = target - account.current_viewers
        lag_risk = classify_lag_risk(account.current_viewers, weighted_capacity, account.lag_signal)
        allocations.append(
            ViewerAllocation(
                account_id=account.account_id,
                current_viewers=account.current_viewers,
                target_viewers=target,
                projected_viewers=target,
                viewer_delta=delta,
                lag_risk=lag_risk,
                weighted_capacity=weighted_capacity,
                recommendation=build_recommendation(delta, lag_risk),
            )
        )

    transfer_plan = build_transfer_plan(allocations)
    recommended_entry_account_id = choose_entry_account(allocations)
    high_risk_count = sum(1 for item in allocations if item.lag_risk in {"high", "critical"})

    summary = (
        f"Da danh gia {len(allocations)} tai khoan livestream. "
        f"Phat hien {high_risk_count} tai khoan co nguy co lag cao, "
        f"va de xuat kenh uu tien nhan viewer moi la {recommended_entry_account_id}."
    )

    return ViewerBalancingResponse(
        summary=summary,
        total_current_viewers=sum(account.current_viewers for account in request.accounts),
        total_incoming_viewers=request.incoming_viewers,
        allocations=allocations,
        transfer_plan=transfer_plan,
        recommended_entry_account_id=recommended_entry_account_id,
    )
