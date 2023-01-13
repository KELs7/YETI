I = importlib

rswp_reserves = ForeignHash(foreign_contract='con_rocketswap_official_v1_1', foreign_name='reserves')
balances = Hash(default_value=0)
metadata = Hash()

TOKEN_CONTRACT = 'con_yeti_contract'

WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
WALLET_YETI_LP = 'a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca'
WALLET_YETI_RAIN = 'e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73'
WALLET_YETI_MARKETING = '3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9'
WALLET_YETI_CHARITY = '4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94'
WALLET_YETI_BUYBACK = 'b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc'


@construct
def init():
    # Token info
    balances[WALLET_CHIEF] = 100_000_000_000 
    metadata['token_name'] = 'YETI TOKEN'
    metadata['token_symbol'] = 'YETI'
    metadata['owners'] = [WALLET_CHIEF, WALLET_NIEL]
    # Swap info
    metadata['swap_token'] =  'con_marmite100_contract'
    metadata['swap_end'] = now + datetime.timedelta(days=180)       # HOW MANY DAYS TO AGREE ON? 6 MONTHS?
    metadata['swap_rate'] = decimal('1')
    # Wallets
    metadata['rewards_contract'] = 'con_yeti_rewards'   
    metadata['LP_wallet'] = WALLET_YETI_LP    
    metadata['rain_wallet'] = WALLET_YETI_RAIN    
    metadata['marketing_wallet'] = WALLET_YETI_MARKETING       
    metadata['charity_wallet'] = WALLET_YETI_CHARITY
    metadata['buyback_wallet'] = WALLET_YETI_BUYBACK
    metadata['burn_wallet'] = 'yeti_burn_wallet'
    # TODO: rule out contracts by checking for "con_"
    
    metadata['blacklisted_wallets'] = [
        '1b6a98bc717d568379218ca87b2b8f67b561ee1e50049da1af8f104270816a6b',
        WALLET_CHIEF,
        WALLET_NIEL,
        WALLET_YETI_LP,
        WALLET_YETI_RAIN,
        WALLET_YETI_MARKETING,
        WALLET_YETI_CHARITY,
        WALLET_YETI_BUYBACK
    ]

    # Rates
    metadata['buy_tax'] = decimal('0.02') #2%
    metadata['sell_tax'] = decimal('0.05') #5%
    metadata['rewards%'] = decimal('0.1') #10% of tax
    metadata['LP%'] = decimal('0.35') #35% of tax
    metadata['rain%'] = decimal('0.05') #5% of tax
    metadata['marketing%'] = decimal('0.5') #50% of tax
    metadata['charity%'] = decimal('0.00') #0% of tax
    metadata['buyback%'] = decimal('0.00') #0% of tax
    metadata['burn%'] = decimal('0.00') #0% of tax
    # DEX
    metadata['dex'] = ['con_rocketswap_official_v1_1']
    # Reward token
    metadata['reward_token'] = 'con_lusd_lst001'

    metadata['bridge'] = ['con_lamden_link_bsc_v1', 'con_lamden_link_weth_v1']


# LST002 with governance

@export
def change_metadata(key: str, value: Any):
    assert_owner()
    owners = metadata['owners']
    caller = ctx.caller

    metadata[caller, key] = {'v':value, 'time':now}
    agreed = False
    for owner in owners:
        if metadata[owner, key] is None:
            # Without this initial value, we cannot later compare the proposed value "v"
            metadata[owner, key] = {'v':'', 'time':''}

        # Ensure caller's proposed value is not compared to itself   
        if owner != caller and metadata[owner, key]['v'] == metadata[caller, key]['v'] :
            metadata[key] = value
            agreed = True

    if agreed:
        for owner in owners:
            # Prevent proposed value been used again by some owner in the future
            metadata[caller, key] = str(now)
        return f'{key} = {value}'

    return agreed


# LST001 with extra features

@export
def mint(amount: float, to: str):
    assert ctx.caller in metadata['bridge'], f'Only bridge can mint!'
    assert amount > 0, 'Cannot mint negative balances!'
    balances[to] += amount

