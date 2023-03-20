import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal

W_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
W_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
W_LP = 'a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca'
W_RAIN = 'e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73'
W_MARKETN = '3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9'
W_BUYBACK = 'b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc'
W_CHARITY = '4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94'

buy_tax = ContractingDecimal('0.02') #2%
sell_tax = ContractingDecimal('0.05') #5%
marketing_perc = ContractingDecimal('0.5') #50% of tax
rewards_perc = ContractingDecimal('0.1') #10% of tax
LP_perc = ContractingDecimal('0.35') #35% of tax
rain_perc = ContractingDecimal('0.05') #5% of tax
charity_perc = ContractingDecimal('0.00') #0% of tax
buyback_perc = ContractingDecimal('0.00') #0% of tax
burn_perc = ContractingDecimal('0.00') #0% of tax

class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open('basic-token.py') as f:
            code = f.read()
            self.c.submit(code, name='currency', constructor_args={'vk': 'sys'})
            self.c.submit(code, name='con_rswp_lst001', constructor_args={'vk': 'sys'}) 
            self.c.submit(code, name='con_marmite100_contract', constructor_args={'vk': 'sys'})  
            self.c.submit(code, name='con_lusd_lst001', constructor_args={'vk': 'sys'})

        self.currency = self.c.get_contract('currency')
        self.rswp = self.c.get_contract('con_rswp_lst001')
        self.marmite = self.c.get_contract('con_marmite100_contract')
        self.lusd = self.c.get_contract('con_lusd_lst001')

        with open('../con_yeti.py') as f:
            code = f.read()
            self.c.submit(code, name='con_yeti_contract')

        self.yeti = self.c.get_contract('con_yeti_contract')

        with open('../con_transfer.py') as f:
            code = f.read()
            self.c.submit(code, name='con_yeti_transfer')

        self.yeti_transfer = self.c.get_contract('con_yeti_transfer')

        with open('../con_transfer_from_1.py') as f:
            code = f.read()
            self.c.submit(code, name='con_yeti_transfer_from_1')

        self.yeti_transfer_from_1 = self.c.get_contract('con_yeti_transfer_from_1')

        with open('../con_transfer_from_2.py') as f:
            code = f.read()
            self.c.submit(code, name='con_yeti_transfer_from_2')

        self.yeti_transfer_from_2 = self.c.get_contract('con_yeti_transfer_from_2')

        with open('dex.py') as f:
            dex = f.read()
            self.c.submit(dex, name='con_rocketswap_official_v1_1')

    def test_01_rates_sums_to_1(self):
        rates = {
            "marketing%": ContractingDecimal("0"),
            "LP%": ContractingDecimal("0.222"),
            "rewards%": ContractingDecimal("0.667"),
            "rain%": ContractingDecimal("0.111"),
            "charity%": ContractingDecimal("0"),
            "buyback%": ContractingDecimal("0"),
            "burn%": ContractingDecimal("0")   
        }
        
        self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates) 

    def test_02_rates_sum_is_less_than_1(self):
        rates = {
            "marketing%": ContractingDecimal("0.4"),
            "LP%": ContractingDecimal("0.3"),
            "rewards%": ContractingDecimal("0.1"),
            "rain%": ContractingDecimal("0.04"),
            "charity%": ContractingDecimal("0.1"),
            "buyback%": ContractingDecimal("0.05"),
            "burn%": ContractingDecimal("0.00")   
        }
        with self.assertRaises(AssertionError):
            self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates)

    def test_03_rates_sum_is_above_1(self):
        rates = {
            "marketing%": ContractingDecimal("0.4"),
            "LP%": ContractingDecimal("0.3"),
            "rewards%": ContractingDecimal("0.1"),
            "rain%": ContractingDecimal("0.05"),
            "charity%": ContractingDecimal("0.1"),
            "buyback%": ContractingDecimal("0.05"),
            "burn%": ContractingDecimal("0.01")   
        }
        with self.assertRaises(AssertionError):
            self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates)

    def test_04_order_of_keys_does_not_matter(self):
        rates = {
            "burn%": ContractingDecimal("0.01"),
            "LP%": ContractingDecimal("0.3"),
            "buyback%": ContractingDecimal("0.05"),
            "rewards%": ContractingDecimal("0.1"),
            "charity%": ContractingDecimal("0.1"),
            "marketing%": ContractingDecimal("0.4"),
            "rain%": ContractingDecimal("0.04"),    
        }
        self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates)

    def test_05_missing_key_fails(self):
        rates = {
            "marketing%": ContractingDecimal("0.4"),
            "LP%": ContractingDecimal("0.3"),
            "rewards%": ContractingDecimal("0.1"),
            "rain%": ContractingDecimal("0.04"),
            "buyback%": ContractingDecimal("0.05"),
            "burn%": ContractingDecimal("0.01")   
        }
        with self.assertRaises(AssertionError):
            self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates)

    def test_06_misspelled_key_fails(self):
        rates = {
            "marketing%": ContractingDecimal("0.4"),
            "LP%": ContractingDecimal("0.3"),
            "rewards": ContractingDecimal("0.1"),
            "rain%": ContractingDecimal("0.04"),
            "charity%": ContractingDecimal("0.1"),
            "buyback%": ContractingDecimal("0.05"),
            "burn%": ContractingDecimal("0.01")   
        }   
        with self.assertRaises(AssertionError):
            self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates)

    # def test_07_non_ContractingDecimal_value_fails(self):
    #     rates = {
    #         "marketing%": ContractingDecimal("0.4"),
    #         "LP%": 0.3,
    #         "rewards%": ContractingDecimal("0.1"),
    #         "rain%": ContractingDecimal("0.04"),
    #         "charity%": ContractingDecimal("0.1"),
    #         "buyback%": ContractingDecimal("0.05"),
    #         "burn%": ContractingDecimal("0.01")   
    #     }  
    #     with self.assertRaises(AssertionError):
    #         self.yeti.change_metadata(signer=W_CHIEF, key='distr_rates', value=rates)

if __name__ == "__main__":
    unittest.main()