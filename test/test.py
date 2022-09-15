import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open("basic-token.py") as f:
            code = f.read()
            self.c.submit(code, name="currency", constructor_args={"vk": "sys"})
            self.c.submit(code, name="con_rswp_lst001", constructor_args={"vk": "sys"}) 
            self.c.submit(code, name="con_marmite100_contract", constructor_args={"vk": "sys"})  

        self.currency = self.c.get_contract("currency")
        self.rswp = self.c.get_contract("con_rswp_lst001")
        self.marmite = self.c.get_contract("con_marmite100_contract")

        with open("../con_yeti.py") as f:
            code = f.read()
            self.c.submit(code, name="con_yeti")

        self.yeti = self.c.get_contract("con_yeti")

        with open("dex.py") as f:
            dex = f.read()
            self.c.submit(dex, name="con_rocketswap_official_v1_1")

        self.dex = self.c.get_contract("con_rocketswap_official_v1_1")
        
        self.setupToken()

    def setupToken(self):
        # approvals
        blocked_wallet = self.yeti.metadata["blocked_wallets"][0]
        self.currency.approve(signer="sys", amount=999999999, to="con_rocketswap_official_v1_1")
        self.currency.approve(signer="Adam", amount=999999999, to="con_rocketswap_official_v1_1")
        self.rswp.approve(signer="sys", amount=999999999, to="con_rocketswap_official_v1_1")
        self.rswp.approve(signer="Adam", amount=999999999, to="con_rocketswap_official_v1_1")
        self.yeti.approve(signer="sys", amount=999999999, to="con_rocketswap_official_v1_1")
        self.yeti.approve(signer="Adam", amount=999999999, to="con_rocketswap_official_v1_1")
        self.marmite.approve(signer="Niel", amount=999999999, to="con_yeti")
        self.marmite.approve(signer=blocked_wallet, amount=999999999, to="con_yeti")

        # TAU, YETi, and MARMITE transfers to Adam
        self.currency.transfer(signer="sys", amount=1000000, to="Adam")
        self.yeti.transfer(signer="sys", amount=1000000, to="Adam")
        self.marmite.transfer(signer="sys", amount=1000000, to="Niel")
        self.marmite.transfer(signer="sys", amount=1000000, to=blocked_wallet)

        # create TAU-RSWP pool
        self.dex.create_market(signer="sys", contract="con_rswp_lst001", currency_amount=1000000, token_amount=1000000)
        
        # create TAU-YETi pool
        self.dex.create_market(signer="sys", contract="con_yeti", currency_amount=2000000, token_amount=200000)

    def tearDown(self):
        self.c.flush()
    
    def test_01_transfering_to_user_attracts_no_tax(self):
        self.yeti.transfer(signer="Adam", amount=300, to="Niel")
        balance_of_niel = 300

        self.assertEqual(self.yeti.balances["Niel"], balance_of_niel)
    
    def test_02_buying_yeti_attracts_tax(self):
        amount_purchased = self.dex.buy(signer="Adam", contract="con_yeti", currency_amount=1000, minimum_received=0, token_fees=False)
        
        amount_credited_to_yeti_fund_when_market_was_created = 100
        tax_amount = amount_purchased * ContractingDecimal("0.05")
        amount_credited_to_yeti_fund = tax_amount * ContractingDecimal("0.01")
        amount_credited_to_yeti_fund += amount_credited_to_yeti_fund_when_market_was_created

        self.assertEqual(self.yeti.balances["rewards_wallet"], amount_credited_to_yeti_fund)
        self.assertEqual(self.yeti.balances["LP_wallet"], amount_credited_to_yeti_fund)
        self.assertEqual(self.yeti.balances["charity_wallet"], amount_credited_to_yeti_fund)
        self.assertEqual(self.yeti.balances["buy_back_wallet"], amount_credited_to_yeti_fund)
        self.assertEqual(self.yeti.balances["burn_wallet"], amount_credited_to_yeti_fund)
       
    def test_03_selling_yeti_attracts_tax(self):
        self.dex.sell(signer="Adam", contract="con_yeti", token_amount=1000, minimum_received=0, token_fees=False)
        
        amount_credited_to_yeti_fund_when_market_was_created = 100
        tax_amount = 1000 * ContractingDecimal("0.05")
        amount_to_dex = tax_amount * ContractingDecimal("0.01")
        amount_to_dex += amount_credited_to_yeti_fund_when_market_was_created
    
        self.assertEqual(self.yeti.balances["rewards_wallet"], amount_to_dex)
        self.assertEqual(self.yeti.balances["LP_wallet"], amount_to_dex)
        self.assertEqual(self.yeti.balances["charity_wallet"], amount_to_dex)
        self.assertEqual(self.yeti.balances["buy_back_wallet"], amount_to_dex)
        self.assertEqual(self.yeti.balances["burn_wallet"], amount_to_dex)
    
    def test_04_swapping_marmite_should_pass(self):
        env_0 = {"now": Datetime(year=2022, month=12, day=16)}

        supply_after_swap = self.yeti.balances["sys"] - 400

        self.yeti.swap_marmite(environment=env_0, signer="Niel", amount=400)

        balance_of_niel = 400

        self.assertEqual(self.marmite.balances["burn_wallet"], balance_of_niel)
        self.assertEqual(self.yeti.balances["Niel"], balance_of_niel)
        self.assertEqual(self.yeti.balances["sys"], supply_after_swap)

    def test_05_blocked_wallet_swapping_marmite_should_fail(self):
        env_0 = {"now": Datetime(year=2022, month=12, day=16)}

        blocked_wallet = self.yeti.metadata["blocked_wallets"][0]

        with self.assertRaises(AssertionError):
            self.yeti.swap_marmite(environment=env_0, signer=blocked_wallet, amount=400)
    
    def test_06_2_out_of_n_governance_should_pass(self):
        burn_wallet_before_governance = "burn_wallet"

        self.assertEqual(self.yeti.metadata["burn_wallet"], burn_wallet_before_governance)

        agreement_state_1 = self.yeti.change_metadata(signer="Adam", key="burn_wallet", value="xxxburnxxx")
        agreement_state_2 = self.yeti.change_metadata(signer="Niel", key="burn_wallet", value="xxxburnxxx")

        burn_wallet_after_governance = "xxxburnxxx"
        
        self.assertEqual(self.yeti.metadata["burn_wallet"], burn_wallet_after_governance)
        self.assertFalse(agreement_state_1)
        self.assertEqual("burn_wallet = xxxburnxxx", agreement_state_2)
    
    def test_07_a_proposal_without_a_second_confirmation_should_fail(self):
        burn_wallet_before_governance = "burn_wallet"

        agreement_state = self.yeti.change_metadata(signer="Niel", key="burn_wallet", value="xxxburnxxx")

        burn_wallet_after_governance = self.yeti.metadata["burn_wallet"]
        
        self.assertEqual(burn_wallet_before_governance, burn_wallet_after_governance)
        self.assertFalse(agreement_state)

    def test_08_can_execute_proposal_after_1_month_when_confirms_not_met(self):
        env_0 = {"now": Datetime(year=2022, month=12, day=16)}
        burn_wallet_before_governance = "burn_wallet"

        self.assertEqual(self.yeti.metadata["burn_wallet"], burn_wallet_before_governance)

        env_1 = {"now": Datetime(year=2023, month=1, day=16)}

        self.yeti.change_metadata(environment=env_0, signer="Adam", key="burn_wallet", value="xxxburnxxx")
        self.yeti.execute_proposal_after_a_month(environment=env_1, signer="Adam", key="burn_wallet")

        burn_wallet_after_governance = "xxxburnxxx"
        
        self.assertEqual(self.yeti.metadata["burn_wallet"], burn_wallet_after_governance)
        #self.assertFalse(agreement_state)
      
        

if __name__ == "__main__":
    unittest.main()

