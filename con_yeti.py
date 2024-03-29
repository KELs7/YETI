I = importlib

balances = Hash(default_value=0)
metadata = Hash()

W_CHIEF = "ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b"
W_NIEL = "b26f61e036e0c54951efb64a106f46aaae60571b29b1914a2c72d966d0b04d26"
W_LP = "a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca"
W_RAIN = "e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73"
W_MARKETN = "3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9"
W_CHARITY = "4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94"
W_BUYBACK = "b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc"


@construct
def init():
    # Token info
    balances[W_CHIEF] = 105_000_000_000
    balances[W_NIEL] = 5_000_000_000
    metadata["token_name"] = "YETI"
    metadata["token_symbol"] = "$YETI"
    metadata["owners"] = [W_CHIEF, W_NIEL]
    # Swap info
    metadata["swap_token"] = "con_marmite100_contract"
    metadata["swap_end"] = now + datetime.timedelta(
        days=180
    )  # HOW MANY DAYS TO AGREE ON? 6 MONTHS?
    metadata["swap_rate"] = decimal("1")
    # Wallets
    metadata["rewards_contract"] = "con_distr_rewards_yeti"
    metadata["LP_wallet"] = W_LP
    metadata["rain_wallet"] = W_RAIN
    metadata["marketing_wallet"] = W_MARKETN
    metadata["charity_wallet"] = W_CHARITY
    metadata["buyback_wallet"] = W_BUYBACK
    metadata["burn_wallet"] = "yeti_burn_wallet"

    metadata["blacklisted_wallets"] = [
        "1b6a98bc717d568379218ca87b2b8f67b561ee1e50049da1af8f104270816a6b",
        W_CHIEF,
        W_LP,
        W_RAIN,
        W_MARKETN,
        W_CHARITY,
        W_BUYBACK,
    ]

    # Rates
    metadata["buy_tax"] = decimal("0.09")  # 9%
    metadata["sell_tax"] = decimal("0.09")  # 9%
    metadata["distr_rates"] = {
        "marketing%": decimal("0"),
        "LP%": decimal("0.222"),
        "rewards%": decimal("0.667"),
        "rain%": decimal("0.111"),
        "charity%": decimal("0"),
        "buyback%": decimal("0"),
        "burn%": decimal("0")   
    }
    # DEX
    metadata["dex"] = ["con_rocketswap_official_v1_1"]
    # Reward token
    metadata["reward_token"] = "currency"

    metadata["bridge"] = ["con_lamden_link_bsc_v1", "con_lamden_link_weth_v1"]

    metadata["transfer_contract"] = "con_yeti_transfer"
    metadata["transfer_from_contract"] = "con_yeti_transfer_from_1"
    metadata["sell_function"] = "sell"
    metadata["buy_function"] = "buy"


# governance


@export
def change_metadata(key: str, value: Any):
    assert_owner()
    owners = metadata["owners"]
    caller = ctx.caller

    if key == "distr_rates":
        validate_distr_rates(value=value)

    metadata[caller, key] = {"v": value, "time": now}
    agreed = False
    for owner in owners:
        if metadata[owner, key] is None:
            # Without this initial value, we cannot later compare the proposed value "v"
            metadata[owner, key] = {"v": "", "time": ""}

        # Ensure caller's proposed value is not compared to itself
        if owner != caller and metadata[owner, key]["v"] == metadata[caller, key]["v"]:
            metadata[key] = value
            agreed = True

    if agreed:
        for owner in owners:
            # Prevent proposed value been used again by some owner in the future
            metadata[caller, key] = str(now)
        return f"{key} = {value}"

    return agreed


@export
def mint(amount: float, to: str):
    assert ctx.caller in metadata["bridge"], "Only bridge can mint!"
    assert amount > 0, "Cannot mint negative balances!"
    balances[to] += amount


@export
def transfer(amount: float, to: str):
    assert amount > 0, "Cannot send negative balances!"

    signer = ctx.signer
    caller = ctx.caller
    contract_name, contract_method = ctx.entry

    assert balances[caller] >= amount, "Not enough YETI to send!"

    if contract_name in metadata["dex"]:
        tax_amount = amount * metadata["buy_tax"]

        transfer = I.import_module(metadata["transfer_contract"])
        amount_2 = transfer.transfer(ctx_signer=signer,contract=
            contract_name, contract_method=contract_method,amount=amount,
            owners=metadata["owners"], tax_amount=tax_amount)

        balances[caller] -= amount
        balances[to] += amount_2

        if signer not in metadata["owners"
            ] and contract_method == metadata["buy_function"]:
            # Transfers to YETI fund wallets
            balances[metadata["marketing_wallet"]
                ] += tax_amount * metadata["distr_rates"]["marketing%"]
            balances[metadata["LP_wallet"]] += tax_amount * metadata["distr_rates"]["LP%"]
            balances[metadata["rewards_contract"]] += tax_amount * metadata["distr_rates"]["rewards%"]
            balances[metadata["rain_wallet"]] += tax_amount * metadata["distr_rates"]["rain%"]
            balances[metadata["charity_wallet"]] += tax_amount * metadata["distr_rates"]["charity%"]
            balances[metadata["buyback_wallet"]] += tax_amount * metadata["distr_rates"]["buyback%"]
            balances[metadata["burn_wallet"]] += tax_amount * metadata["distr_rates"]["burn%"]
    else:
        balances[caller] -= amount
        balances[to] += amount


