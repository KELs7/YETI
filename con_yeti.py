I = importlib

balances = Hash(default_value=0)
metadata = Hash()

@construct
def init():
    # Token info
    balances["sys"] = 100_000_000_000       # WHO/WHAT WALLET HAS ALL THE SUPPLY?
    metadata["token_name"] = 'YETI'
    metadata["token_symbol"] = 'YETI'
    metadata["owners"] = ["Adam", "Niel"]       # PLACE REAL ADDRESSES HERE
    # Swap info
    metadata["swap_token"] =  "con_marmite100_contract"
    metadata["swap_end"] = now + datetime.timedelta(days=180)       # HOW MANY DAYS TO AGREE ON?
    metadata["swap_rate"] = decimal('1')
    # Wallets
    metadata["rewards_wallet"] = "rewards_wallet"   # PLACE REAL ADDRESS HERE
    metadata["LP_wallet"] = "LP_wallet"     # PLACE REAL ADDRESS HERE
    metadata["charity_wallet"] = "charity_wallet"       # PLACE REAL ADDRESS HERE
    metadata["buy_back_wallet"] = "buy_back_wallet"     # PLACE REAL ADDRESS HERE
    metadata["burn_wallet"] = "burn_wallet"     # PLACE REAL ADDRESS HERE
    metadata["blocked_wallets"] = ["1b6a98bc717d568379218ca87b2b8f67b561ee1e50049da1af8f104270816a6b"]
    # Rates
    metadata["buy_tax"] = decimal('0.05')
    metadata["sell_tax"] = decimal('0.05')
    metadata["rewards_perc"] = decimal('0.01')
    metadata["LP_perc"] = decimal('0.01')
    metadata["charity_perc"] = decimal('0.01')
    metadata["buy_back_perc"] = decimal('0.01')
    metadata["burn_perc"] = decimal('0.01')
    # DEX
    metadata["dex"] = ["con_rocketswap_official_v1_1"]


# LST002 with governance

@export
def change_metadata(key: str, value: Any):
    assert_owner()
    owners = metadata["owners"]
    caller = ctx.caller

    metadata[caller, key] = {"v":value, "time":now}
    agreed = False
    for owner in owners:
        if metadata[owner, key] is None:
            # Without this initial value, we cannot later compare the proposed value "v"
            metadata[owner, key] = {"v":"", "time":""}

        # Ensure caller's proposed value is not compared to itself   
        if owner != caller and metadata[owner, key]["v"] == metadata[caller, key]["v"] :
            metadata[key] = value
            agreed = True

    if agreed:
        for owner in owners:
            # Prevent proposed value been used again by some owner in the future
            metadata[caller, key] = hashlib.sha256(str(now))
        return f"{key} = {value}"

    return agreed


# LST001 with extra features

@export
def transfer(amount: float, to: str):
    assert amount > 0, "Cannot send negative balances!"

    sender = ctx.caller

    assert balances[sender] >= amount, "Not enough CURRENCY to send!"

    if sender in metadata["dex"]:
        tax_amount = amount * metadata["buy_tax"]
        amount_to_buyer = amount - tax_amount

        balances[sender] -= amount
        balances[to] += amount_to_buyer
        # Transfers to YETI fund wallets
        balances[metadata["rewards_wallet"]] += tax_amount * metadata["rewards_perc"]
        balances[metadata["LP_wallet"]] += tax_amount * metadata["LP_perc"]
        balances[metadata["charity_wallet"]] += tax_amount * metadata["charity_perc"]
        balances[metadata["buy_back_wallet"]] += tax_amount * metadata["buy_back_perc"]
        balances[metadata["burn_wallet"]] += tax_amount * metadata["burn_perc"]
        return
        
    balances[sender] -= amount
    balances[to] += amount

@export
def approve(amount: float, to: str):
    assert amount > 0, "Cannot send negative balances!"

    sender = ctx.caller
    balances[sender, to] += amount
    return balances[sender, to]

@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, "Cannot send negative balances!"

    sender = ctx.caller

    assert balances[main_account, sender] >= amount, f"Not enough coins approved to send! You have {balances[main_account, sender]} and are trying to spend {amount}"
    assert balances[main_account] >= amount, "Not enough coins to send!"

    if to in metadata["dex"]:
        tax_amount = amount * metadata["sell_tax"]
        amount_to_dex = amount - tax_amount

        balances[main_account, sender] -= amount
        balances[main_account] -= amount
        balances[to] += amount_to_dex
        # Transfers to YETI fund wallets
        balances[metadata["rewards_wallet"]] += tax_amount * metadata["rewards_perc"]
        balances[metadata["LP_wallet"]] += tax_amount * metadata["LP_perc"]
        balances[metadata["charity_wallet"]] += tax_amount * metadata["charity_perc"]
        balances[metadata["buy_back_wallet"]] += tax_amount * metadata["buy_back_perc"]
        balances[metadata["burn_wallet"]] += tax_amount * metadata["burn_perc"]
        return

    balances[main_account, sender] -= amount
    balances[main_account] -= amount

    balances[to] += amount

@export 
def swap_marmite(amount: float):
    caller = ctx.caller
    assert amount > 0, "Cannot send negative balances!"
    assert caller not in metadata["blocked_wallets"], "caller is a blocked wallet!"
    assert now < metadata["swap_end"], "Swap is over!"

    token_contract = metadata["swap_token"]
    swap_token = I.import_module(token_contract)

    swap_token.transfer_from(amount=amount, to=metadata["burn_wallet"], main_account=caller)
    amount_of_yeti = amount * metadata["swap_rate"] 
    balances[caller] += amount_of_yeti
    balances["sys"] -= amount_of_yeti

@export
def execute_proposal_after_a_month(key: str):
    assert_owner()
    caller = ctx.caller
    assert metadata[caller, key], "Proposal does not exist!"
    assert now > metadata[caller, key]["time"] + datetime.timedelta(weeks=4) , "Proposal must be 1 month old!"
    metadata[key] = metadata[caller, key]["v"]
    return True

def assert_owner():
    assert ctx.caller in metadata["owners"], "Only owner can call this method!"
