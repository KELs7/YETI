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


def buy_reward_token(contract: str, fee_cover_perc: float):
    #if nothing is passed to fee_cover_perc we assume a default value
    if fee_cover_perc == None: fee_cover_perc = decimal('0.05')
    #get total YETI balance of this contract
    yeti_amount = yeti_balance[REWARDS_CONTRACT]
    #sell YETI balance for TAU
    DEX.sell(contract=YETI, token_amount=yeti_amount)
    #get total TAU balance of this contract
    rewards_currency_amount = currency_balance[REWARDS_CONTRACT]  
    #reserve a percentage to cover for present and future transaction fees
    fee_cover  = rewards_currency_amount * fee_cover_perc
    currency_amount = rewards_currency_amount - fee_cover
    #buy reward token with TAU from YETI sell
    DEX.buy(contract=contract, currency_amount=currency_amount)
    
@export
def distribute_rewards(contract: str, addresses: list, 
    holder_min: float, distribute_min: float, fee_cover_perc: float):
    #check if caller is operator
    assert_operator()
    #if nothing is passed to holder_min and distribute_min, we assume certain default values
    if holder_min == None: holder_min = 50_000_000
    if distribute_min == None: distribute_min = 1000
    #buy reward token for distribution
    buy_reward_token(contract=contract, fee_cover_perc=fee_cover_perc)
    #get total reward token balance of this contract
    rewards_token_balance = ForeignHash(foreign_contract=contract, foreign_name='balances')
    rewards_token_amount = rewards_token_balance[REWARDS_CONTRACT]
    #check minimum reward token amount required for distribution 
    assert rewards_token_amount >= distribute_min, \
        f'Not enough funds to distribute! Current amount is {rewards_token_amount}'
    
    reward_token = I.import_module(contract)
    
    for address in addresses:
        #get holder YETI balance
        user_yeti_balance = yeti_balance[address]
        #check if holder has a certain minimum to qualify for reward and
        #if address is not a contract
        if user_yeti_balance >= holder_min and not address.startswith('con_'):
            #calculate amount to reward
            reward_amount = rewards_token_amount * (user_yeti_balance/100_000_000_000)
            #transfer reward to holder
            reward_token.transfer(amount=reward_amount, to=address)

def assert_operator():
    assert ctx.caller == operator.get(), 'Only operator can call!'
