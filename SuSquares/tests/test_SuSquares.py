import pytest
from erc721_pbt import StateMachine


@pytest.fixture()
def contract2test(SuMain):
    yield SuMain


class SuMain(StateMachine):
    def __init__(self, accounts, contract2test):
        contract = contract2test.deploy({"from": accounts[0]})
        StateMachine.__init__(self, accounts, contract, [])


def test_stateful(contract2test, accounts, state_machine):
    state_machine(SuMain, accounts, contract2test)
