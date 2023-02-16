I = importlib

YETI = 'con_yeti_contract'

operator = Variable()

@construct
def init():
    operator.set(YETI)

@export
def transfer(ctx_signer: str, contract: str, contract_method: str, amount: float, 
    owners: list, tax_amount: float):
    assert_operator()

    if contract == 'con_rocketswap_official_v1_1':
        if contract_method == 'buy':
            if ctx_signer in owners:
                return amount
            else:
                amount -= tax_amount
                return amount
        else:
            #here works in the case of contract_method == remove_liquidity
            return amount

def assert_operator():
    assert ctx.caller == operator.get(), 'Only operator can call!'