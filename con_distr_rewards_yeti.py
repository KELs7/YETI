I = importlib

import currency as tau
import con_yeti_contract as yeti_token
import con_rocketswap_official_v1_1

YETI = 'con_yeti_contract'
DEX = con_rocketswap_official_v1_1
REWARDS_CONTRACT = 'con_distr_rewards_yeti'

yeti_balance = ForeignHash(foreign_contract=YETI, foreign_name='balances')

operator = Variable()
tau_to_distribute = Variable()

@construct
def init():
    operator.set(YETI)
    tau_to_distribute.set(decimal('0.00'))
    approve()


@export
def approve():
    tau.approve(amount=9999999999999999999999, to='con_rocketswap_official_v1_1')
    yeti_token.approve(amount=9999999999999999999999, to='con_rocketswap_official_v1_1')

@export
def sell_yeti_for_rewards(cost_of_distr: float, reward_token: str):
    #check if caller is operator
    assert_operator()
    #get total YETI balance of this contract
    yeti_amount = yeti_balance[REWARDS_CONTRACT]
    #sell all YETI for TAU
    DEX.sell(contract=YETI, token_amount=yeti_amount)
    #get total TAU balance of this contract
    currency_balance = ForeignHash(foreign_contract='currency', foreign_name='balances')
    currency_amount = currency_balance[REWARDS_CONTRACT] 

    assert currency_amount > cost_of_distr, 'Not enough to cover distribution fees'
    #amount worth distributing
    currency_amount -= cost_of_distr

    if reward_token == 'currency':
        tau_to_distribute.set(tau_to_distribute.get() + currency_amount)
    else:
        DEX.buy(contract=reward_token, currency_amount=currency_amount)

@export
def distribute_rewards(reward_token: str, addresses: list, holder_min: float, 
    cost_of_distr: float, eligible_total_balance: float):
    #check if caller is operator
    assert_operator()
    #if nothing is passed to holder_min we assume a certain default value
    if holder_min == None: holder_min = 50_000_000

    if reward_token == 'currency':

        rewards_token_amount = tau_to_distribute.get()

        for address in addresses:
            #get holder YETI balance
            user_yeti_balance = yeti_balance[address]
            #check if holder has a certain minimum to qualify for reward and
            #if address is not a contract
            if user_yeti_balance >= holder_min and not address.startswith('con_'):
                #calculate amount to reward
                reward_amount = rewards_token_amount * (user_yeti_balance/eligible_total_balance)
                assert tau_to_distribute.get() >= decimal('0'), 'TAU for distribution is exhaused!'
                #transfer reward to holder
                tau.transfer(amount=reward_amount, to=address)
                tau_to_distribute.set(tau_to_distribute.get() - reward_amount)
    else:
        #get total reward token balance of this contract
        rewards_token_balance = ForeignHash(foreign_contract=reward_token, 
            foreign_name='balances')
        rewards_token_amount = rewards_token_balance[REWARDS_CONTRACT]
        token = I.import_module(reward_token)

        for address in addresses:
            #get holder YETI balance
            user_yeti_balance = yeti_balance[address]
            #check if holder has a certain minimum to qualify for reward and
            #if address is not a contract
            if user_yeti_balance >= holder_min and not address.startswith('con_'):
                #calculate amount to reward
                reward_amount = rewards_token_amount * (user_yeti_balance/eligible_total_balance)
                #transfer reward to holder
                token.transfer(amount=reward_amount, to=address)

def assert_operator():
    assert ctx.caller == operator.get(), 'Only operator can call!'
