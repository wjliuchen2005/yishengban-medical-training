"""Unified entry must create only absent accounts and preserve existing credentials."""
import asyncio
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User
from app.schemas import UserLogin
from app.routers.auth import login
from app.auth import verify_password

@pytest.fixture
def auth_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        yield db
    engine.dispose()

def enter(db, username='newstudent', password='secure123', **kwargs):
    return asyncio.run(login(UserLogin(username=username, password=password, **kwargs), db))

def test_new_account_then_existing_login(auth_db):
    created = enter(auth_db, register_if_missing=True)
    assert created.registered and created.token
    row = auth_db.query(User).one()
    assert row.school == '南京医科大学' and verify_password('secure123', row.password_hash)
    original = row.password_hash
    again = enter(auth_db, register_if_missing=True)
    assert not again.registered and again.user.id == created.user.id
    with pytest.raises(HTTPException) as error:
        enter(auth_db, password='wrong123', register_if_missing=True)
    assert error.value.status_code == 401
    assert auth_db.query(User).count() == 1 and auth_db.query(User).one().password_hash == original

def test_legacy_login_does_not_create_account(auth_db):
    with pytest.raises(HTTPException) as error:
        enter(auth_db)
    assert error.value.status_code == 401 and auth_db.query(User).count() == 0

@pytest.mark.parametrize('username,password', [('ab','secure123'), ('a'*21,'secure123'), ('newstudent','12345'), ('newstudent','a'*21)])
def test_invalid_new_credentials_do_not_create_account(auth_db, username, password):
    with pytest.raises(HTTPException) as error:
        enter(auth_db, username, password, register_if_missing=True)
    assert error.value.status_code == 422 and auth_db.query(User).count() == 0
