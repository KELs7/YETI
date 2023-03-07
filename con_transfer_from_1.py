I = importlib

YETI = "con_yeti_contract"

operator = Variable()


@construct
def init():
    operator.set(YETI)


@export
def transfer_from(caller: str, contract: str, contract_method: str, amount: 
    float, to: str, main_account: str, tax_amount: float):
    assert_operator()

    yeti_balances = ForeignHash(foreign_contract=YETI, foreign_name="balances")

    approved = yeti_balances[main_account, caller]
    main_account_balance = yeti_balances[main_account]

    if contract == "con_rocketswap_official_v1_1":
        if contract_method == "sell":
            amount_to_spend = amount + tax_amount

            assert approved >= amount_to_spend, f"Not enough coins approved to send! You have {approved} and are trying to spend {amount_to_spend}"
            assert main_account_balance >= amount_to_spend, f"Not enough coins to pay tax of {tax_amount}!"

            return amount

        else:
            # here works in the case of contract_method == 'create_market' 
            # or contract_method == 'add_liquidity'
            assert approved >= amount, f"Not enough coins approved to send! You have {approved} and are trying to spend {amount}"
            assert main_account_balance >= amount, "Not enough coins to send!"

            return amount


def assert_operator():
    assert ctx.caller == operator.get(), "Only operator can call!"
