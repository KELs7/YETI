import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal

W_CHIEF = "ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b"
W_NIEL = "1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04"


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open("basic-token.py") as f:
            code = f.read()
            self.c.submit(code, name="currency", constructor_args={"vk": "sys"})
            self.c.submit(code, name="con_rswp_lst001", constructor_args={"vk": "sys"})
            self.c.submit(
                code, name="con_marmite100_contract", constructor_args={"vk": "sys"}
            )
            self.c.submit(code, name="con_lusd_lst001", constructor_args={"vk": "sys"})

        self.currency = self.c.get_contract("currency")
        self.rswp = self.c.get_contract("con_rswp_lst001")
        self.marmite = self.c.get_contract("con_marmite100_contract")
        self.lusd = self.c.get_contract("con_lusd_lst001")

        with open("../con_yeti.py") as f:
            code = f.read()
            self.c.submit(code, name="con_yeti_contract")

        self.yeti = self.c.get_contract("con_yeti_contract")

        with open("dex.py") as f:
            dex = f.read()
            self.c.submit(dex, name="con_rocketswap_official_v1_1")

        self.dex = self.c.get_contract("con_rocketswap_official_v1_1")

        with open("../con_transfer_from_1.py") as f:
            code = f.read()
            self.c.submit(code, name="con_yeti_transfer_from_1")

        self.yeti_transfer_from_1 = self.c.get_contract("con_yeti_transfer_from_1")

        with open("../con_transfer_from_2.py") as f:
            code = f.read()
            self.c.submit(code, name="con_yeti_transfer_from_2")

        # self.yeti_transfer_from_2 = self.c.get_contract('con_yeti_transfer_from_2')

        with open("../con_distr_rewards_yeti.py") as f:
            code = f.read()
            self.c.submit(code, name="con_distr_rewards_yeti")

        self.yeti_rewards = self.c.get_contract("con_distr_rewards_yeti")

        self.setupToken()

    def setupToken(self):
        # Approvals
        self.currency.approve(
            signer="sys", amount=999999999, to="con_rocketswap_official_v1_1"
        )
        self.currency.approve(
            signer=W_CHIEF, amount=999999999, to="con_rocketswap_official_v1_1"
        )

        self.rswp.approve(
            signer="sys", amount=999999999, to="con_rocketswap_official_v1_1"
        )
        self.rswp.approve(
            signer=W_CHIEF, amount=999999999, to="con_rocketswap_official_v1_1"
        )

        self.lusd.approve(
            signer="sys", amount=999999999, to="con_rocketswap_official_v1_1"
        )

        self.yeti.approve(
            signer=W_CHIEF, amount=999999999, to="con_rocketswap_official_v1_1"
        )

        # TAU transfer to W_CHIEF
        self.currency.transfer(signer="sys", amount=6000000, to=W_CHIEF)

        # Create TAU-RSWP pool
        self.dex.create_market(
            signer="sys",
            contract="con_rswp_lst001",
            currency_amount=1000000,
            token_amount=1000000,
        )

        # Create TAU-YETI pool
        self.dex.create_market(
            signer=W_CHIEF,
            contract="con_yeti_contract",
            currency_amount=2000000,
            token_amount=200000,
        )

        # Create TAU-LUSD pool
        self.dex.create_market(
            signer="sys",
            contract="con_lusd_lst001",
            currency_amount=2000000,
            token_amount=200000,
        )

    def test_01_other_operators_calling_reward_contract_should_fail(self):
        # transfer yeti and tau to rewards contract
        self.currency.transfer(amount=500, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=2000, to="con_distr_rewards_yeti")

        address_list = ["chief", "niel", "dev"]
        amount_list = [10000, 20000, 30000]

        with self.assertRaises(AssertionError):
            self.yeti_rewards.sell_yeti_for_rewards(cost_of_distr=1000)

        with self.assertRaises(AssertionError):
            self.yeti_rewards.distribute_rewards(
                signer=W_CHIEF,
                reward_token="con_lusd_lst001",
                addresses=address_list,
                amounts=amount_list,
            )

    def test_02_when_distr_cost_exceeds_tau_purchased_distr_fails(self):
        cost_of_distr = 105
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")

        address_list = ["chief", "niel", "dev"]
        amount_list = [10000, 20000, 30000]

        with self.assertRaises(AssertionError):
            self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)
            self.yeti.distribute_rewards(
                signer=W_CHIEF, addresses=address_list, amounts=amount_list
            )

    def test_03_distributing_reward_token_other_than_tau_works(self):
        cost_of_distr = 90
        self.yeti.metadata["reward_token"] = "con_lusd_lst001"
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="chief")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        tau_bought = 99.69501524918922288
        tau_to_buy_lusd = tau_bought - cost_of_distr
        lusd_bought = 0.966588334799842734689347949841

        address_list = ["chief", "niel", "dev"]
        amount_list = [
            lusd_bought * (199.99999999 / 1400),
            lusd_bought * (399.99999999 / 1400),
            lusd_bought * (799.99999999 / 1400),
        ]

        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)

        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        self.assertAlmostEqual(self.lusd.balances["chief"], lusd_bought * (200 / 1400))
        self.assertAlmostEqual(self.lusd.balances["niel"], lusd_bought * (400 / 1400))
        self.assertAlmostEqual(self.lusd.balances["dev"], lusd_bought * (800 / 1400))

    def test_04_distributing_tau_as_rewards_works(self):
        self.yeti.metadata["reward_token"] = "currency"
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="chief")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr

        address_list = ["chief", "niel", "dev"]
        amount_list = [
            tau_to_distr * (199.99999999 / 1400),
            tau_to_distr * (399.99999999 / 1400),
            tau_to_distr * (799.99999999 / 1400),
        ]

        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)

        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        # self.assertAlmostEqual(self.currency.balances['con_distr_rewards_yeti'], cost_of_distr)
        self.assertAlmostEqual(
            self.currency.balances["chief"], tau_to_distr * (200 / 1400)
        )
        self.assertAlmostEqual(
            self.currency.balances["niel"], tau_to_distr * (400 / 1400)
        )
        self.assertAlmostEqual(
            self.currency.balances["dev"], tau_to_distr * (800 / 1400)
        )

    def test_05_signer_is_payed_distr_cost_when_distr_tau(self):
        self.yeti.metadata["reward_token"] = "currency"
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="chief")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr

        address_list = ["chief", "niel", "dev"]
        amount_list = [
            tau_to_distr * (199.99999999 / 1400),
            tau_to_distr * (399.99999999 / 1400),
            tau_to_distr * (799.99999999 / 1400),
        ]

        balance_chief_tau = self.currency.balances[W_CHIEF]

        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)

        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        self.assertAlmostEqual(self.currency.balances["con_distr_rewards_yeti"], 0)
        self.assertEqual(
            self.currency.balances[W_CHIEF], balance_chief_tau + cost_of_distr
        )

    def test_06_signer_is_payed_distr_cost_when_distr_other_tokens(self):
        cost_of_distr = 90
        self.yeti.metadata["reward_token"] = "con_lusd_lst001"
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="chief")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        lusd_bought = 0.966588334799842734689347949841

        address_list = ["chief", "niel", "dev"]
        amount_list = [
            lusd_bought * (199.99999999 / 1400),
            lusd_bought * (399.99999999 / 1400),
            lusd_bought * (799.99999999 / 1400),
        ]

        balance_chief_tau = self.currency.balances[W_CHIEF]
        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)
        
        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        self.assertAlmostEqual(self.currency.balances["con_distr_rewards_yeti"], 0)
        self.assertEqual(
            self.currency.balances[W_CHIEF], balance_chief_tau + cost_of_distr
        )

    def test_07_contracts_are_excluded_from_reward_distribution(self):
        self.yeti.metadata["reward_token"] = "currency"
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="con_am_contract")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr

        address_list = ["con_am_contract", "niel", "dev"]
        amount_list = [
            tau_to_distr * (199.99999999 / 1400),
            tau_to_distr * (399.99999999 / 1400),
            tau_to_distr * (799.99999999 / 1400),
        ]

        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)

        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        undistr_amount = tau_to_distr * (199.99999999 / 1400)

        self.assertIsNone(
            self.currency.balances["con_am_contract"]
        )  # does not get rewarded
        self.assertAlmostEqual(
            self.currency.balances["niel"], tau_to_distr * (399.99999999 / 1400)
        )
        self.assertAlmostEqual(
            self.currency.balances["dev"], tau_to_distr * (799.99999999 / 1400)
        )

    # # USING DEDUCTING TAX FROM AMOUNT SOLD
    def test_08_distributing_reward_token_other_than_tau_works_2(self):
        self.yeti.metadata["transfer_from_contract"] = "con_yeti_transfer_from_2"
        self.yeti.metadata["reward_token"] = "con_lusd_lst001"
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="chief")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        tau_bought = 99.69501524918922288
        tau_to_buy_lusd = tau_bought - cost_of_distr
        lusd_bought = 0.966588334799842734689347949841

        address_list = ["chief", "niel", "dev"]
        amount_list = [
            lusd_bought * (199.99999999 / 1400),
            lusd_bought * (399.99999999 / 1400),
            lusd_bought * (799.99999999 / 1400),
        ]

        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)

        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        self.assertAlmostEqual(self.lusd.balances["chief"], lusd_bought * (200 / 1400))
        self.assertAlmostEqual(self.lusd.balances["niel"], lusd_bought * (400 / 1400))
        self.assertAlmostEqual(self.lusd.balances["dev"], lusd_bought * (800 / 1400))

    def test_09_distributing_tau_as_rewards_works_2(self):
        self.yeti.metadata["transfer_from_contract"] = "con_yeti_transfer_from_2"

        self.yeti.metadata["reward_token"] = "currency"
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to="con_distr_rewards_yeti")
        self.yeti.transfer(signer=W_CHIEF, amount=200, to="chief")
        self.yeti.transfer(signer=W_CHIEF, amount=400, to="niel")
        self.yeti.transfer(signer=W_CHIEF, amount=800, to="dev")

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr

        address_list = ["chief", "niel", "dev"]
        amount_list = [
            tau_to_distr * (199.99999999 / 1400),
            tau_to_distr * (399.99999999 / 1400),
            tau_to_distr * (799.99999999 / 1400),
        ]

        self.yeti.sell_yeti_for_rewards(signer=W_CHIEF, cost_of_distr=cost_of_distr)

        self.yeti.distribute_rewards(
            signer=W_CHIEF, addresses=address_list, amounts=amount_list
        )

        self.assertAlmostEqual(
            self.currency.balances["chief"], tau_to_distr * (200 / 1400)
        )
        self.assertAlmostEqual(
            self.currency.balances["niel"], tau_to_distr * (400 / 1400)
        )
        self.assertAlmostEqual(
            self.currency.balances["dev"], tau_to_distr * (800 / 1400)
        )


if __name__ == "__main__":
    unittest.main()
