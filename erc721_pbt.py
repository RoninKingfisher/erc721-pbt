import os
import brownie
from brownie.test import strategy
from brownie.exceptions import VirtualMachineError
from hypothesis.strategies import sampled_from


class Options:
    VERIFY_EVENTS = os.getenv("PBT_VERIFY_EVENTS", "no") == "yes"
    VERIFY_RETURN_VALUES = os.getenv("PBT_VERIFY_RETURN_VALUES", "no") == "yes"
    DEBUG = os.getenv("PBT_DEBUG", "no") == "yes"
    STATEFUL_STEP_COUNT = int(os.getenv("PBT_STATEFUL_STEP_COUNT", 10))
    MAX_EXAMPLES = int(os.getenv("PBT_MAX_EXAMPLES", 100))
    SEED = int(os.getenv("PBT_SEED", 0))
    ACCOUNTS = int(os.getenv("PBT_ACCOUNTS", 4))
    TOKENS = int(os.getenv("PBT_TOKENS", 6))


class StateMachine:
    st_owner = strategy("uint256", min_value=0, max_value=Options.ACCOUNTS - 1)
    st_sender = strategy("uint256", min_value=0, max_value=Options.ACCOUNTS - 1)
    st_receiver = strategy(
        "uint256", min_value=0, max_value=Options.ACCOUNTS - 1
    )
    st_token = strategy("uint256", min_value=1, max_value=Options.TOKENS)
    st_bool = strategy("bool" )

    def __init__(self, wallets, contract, DEBUG=None):
        self.wallets = wallets
        self.addr2idx = { addr: i for i,addr in enumerate(wallets)}
        self.addr2idx[0] = -1
        self.addr2idx[brownie.convert.to_address('0x0000000000000000000000000000000000000000')] = -1
        self.tokens = range(1, Options.TOKENS + 1)
        self.contract = contract

    def setup(self):
        # tokenId -> owner address - must match contract's ownerOf(tokenId)
        self.owner = {tokenId: self.contract.address for tokenId in self.tokens}

        # address -> number of tokens - must match contract's balanceOf(address)
        self.balance = {addr: 0 for addr in range(Options.ACCOUNTS)}

        # tokenId -> approved address - must match contract's getApproved(address)
        self.approved = {tokenId: -1 for tokenId in self.tokens}

        # address -> list of approved operators - for each address x in operators[address]
        # isApprovedForAll(address,x) must return true
        self.operators = {addr: set() for addr in range(Options.ACCOUNTS)}

        # Callback for initial setup (contract-dependent)
        self.onSetup()

        if Options.DEBUG:
            print("setup()")
            self.dumpState()

    def teardown(self):
        if Options.DEBUG:
            print("teardown()")
            self.dumpState()

    def canTransfer(self, sender, owner, tokenId):
        return owner == self.owner[tokenId] and (
            sender == owner
            or sender == self.approved[tokenId]
            or sender in self.operators[owner]
        )

    def rule_transferFrom(self, st_owner, st_receiver, st_token, st_sender):
        if Options.DEBUG:
            print(
                "transferFrom(owner {},receiver {},token {} [sender: {}])".format(
                    st_owner, st_receiver, st_token, st_sender
                )
            )
        if self.canTransfer(st_sender, st_owner, st_token):
            tx = self.contract.transferFrom(
                self.wallets[st_owner],
                self.wallets[st_receiver],
                st_token,
                {"from": self.wallets[st_sender]},
            )
            self.owner[st_token] = st_receiver
            self.approved[st_token] = -1
            self.balance[st_owner] = self.balance[st_owner] - 1
            self.balance[st_receiver] = self.balance[st_receiver] + 1

            self.verifyOwner(st_token)
            self.verifyApproved(st_token)
            self.verifyBalance(st_owner)
            self.verifyBalance(st_receiver)
            self.verifyEvent(
                tx,
                "Transfer",
                {
                    "_from": self.wallets[st_owner],
                    "_to": self.wallets[st_receiver],
                    "_tokenId": st_token
                },
            )
        else:
            with brownie.reverts():
                self.contract.transferFrom(
                    self.wallets[st_owner],
                    self.wallets[st_receiver],
                    st_token,
                    {"from": self.wallets[st_sender]},
                )
    def rule_safeTransferFrom(self, st_owner, st_receiver, st_token, st_sender):
        if Options.DEBUG:
            print(
                "safeTransferFrom({},{},{} [sender: {}])".format(
                    st_owner, st_receiver, st_token, st_sender
                )
            )
        if self.canTransfer(st_sender, st_owner, st_token):
            tx = self.contract.safeTransferFrom(
                self.wallets[st_owner],
                self.wallets[st_receiver],
                st_token,
                {"from": self.wallets[st_sender]},
            )
            self.owner[st_token] = st_receiver
            self.approved[st_token] = -1
            self.balance[st_owner] = self.balance[st_owner] - 1
            self.balance[st_receiver] = self.balance[st_receiver] + 1

            self.verifyOwner(st_token)
            self.verifyApproved(st_token)
            self.verifyBalance(st_owner)
            self.verifyBalance(st_receiver)
            self.verifyEvent(
                tx,
                "Transfer",
                {
                    "_from": self.wallets[st_owner],
                    "_to": self.wallets[st_receiver],
                    "_tokenId": st_token
                },
            )
        else:
            with brownie.reverts():
                self.contract.safeTransferFrom(
                    self.wallets[st_owner],
                    self.wallets[st_receiver],
                    st_token,
                    {"from": self.wallets[st_sender]},
                )

    def rule_approve(self, st_sender, st_token, st_receiver):
        if Options.DEBUG:
            print(
                "approve({},{}) [sender: {}])".format(
                    st_receiver, st_token, st_sender
                )
            )
        if st_receiver != self.owner[st_token] and \
           (self.owner[st_token] == st_sender 
           or st_sender in self.operators[self.owner[st_token]]):
            with normal():
                tx = self.contract.approve(
                    self.wallets[st_receiver], st_token,{"from": self.wallets[st_sender]}
                )
                self.approved[st_token] = st_receiver
                self.verifyApproved(st_token)
                self.verifyEvent(
                    tx,
                    "Approval",
                    {"_owner": self.wallets[self.owner[st_token]], "_tokenId": st_token, "_approved": self.wallets[st_receiver]}
                )
        else:
            with brownie.reverts():
                self.contract.approve(
                    self.wallets[st_receiver], st_token,{"from": self.wallets[st_sender]}
                )

    def rule_setApprovalForAll(self, st_sender, st_receiver, st_bool):
        if Options.DEBUG:
            print(
                "setApprovedForAll({}, {}) [sender: {}])".format(
                    st_receiver, st_bool, st_sender
                )
            )
        if st_receiver != st_sender:
            with normal():
                tx = self.contract.setApprovalForAll(
                        self.wallets[st_receiver], 
                        st_bool, {"from":self.wallets[st_sender]})
                if st_bool:
                   self.operators[st_sender].add(st_receiver)
                elif st_receiver in self.operators[st_sender]:
                   self.operators[st_sender].remove(st_receiver)
                self.verifySetApprovedForAll(st_sender, st_receiver)
                self.verifyEvent(
                    tx,
                    "ApprovalForAll",
                    {"_owner": self.wallets[st_sender], "_operator": self.wallets[st_receiver], "_approved": st_bool}
                )
        else:
            with brownie.reverts():
                tx = self.contract.setApprovalForAll(
                        self.wallets[st_receiver], 
                        st_bool, {"from":self.wallets[st_sender]})

    def verifyOwner(self, tokenId):
        self.verifyValue(
            "ownerOf({})".format(tokenId),
            self.owner[tokenId],
            self.addr2idx[self.contract.ownerOf(tokenId)]
        )

    def verifyBalance(self, wIdx):
        self.verifyValue(
            "balanceOf({})".format(wIdx),
            self.balance[wIdx],
            self.contract.balanceOf(self.wallets[wIdx]),
        )

    def verifyApproved(self, token):
        self.verifyValue(
            "getApproved({})".format(token),
            self.approved[token],
            self.addr2idx[self.contract.getApproved(token)]
        )

    def verifySetApprovedForAll(self, sender, receiver):
        self.verifyValue(
            "isApprovedForAll({}, {})".format(sender, receiver),
            receiver in self.operators[sender],
            self.contract.isApprovedForAll(self.wallets[sender], self.wallets[receiver])
        )

    def verifyEvent(self, tx, eventName, data):
        if Options.VERIFY_EVENTS:
            if not eventName in tx.events:
                raise AssertionError(
                    "{}: event was not fired".format(eventName)
                )
            ev = tx.events[eventName]
            for k in data:
                if not k in ev:
                    raise AssertionError(
                        "{}.{}: absent event data".format(eventName, k)
                    )
                self.verifyValue("{}.{}".format(eventName, k), data[k], ev[k])

    def verifyReturnValue(self, tx, expected):
        if Options.VERIFY_RETURN_VALUES:
            self.verifyValue("return value", expected, tx.return_value)

    def verifyValue(self, msg, expected, actual):
        if expected != actual:
            self.value_failure = True
            raise AssertionError(
                "{} : expected value {}, actual value was {}".format(
                    msg, expected, actual
                )
            )

    def dumpMap(self, desc, map):
        print(desc + " {")
        for k in map:
            print("{} ----> {}".format(k, map[k]))
        print("}")

    def dumpState(self):
        print("= STATE =")
        self.dumpMap("owner", self.owner)
        self.dumpMap("balance", self.balance)
        self.dumpMap("approved", self.approved)
        self.dumpMap("operators", self.operators)


