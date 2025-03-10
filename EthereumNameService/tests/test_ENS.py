import pytest
from erc721_pbt import StateMachine, Options
from brownie import TokenReceiver, ENSRegistry

@pytest.fixture()
def contract2test(BaseRegistrarImplementation):
    yield BaseRegistrarImplementation


class BaseRegistrarImplementation(StateMachine):
    def __init__(self, accounts, contract2test):
        wallets = list()
        for i in range(0, Options.ACCOUNTS):
            tr = TokenReceiver.deploy({"from": accounts[i] })
            wallets.append(tr.address)
        ens = ENSRegistry.deploy({"from": wallets[0]})
        contract = contract2test.deploy(ens, {"from": wallets[0]})
        contract.addController(wallets[0], { "from": wallets[0] } )
        super().__init__(self, wallets, contract)

    def onSetup(self):
        for tokenId in range(1, Options.TOKENS + 1):
            account = tokenId % Options.ACCOUNTS
            address = self.wallets[account]
            self.contract.mint(address, tokenId, { "from": self.wallets[0] } )
            self.owner[tokenId] = account
            self.balance[account] = self.balance.get(account, 0) + 1

def test_stateful(contract2test, accounts, state_machine):
    state_machine(BaseRegistrarImplementation, accounts, contract2test)
