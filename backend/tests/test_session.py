import pytest
from app.core.constants import BiologicalSex
from app.models.session import EphemeralPatientProfile
from app.services.session_service import SessionService


@pytest.mark.asyncio
async def test_session_lifecycle():
    service = SessionService()
    profile = EphemeralPatientProfile(
        name="Alex",
        age_years=35,
        biological_sex=BiologicalSex.MALE,
        country_code="US",
    )

    # 1. Create session
    session = await service.create_session(profile)
    assert session.session_id is not None
    assert session.terminated is False
    assert session.profile.name == "Alex"

    # 2. Status inspection (does not refresh TTL)
    status_data = await service.get_session_status(session.session_id)
    assert status_data["active"] is True
    assert status_data["seconds_remaining"] > 0

    # 3. Keep alive extends TTL
    old_expires = session.expires_at
    new_expires = await service.keep_alive(session.session_id)
    assert new_expires >= old_expires

    # 4. Idempotent destruction
    res1 = await service.destroy_session(session.session_id)
    assert res1 is True
    res2 = await service.destroy_session(session.session_id)
    assert res2 is True