def patch_hypothesis_for_seed_handling(seed):
    import hypothesis

    h_run_state_machine = hypothesis.stateful.run_state_machine_as_test

    def run_state_machine(state_machine_factory, settings=None):
        state_machine_factory._hypothesis_internal_use_seed = seed
        h_run_state_machine(state_machine_factory, settings)

    hypothesis.stateful.run_state_machine_as_test = run_state_machine

def patch_hypothesis_for_fuzz_behavior():
    import hypothesis

    # Replacement for method should_generate_more in hypothesis.internal.conjecture.engine.ConjectureRunner
    def should_generate_more_patch(self):
        # End the generation phase where we would have ended it if no bugs had
        # been found.  This reproduces the exit logic in `self.test_function`,
        # but with the important distinction that this clause will move on to
        # the shrinking phase having found one or more bugs, while the other
        # will exit having found zero bugs.
        if self.valid_examples >= self.settings.max_examples or self.call_count >= max(
            self.settings.max_examples * 10, 1000
        ):  # pragma: no cover
            return False

        # If we haven't found a bug, keep looking - if we hit any limits on
        # the number of tests to run that will raise an exception and stop
        # the run.
        if not self.interesting_examples:
            return True
        # If we've found a bug and won't report more than one, stop looking.
        elif not self.settings.report_multiple_bugs:
            return False
        assert self.first_bug_found_at <= self.last_bug_found_at <= self.call_count
        # PATCH IS HERE
        return self.valid_examples <= self.settings.max_examples \
            and self.call_count <= 2 * self.settings.max_examples
    hypothesis.internal.conjecture.engine.ConjectureRunner.should_generate_more = should_generate_more_patch 


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

    derandomize = True

    if Options.SEED != 0:
        patch_hypothesis_for_seed_handling(Options.SEED)
        derandomize = False

    patch_hypothesis_for_fuzz_behavior()
    patch_brownie_for_assertion_detection()

    settings.register_profile(
        "generate",
        stateful_step_count=Options.STATEFUL_STEP_COUNT,
        max_examples=Options.MAX_EXAMPLES,
        phases=[Phase.generate],
        report_multiple_bugs=True,
        derandomize=derandomize,
        print_blob=True,
    )

    settings.register_profile(
        "shrinking",
        stateful_step_count=Options.STATEFUL_STEP_COUNT,
        max_examples=Options.MAX_EXAMPLES,
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
