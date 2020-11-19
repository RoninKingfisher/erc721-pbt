import os
import brownie
from brownie.test import strategy
from brownie.exceptions import VirtualMachineError


class StateMachine:
    st_owner = strategy("address")
    st_spender = strategy("address")
    st_sender = strategy("address")
    st_receiver = strategy("address")
    st_token = strategy("uint256", min_value=1, max_value=5)

    def __init__(self, accounts, contract, DEBUG=None):
        self.accounts = accounts
        self.contract = contract
        self.DEBUG = DEBUG != None or os.getenv("PBT_DEBUG", "no") == "yes"
        self.VERIFY_EVENTS = os.getenv("PBT_VERIFY_EVENTS") == "yes"
        self.VERIFY_RETURN_VALUES = (
            os.getenv("PBT_VERIFY_RETURN_VALUES") == "yes"
        )

    def setup(self):
        # tokenId -> owner address - must match contract's ownerOf(tokenId)
        self.owner = { tokenId: self.contract for tokenId in self.tokens }

        # address -> number of tokens - must match contract's balanceOf(address)
        self.balances = { addr: 0 for addr in self.accounts} 

        # tokenId -> approved address - must match contract's getApproved(address)
        self.approved = { tokenId : 0 for tokenId in self.tokens }

        # address -> list of approved operators - for each address x in operators[address]
        # isApprovedForAll(address,x) must return true
        self.operators = { addr : [] for addr in self.accounts }

    # def teardown(self):
        
        

    def canTransfer(self,sender, owner, tokenId):
        return owner == self.owner[tokenId] and (
                  sender == owner or 
                  sender == self.approved[tokendId] or
                  sender in self.operators[owner] )

    def rule_transferFrom(self, st_sender, st_owner, st_receiver, st_token):
        if self.canTransfer(st_sender, st_owner, st_token):
            tx = self.contract.transferFrom(st_owner, st_receiver, st_token, { "from": st_sender }) 
            self.owner[st_token] = st_receiver
            self.balances[st_owner] = self.balances[st_owner] - 1
            self.balances[st_receiver] = self.balances[st_owner] + 1
            assert st_receiver == self.contract.ownerOf(st_token)
            assert self.balances[st_owner] == self.contract.balanceOf(st_owner)
            assert self.balances[st_receiver] == self.contract.balanceOf(st_receiver)
        else:
            with brownie.reverts():
                self.contract.transferFrom(st_owner, st_receiver, st_token, { "from": st_sender })


def patch_hypothesis_for_seed_handling(seed):
    import hypothesis

    h_run_state_machine = hypothesis.stateful.run_state_machine_as_test

    def run_state_machine(state_machine_factory, settings=None):
        state_machine_factory._hypothesis_internal_use_seed = seed
        h_run_state_machine(state_machine_factory, settings)

    hypothesis.stateful.run_state_machine_as_test = run_state_machine


def patch_brownie_for_assertion_detection():
    from brownie.test.managers.runner import RevertContextManager
    from brownie.exceptions import VirtualMachineError

    f = RevertContextManager.__exit__

    def alt_exit(self, exc_type, exc_value, traceback):
        if exc_type is VirtualMachineError:
            exc_value.__traceback__.tb_next = None
            if exc_value.revert_type != "revert":
                return False
        return f(self, exc_type, exc_value, traceback)

    RevertContextManager.__exit__ = alt_exit


def register_hypothesis_profiles():
    import hypothesis
    from hypothesis import settings, Verbosity, Phase

    stateful_step_count = int(os.getenv("PBT_STATEFUL_STEP_COUNT", 10))
    max_examples = int(os.getenv("PBT_MAX_EXAMPLES", 100))
    derandomize = True
    seed = int(os.getenv("PBT_SEED", 0))

    if seed != 0:
        patch_hypothesis_for_seed_handling(seed)
        derandomize = False

    patch_brownie_for_assertion_detection()

    settings.register_profile(
        "generate",
        stateful_step_count=stateful_step_count,
        max_examples=max_examples,
        phases=[Phase.generate],
        report_multiple_bugs=True,
        derandomize=derandomize,
        print_blob=True,
    )

    settings.register_profile(
        "shrinking",
        stateful_step_count=stateful_step_count,
        max_examples=max_examples,
        phases=[Phase.generate, Phase.shrink],
        report_multiple_bugs=True,
        derandomize=derandomize,
        print_blob=True,
    )


class NoRevertContextManager:
    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return True
        import traceback

        if exc_type is VirtualMachineError:
            exc_value.__traceback__.tb_next = None
        elif exc_type is AssertionError:
            exc_value.__traceback__.tb_next = None
        return False


def normal():
    return NoRevertContextManager()