@export
def transfer(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'

    sender = ctx.caller
    signer = ctx.signer

    assert balances[sender] >= amount, 'Not enough YETI to send!'

    if signer not in metadata['owners'] and sender in metadata['dex']:
        tax_amount = amount * metadata['buy_tax']
        amount_to_buyer = amount - tax_amount

        balances[sender] -= amount
        balances[to] += amount_to_buyer
        # Transfers to YETI fund wallets
        balances[metadata['marketing_wallet']] += tax_amount * metadata['marketing%']
        balances[metadata['LP_wallet']] += tax_amount * metadata['LP%']
        balances[metadata['rewards_contract']] += tax_amount * metadata['rewards%']
        balances[metadata['rain_wallet']] += tax_amount * metadata['rain%']
        balances[metadata['charity_wallet']] += tax_amount * metadata['charity%']
        balances[metadata['buyback_wallet']] += tax_amount * metadata['buyback%']
        balances[metadata['burn_wallet']] += tax_amount * metadata['burn%']

        return
        
    balances[sender] -= amount
    balances[to] += amount

@export
def approve(amount: float, to: str):
    assert amount > 0, 'Cannot send negative balances!'

    sender = ctx.caller
    balances[sender, to] += amount
    return balances[sender, to]

@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, 'Cannot send negative balances!'
    
    spender = ctx.caller
    signer = ctx.signer

    tax_amount = amount * metadata['sell_tax']
    amount_to_spend = tax_amount + amount

    if signer not in metadata['owners']:
        assert balances[main_account] > amount_to_spend, \
            f'Not enough tokens to pay tax! Expected tax to pay is {tax_amount}'
        assert balances[main_account, spender] >= amount_to_spend, \
            f'Not enough YETI approved to send! You have {balances[main_account, spender]} \
            and are trying to spend {amount}'
    assert balances[main_account] >= amount, 'Not enough YETI to send!'
    
    balances[main_account, spender] -= amount
    balances[main_account] -= amount
    balances[to] += amount

    if signer not in metadata['owners'] and to in metadata['dex']:
        pay_tax(tax_amount, spender, main_account)

def pay_tax(tax_amount, spender, main_account):
    # check if there is a rocketswap market for this token
    if rswp_reserves[TOKEN_CONTRACT] == None: # reserve initial value is None in testing environment
        return 
    if rswp_reserves[TOKEN_CONTRACT] == [0,0]: # reserve initial value on mainnet
        return 

    balances[main_account, spender] -= tax_amount
    balances[main_account] -= tax_amount
    # Transfers to YETI fund wallets
    balances[metadata['marketing_wallet']] += tax_amount * metadata['marketing%']
    balances[metadata['LP_wallet']] += tax_amount * metadata['LP%']
    balances[metadata['rewards_contract']] += tax_amount * metadata['rewards%']
    balances[metadata['rain_wallet']] += tax_amount * metadata['rain%']
    balances[metadata['charity_wallet']] += tax_amount * metadata['charity%']
    balances[metadata['buyback_wallet']] += tax_amount * metadata['buyback%']
    balances[metadata['burn_wallet']] += tax_amount * metadata['burn%']
    
@export 
def distribute_rewards(addresses: list, holder_min: float, \
    distribute_min: float, fee_cover_perc: float):
    assert_owner()
    rewards_contract = I.import_module(metadata['rewards_contract'])
    rewards_contract.distribute_rewards(contract=metadata['reward_token'],
        addresses=addresses, holder_min=holder_min, distribute_min=distribute_min, \
        fee_cover_perc=fee_cover_perc)

@export 
def swap_token(amount: float):
    caller = ctx.caller
    assert amount > 0, 'Cannot send negative balances!'
    assert caller not in metadata['blacklisted_wallets'], 'this wallet is blacklisted'
    assert not caller.startswith('con_'), 'Caller is a contract!'
    assert balances[WALLET_CHIEF] > amount, f'Token amount left is {balances[WALLET_CHIEF]} \
        and you are trying to swap for {amount}'
    assert now < metadata['swap_end'], 'Swap is over!'

    contract = metadata['swap_token']
    swap_token = I.import_module(contract)

    swap_token.transfer_from(amount=amount, to=metadata['burn_wallet'], main_account=caller)
    amount_of_yeti = amount * metadata['swap_rate'] 
    balances[caller] += amount_of_yeti
    balances[WALLET_CHIEF] -= amount_of_yeti

@export
def execute_proposal_after_a_month(key: str):
    assert_owner()
    caller = ctx.caller
    assert metadata[caller, key], 'Proposal does not exist!'
    assert now > metadata[caller, key]['time'] + datetime.timedelta(weeks=4) , \
        'Proposal must be 1 month old!'
    metadata[key] = metadata[caller, key]['v']
    return True

def assert_owner():
    assert ctx.caller in metadata['owners'], 'Only owner can call this method!'
