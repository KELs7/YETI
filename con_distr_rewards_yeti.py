I = importlib

import currency as tau
import con_yeti_contract as yeti_token
import con_rocketswap_official_v1_1

YETI = "con_yeti_contract"
DEX = con_rocketswap_official_v1_1
REWARDS_CONTRACT = "con_distr_rewards_yeti"

yeti_balance = ForeignHash(foreign_contract=YETI, foreign_name="balances")

operator = Variable()
tau_to_distribute = Variable()


@construct
def init():
    operator.set(YETI)
    tau_to_distribute.set(decimal("0.00"))
    approve()


@export
def approve():
    tau.approve(amount=9999999999999999999999, to="con_rocketswap_official_v1_1")
    yeti_token.approve(amount=9999999999999999999999, to="con_rocketswap_official_v1_1")


@export
def sell_yeti_for_rewards(cost_of_distr: float, reward_token: str):
    # check if caller is operator
    assert_operator()
    # get total YETI balance of this contract
    yeti_amount = yeti_balance[REWARDS_CONTRACT]
    # sell all YETI for TAU
    DEX.sell(contract=YETI, token_amount=yeti_amount)
    # get total TAU balance of this contract
    currency_balance = ForeignHash(foreign_contract="currency", foreign_name="balances")
    currency_amount = currency_balance[REWARDS_CONTRACT]

    assert currency_amount > cost_of_distr, "Not enough to cover distribution fees"
    # amount worth distributing
    currency_amount -= cost_of_distr
    tau.transfer(amount=cost_of_distr, to=ctx.signer)

    if reward_token == "currency":
        tau_to_distribute.set(tau_to_distribute.get() + currency_amount)
    else:
        DEX.buy(contract=reward_token, currency_amount=currency_amount)

@export
def distribute_rewards(reward_token: str, addresses: list, amounts: list):
    assert_operator()

    if reward_token == "currency":
        for num in range(len(addresses)):
            address = addresses[num]
            amount = amounts[num]
            if not address.startswith("con_"):
                assert tau_to_distribute.get() >= decimal(
                    "0"
                ), "TAU for distribution is exhausted!"
                tau.transfer(amount=amount, to=address)
                tau_to_distribute.set(tau_to_distribute.get() - amount)
    else:
        for num in range(len(addresses)):
            address = addresses[num]
            amount = amounts[num]
            token = I.import_module(reward_token)
            if not address.startswith("con_"):
                token.transfer(amount=amount, to=address)


def assert_operator():
    assert ctx.caller == operator.get(), "Only operator can call!"