@export
def approve(amount: float, to: str):
    assert amount > 0, "Cannot send negative balances!"

    caller = ctx.caller
    balances[caller, to] += amount
    return balances[caller, to]


@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, "Cannot send negative balances!"

    caller = ctx.caller
    contract_name, contract_method = ctx.entry

    if contract_name in metadata["dex"]:
        tax_amount = amount * metadata["sell_tax"]

        transfer_from = I.import_module(metadata["transfer_from_contract"])
        amount_2 = transfer_from.transfer_from(caller=caller,contract=
            contract_name, contract_method=contract_method, amount=amount,
            to=caller, main_account=main_account, tax_amount=tax_amount)

        balances[main_account, caller] -= amount

        balances[main_account] -= amount
        balances[to] += amount_2

        if contract_method == metadata["sell_function"]:
            if amount == amount_2:
                balances[main_account, caller] -= tax_amount
                balances[main_account] -= tax_amount
            # Transfers to YETI fund wallets
            balances[metadata["marketing_wallet"]
                ] += tax_amount * metadata["distr_rates"]["marketing%"]
            balances[metadata["LP_wallet"]] += tax_amount * metadata["distr_rates"]["LP%"]
            balances[metadata["rewards_contract"]] += tax_amount * metadata["distr_rates"]["rewards%"]
            balances[metadata["rain_wallet"]] += tax_amount * metadata["distr_rates"]["rain%"]
            balances[metadata["charity_wallet"]] += tax_amount * metadata["distr_rates"]["charity%"]
            balances[metadata["buyback_wallet"]] += tax_amount * metadata["distr_rates"]["buyback%"]
            balances[metadata["burn_wallet"]] += tax_amount * metadata["distr_rates"]["burn%"]
    else:
        assert balances[main_account, caller
            ] >= amount, f"Not enough coins approved to send! You have {balances[main_account, caller]} and are trying to spend {amount}"
        assert balances[main_account] >= amount, "Not enough coins to send!"

        balances[main_account, caller] -= amount

        balances[main_account] -= amount
        balances[to] += amount


@export
def swap_token(amount: float):
    caller = ctx.caller
    assert amount > 0, "Cannot send negative balances!"
    assert caller not in metadata["blacklisted_wallets"], "This wallet is blacklisted"
    assert not caller.startswith("con_"), "Caller is a contract!"
    assert balances[W_CHIEF
        ] > amount, f"Token amount left is {balances[W_CHIEF]} and you are trying to swap for {amount}"
    assert now < metadata["swap_end"], "Swap is over!"

    contract = metadata["swap_token"]
    swap_token = I.import_module(contract)

    swap_token.transfer_from(amount=amount, to=metadata["burn_wallet"],
        main_account=caller)
    amount_of_yeti = amount * metadata["swap_rate"]
    balances[caller] += amount_of_yeti
    balances[W_CHIEF] -= amount_of_yeti


@export
def execute_proposal_after_a_month(key: str):
    assert_owner()
    caller = ctx.caller
    assert metadata[caller, key], "Proposal does not exist!"
    assert now > metadata[caller, key]["time"] + datetime.timedelta(weeks=4
        ), "Proposal must be 1 month old!"
    metadata[key] = metadata[caller, key]["v"]
    return True


@export
def sell_yeti_for_rewards(cost_of_distr: float):
    assert_owner()
    rewards_contract = I.import_module(metadata["rewards_contract"])
    rewards_contract.sell_yeti_for_rewards(cost_of_distr=cost_of_distr,
     reward_token=metadata["reward_token"])


@export
def distribute_rewards(addresses: list, amounts: list):
    assert_owner()
    rewards_contract = I.import_module(metadata["rewards_contract"])
    rewards_contract.distribute_rewards(reward_token=metadata[
        "reward_token"], addresses=addresses, amounts=amounts)


def validate_distr_rates(value: Any):
    r = {"marketing%", "LP%", "rewards%", "rain%", "charity%", "buyback%", "burn%"}
    s , t = set(), 0
    for rk in list(value.keys()):
        s.add(rk)
    assert s == r, "Key missing or mispelled!"
    for k, v in value.items():
        t += v
    assert t == 1, "Ratios do not sum to 1!"

def assert_owner():
    assert ctx.caller in metadata["owners"
        ], "Only owner can call this method!"
