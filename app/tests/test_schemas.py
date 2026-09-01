import pytest
from pydantic import ValidationError

from schemas.auth import UserLoginRequest, UserRegisterRequest
from schemas.ticket import TicketCreateRequest, TicketUpdateRequest


def test_ticket_create_request_valid():
    req = TicketCreateRequest(
        subject="Cannot login",
        description="I cannot access my account after reset.",
        priority="high",
    )
    assert req.subject == "Cannot login"
    assert req.priority == "high"


def test_ticket_create_request_rejects_bad_priority():
    with pytest.raises(ValidationError):
        TicketCreateRequest(
            subject="x",
            description="This description is long enough.",
            priority="urgent",
        )


def test_ticket_create_request_rejects_short_subject():
    with pytest.raises(ValidationError):
        TicketCreateRequest(subject="x", description="Some long description here.")


def test_ticket_create_request_default_priority():
    req = TicketCreateRequest(
        subject="Help needed", description="Valid long description."
    )
    assert req.priority == "medium"


def test_ticket_update_request_allows_partial():
    req = TicketUpdateRequest(status="resolved")
    assert req.status == "resolved"
    assert req.priority is None
    assert req.comment is None


def test_user_register_request_rejects_bad_email():
    with pytest.raises(ValidationError):
        UserRegisterRequest(email="not-an-email", password="secret", full_name="A")


def test_user_login_request_valid():
    req = UserLoginRequest(email="a@b.com", password="secret")
    assert req.email == "a@b.com"