from cua.surface.browser import BrowserSession
from cua.artifact import store
from cua.replay.executor import replay
from cua.escalation.operator_cli import to_operator

import os
from dotenv import load_dotenv
load_dotenv()


TEST_USERNAME_SUCCESS = os.environ.get("PARABANK_USERNAME_SUCCESS", "test_user")
TEST_PASSWORD_SUCCESS = os.environ.get("PARABANK_PASSWORD_SUCCESS", "test_password")

capability = store.load("parabank.login")

with BrowserSession(headless=False) as session:
    capability.entry_url = "https://parabank.parasoft.com/parabank/nonexistent.htm"
    result = replay(
        session, 
        capability, 
        {"username": f"{TEST_USERNAME_SUCCESS}", "password": f"{TEST_PASSWORD_SUCCESS}"},
        on_escalation=lambda req: to_operator(req, __import__("cua.escalation.handoff", fromlist=["HandoffState"]).HandoffState()))
    # print(result)