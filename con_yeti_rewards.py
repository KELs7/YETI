I = importlib

import currency as tau
import con_yeti_contract as yeti_token
import con_rocketswap_official_v1_1

YETI = 'con_yeti_contract'
DEX = con_rocketswap_official_v1_1
REWARDS_CONTRACT = 'con_yeti_rewards'

currency_balance = ForeignHash(foreign_contract='currency', foreign_name='balances')
yeti_balance = ForeignHash(foreign_contract=YETI, foreign_name='balances')

operator = Variable()

@construct
def init():
    operator.set(YETI)
    approve()


@export
def approve():
    tau.approve(amount=9999999999999999999999, to='con_rocketswap_official_v1_1')
    yeti_token.approve(amount=9999999999999999999999, to='con_rocketswap_official_v1_1')

def sell_yeti_for_rewards(cost_of_distr: float, reward_token: str):
    #get total YETI balance of this contract
    yeti_amount = yeti_balance[REWARDS_CONTRACT]
    #sell all YETI for TAU
    DEX.sell(contract=YETI, token_amount=yeti_amount)
    #get total TAU balance of this contract
    currency_amount = currency_balance[REWARDS_CONTRACT] 
    assert currency_amount > cost_of_distr, 'Not enough to cover distribution fees'
    
    if reward_token != 'currency':
        #some TAU is reserved for covering distribution fees
        currency_amount -= cost_of_distr
        #buy reward token with TAU from YETI sell
        DEX.buy(contract=reward_token, currency_amount=currency_amount)

@export
def distribute_rewards(contract: str, addresses: list, holder_min: float, 
    cost_of_distr: float, eligible_total_balance: float):
    #check if caller is operator
    assert_operator()
    #if nothing is passed to holder_min we assume a certain default value
    if holder_min == None: holder_min = 50_000_000
    #buy reward token for distribution
    sell_yeti_for_rewards(cost_of_distr=cost_of_distr, reward_token=contract)
    #get total reward token balance of this contract
    rewards_token_balance = ForeignHash(foreign_contract=contract, 
        foreign_name='balances')
    rewards_token_amount = rewards_token_balance[REWARDS_CONTRACT]
    reward_token = I.import_module(contract)

    if contract == 'currency':
        rewards_token_amount -= cost_of_distr

    for address in addresses:
        #get holder YETI balance
        user_yeti_balance = yeti_balance[address]
        #check if holder has a certain minimum to qualify for reward and
        #if address is not a contract
        if user_yeti_balance >= holder_min and not address.startswith('con_'):
            #calculate amount to reward
            reward_amount = rewards_token_amount * (user_yeti_balance/eligible_total_balance)
            #transfer reward to holder
            reward_token.transfer(amount=reward_amount, to=address)

def assert_operator():
    assert ctx.caller == operator.get(), 'Only operator can call!'
