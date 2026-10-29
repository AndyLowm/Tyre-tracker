import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.database import get_session
from app.dependencies.auth_flow import get_acc_id
from collections.abc import Iterator

@pytest.fixture
def session():
    engine = create_engine(
        url="sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

@pytest.fixture
def client(session: Session)-> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_acc_id] = lambda: 1
    yield TestClient(app)
    app.dependency_overrides.clear()

TYRE  = {
    "make": "michelin", "model": "pilot",
    "width": 205, "aspect_ratio": 55, "rim": 16, "speed_rating": "v",
    "cost_price": 50,
    "location_stock": {"unit": 1, "van": 4},
}
@pytest.fixture
def tyre(client: TestClient) -> dict:
    """ A tyre already in the db with 1 in unit and 4 in van """
    res = client.post(url="/tyre/add-tyre", json=TYRE)
    assert res.status_code == 201
    return res.json()