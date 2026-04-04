from app.analyzer import analyze_comment, detect_intent, detect_sentiment
from app.balancer import balance_viewers
from app.schemas import CommentRequest, ViewerAccount, ViewerBalancingRequest


def test_buying_comment_gets_high_score():
    result = analyze_comment(CommentRequest(comment="Shop oi ib minh de minh dat 2 san pham"))
    assert result.intent == "buying_intent"
    assert result.lead_score >= 80
    assert result.priority == "high"


def test_spam_comment_gets_low_score():
    result = analyze_comment(CommentRequest(comment="Spam link https://abc.xyz kiem tien"))
    assert result.intent == "spam"
    assert result.lead_score <= 10
    assert result.priority == "low"


def test_rule_based_predictors_still_work_without_models():
    assert detect_intent("shop oi bao nhieu vay") in {"ask_price", "other"}
    assert detect_sentiment("dep qua shop") in {"positive", "neutral"}


def test_balancer_moves_viewers_from_overloaded_accounts():
    response = balance_viewers(
        ViewerBalancingRequest(
            incoming_viewers=300,
            accounts=[
                ViewerAccount(
                    account_id="tiktok-a",
                    platform="tiktok",
                    current_viewers=900,
                    max_capacity=850,
                    lag_signal=0.9,
                    engagement_rate=0.7,
                ),
                ViewerAccount(
                    account_id="facebook-b",
                    platform="facebook",
                    current_viewers=350,
                    max_capacity=900,
                    lag_signal=0.2,
                    engagement_rate=0.5,
                ),
            ],
        )
    )
    assert response.recommended_entry_account_id == "facebook-b"
    assert len(response.transfer_plan) >= 1
