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

        self.dex = self.c.get_contract('con_rocketswap_official_v1_1')
       
        self.setupToken()

    def setupToken(self):
        # Approvals
        blacklisted_wallets = self.yeti.metadata['blacklisted_wallets'][0]
        self.currency.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.currency.approve(signer=W_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        self.currency.approve(signer='kels', amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.rswp.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.rswp.approve(signer=W_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.yeti.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.yeti.approve(signer=W_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        self.yeti.approve(signer='kels', amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.marmite.approve(signer=W_NIEL, amount=999999999, to='con_yeti_contract')
        self.marmite.approve(signer=blacklisted_wallets, amount=999999999, to='con_yeti_contract')
        self.marmite.approve(signer='kels', amount=999999999, to='con_yeti_contract')
        self.lusd.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')

        # TAU, YETi, and MARMITE transfers to W_CHIEF
        self.currency.transfer(signer='sys', amount=6_000_000, to=W_CHIEF)
        self.currency.transfer(signer='sys', amount=20_000_000, to='kels')
        self.marmite.transfer(signer='sys', amount=1_000_000, to=W_NIEL)
        self.marmite.transfer(signer='sys', amount=1_000_000, to=blacklisted_wallets)
        self.marmite.transfer(signer='sys', amount=1_000_000, to='kels')
        self.yeti.transfer(signer=W_CHIEF, amount=600_000, to='kels')

        # Create TAU-RSWP pool
        self.dex.create_market(signer='sys', contract='con_rswp_lst001', currency_amount=1000000, token_amount=1000000)
        
        # Create TAU-YETI pool
        self.dex.create_market(signer=W_CHIEF, contract='con_yeti_contract', currency_amount=2000000, token_amount=200000)

        # Create TAU-LUSD pool
        self.dex.create_market(signer='sys', contract='con_lusd_lst001', currency_amount=2000000, token_amount=200000)


    def tearDown(self):
        self.c.flush()
    
    def test_01_transfering_to_user_attracts_no_tax(self):
        self.yeti.transfer(signer='kels', amount=300, to='benji')
       
        self.assertEqual(self.yeti.balances['benji'], 300)

    def test_02_other_contracts_should_fail_calling_transfer_contract(self):
        owners = [W_CHIEF, W_NIEL]
        dex = 'con_rocketswap_official_v1_1'
        with self.assertRaises(AssertionError):
            self.yeti_transfer.transfer(signer='con_yeti_lst001', ctx_signer=W_CHIEF, contract=dex, 
                contract_method='buy', amount=1000, owners=owners, tax_amount=10)

    def test_03_user_removing_liq_is_not_taxed(self):
        balance_kels_yeti_1 = self.yeti.balances['kels']

        self.dex.add_liquidity(signer='kels', contract='con_yeti_contract', currency_amount=100_000)

        balance_kels_yeti_2 = self.yeti.balances['kels']
        amount_yeti_added_to_liq = balance_kels_yeti_1 - balance_kels_yeti_2
        
        self.dex.remove_liquidity(signer='kels', contract='con_yeti_contract', amount=5)
        amount_yeti_liq_removed = self.yeti.balances['kels'] - balance_kels_yeti_2
        
        self.assertAlmostEqual(amount_yeti_added_to_liq, amount_yeti_liq_removed)
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])
        

    def test_04_owner_removing_liq_is_not_taxed(self):
        balance_chief_yeti_1 = self.yeti.balances[W_CHIEF]

        self.dex.add_liquidity(signer=W_CHIEF, contract='con_yeti_contract', currency_amount=100_000)

        balance_chief_yeti_2 = self.yeti.balances[W_CHIEF]
        amount_yeti_added_to_liq = balance_chief_yeti_1 - balance_chief_yeti_2
        
        self.dex.remove_liquidity(signer=W_CHIEF, contract='con_yeti_contract', amount=5)
        amount_yeti_liq_removed = self.yeti.balances[W_CHIEF] - balance_chief_yeti_2

        self.assertAlmostEqual(amount_yeti_added_to_liq, amount_yeti_liq_removed)
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])
        
    
    def test_05_user_buying_yeti_attracts_tax(self):
        balance_kels_yeti = self.yeti.balances['kels']

        token_amount_purchased = self.dex.buy(signer='kels', contract='con_yeti_contract', currency_amount=1000)

        tax_amount = token_amount_purchased * buy_tax
        amount_credited_to_marketing_fund = tax_amount * marketing_perc
        amount_credited_to_rewards_fund = tax_amount * rewards_perc
        amount_credited_to_LP_fund = tax_amount * LP_perc
        amount_credited_to_rain_fund = tax_amount * rain_perc
        amount_credited_to_charity_fund = tax_amount * charity_perc
        amount_credited_to_buyback_fund = tax_amount * buyback_perc
        amount_credited_to_burn_wallet = tax_amount * burn_perc

        total_credited_to_yeti_fund = amount_credited_to_marketing_fund + \
            amount_credited_to_rewards_fund + amount_credited_to_LP_fund + \
            amount_credited_to_rain_fund

        calculated_buy_tax = total_credited_to_yeti_fund / token_amount_purchased

        balance_kels_yeti_current = balance_kels_yeti + token_amount_purchased - tax_amount
        
        self.assertEqual(self.yeti.balances['kels'], balance_kels_yeti_current)
        self.assertEqual(self.yeti.balances[W_MARKETN], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_distr_rewards_yeti'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[W_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[W_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[W_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[W_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(buy_tax, calculated_buy_tax)

    def test_06_owner_buying_yeti_attracts_no_tax(self):
        balance_chief_yeti = self.yeti.balances[W_CHIEF]

        token_amount_purchased = self.dex.buy(signer=W_CHIEF, contract='con_yeti_contract', currency_amount=1000)

        balance_chief_yeti_current = balance_chief_yeti + token_amount_purchased 
        
        self.assertEqual(self.yeti.balances[W_CHIEF], balance_chief_yeti_current)
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    # USING PAYING TAX ON TOP OF SOLD AMOUNT

    def test_07_spending_from_other_contracts_works(self):
        balance_chief = self.yeti.balances[W_CHIEF]
        self.yeti.approve(signer=W_CHIEF, amount=100, to='qt')
        self.yeti.transfer_from(signer='qt', amount=100, to='qt', main_account=W_CHIEF)

        self.assertEqual(self.yeti.balances[W_CHIEF], balance_chief - 100)
        self.assertEqual(self.yeti.balances['qt'], 100)
        self.assertEqual(self.yeti.balances[W_CHIEF,'qt'], 0) #Approval

    def test_08_other_contracts_should_fail_calling_transfer_from_contract(self):
        dex = 'con_rocketswap_official_v1_1'
        with self.assertRaises(AssertionError):
            self.yeti_transfer_from_1.transfer_from(signer='con_yeti_lst001', caller=dex, contract=dex, 
                contract_method='sell', amount=1000, to=dex, main_account='kels', tax_amount=10)

    def test_09_owner_created_yeti_market_was_not_taxed(self):
        # YETI market was created in setupToken()
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    def test_10_owner_adding_liq_is_not_taxed(self):
        balance_chief_yeti_1 = self.yeti.balances[W_CHIEF]
        balance_dex_yeti_1 = self.yeti.balances['con_rocketswap_official_v1_1']

        self.dex.add_liquidity(signer=W_CHIEF, contract='con_yeti_contract', currency_amount=100)

        balance_chief_yeti_2 = self.yeti.balances[W_CHIEF]
        balance_dex_yeti_2 = self.yeti.balances['con_rocketswap_official_v1_1']

        amount_yeti_added_to_liq = balance_chief_yeti_1 - balance_chief_yeti_2
        amount_received_dex_yeti = balance_dex_yeti_2 - balance_dex_yeti_1

        self.assertEqual(amount_yeti_added_to_liq, amount_received_dex_yeti)
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    def test_11_user_adding_liq_is_not_taxed(self):
        balance_kels_yeti_1 = self.yeti.balances['kels']
        balance_dex_yeti_1 = self.yeti.balances['con_rocketswap_official_v1_1']

        self.dex.add_liquidity(signer='kels', contract='con_yeti_contract', currency_amount=100)

        balance_kels_yeti_2 = self.yeti.balances['kels']
        balance_dex_yeti_2 = self.yeti.balances['con_rocketswap_official_v1_1']

        amount_yeti_added_to_liq = balance_kels_yeti_1 - balance_kels_yeti_2
        amount_received_dex_yeti = balance_dex_yeti_2 - balance_dex_yeti_1

        self.assertEqual(amount_yeti_added_to_liq, amount_received_dex_yeti)
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    def test_12_not_enough_YETI_to_pay_for_tax_(self):
        with self.assertRaises(AssertionError):
            self.dex.sell(signer='kels', contract='con_yeti_contract', token_amount=600_000)

    def test_13_user_selling_yeti_attracts_tax(self):
        balance_kels_yeti = self.yeti.balances['kels']
        balance_dex_yeti = self.yeti.balances['con_rocketswap_official_v1_1']

        self.dex.sell(signer='kels', contract='con_yeti_contract', token_amount=1000, 
            minimum_received=0, token_fees=False)
        
        tax_amount = 1000 * sell_tax
        amount_credited_to_marketing_fund = tax_amount * marketing_perc
        amount_credited_to_rewards_fund = tax_amount * rewards_perc
        amount_credited_to_LP_fund = tax_amount * LP_perc
        amount_credited_to_rain_fund = tax_amount * rain_perc
        amount_credited_to_charity_fund = tax_amount * charity_perc
        amount_credited_to_buyback_fund = tax_amount * buyback_perc
        amount_credited_to_burn_wallet = tax_amount * burn_perc

        total_credited_to_yeti_fund = amount_credited_to_marketing_fund + \
        amount_credited_to_rewards_fund + amount_credited_to_LP_fund + \
        amount_credited_to_rain_fund

        calculated_sell_tax = total_credited_to_yeti_fund / 1000

        balance_kels_yeti_current = balance_kels_yeti - 1000 - tax_amount

        self.assertEqual(self.yeti.balances['kels'], balance_kels_yeti_current)
        self.assertEqual(self.yeti.balances['con_rocketswap_official_v1_1'], balance_dex_yeti+1000)
        self.assertEqual(self.yeti.balances[W_MARKETN], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_distr_rewards_yeti'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[W_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[W_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[W_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[W_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(sell_tax, calculated_sell_tax)
        
    def test_14_owner_selling_yeti_attracts_tax(self):
        balance_chief_yeti = self.yeti.balances[W_CHIEF]
        balance_dex_yeti = self.yeti.balances['con_rocketswap_official_v1_1']

        self.dex.sell(signer=W_CHIEF, contract='con_yeti_contract', 
            token_amount=1000, minimum_received=0, token_fees=False)

        tax_amount = 1000 * sell_tax
        amount_credited_to_marketing_fund = tax_amount * marketing_perc
        amount_credited_to_rewards_fund = tax_amount * rewards_perc
        amount_credited_to_LP_fund = tax_amount * LP_perc
        amount_credited_to_rain_fund = tax_amount * rain_perc
        amount_credited_to_charity_fund = tax_amount * charity_perc
        amount_credited_to_buyback_fund = tax_amount * buyback_perc
        amount_credited_to_burn_wallet = tax_amount * burn_perc

        total_credited_to_yeti_fund = amount_credited_to_marketing_fund + \
        amount_credited_to_rewards_fund + amount_credited_to_LP_fund + \
        amount_credited_to_rain_fund

        calculated_sell_tax = total_credited_to_yeti_fund / 1000

        balance_chief_yeti_current = balance_chief_yeti - 1000 - tax_amount

        self.assertEqual(self.yeti.balances[W_CHIEF], balance_chief_yeti_current)
        self.assertEqual(self.yeti.balances['con_rocketswap_official_v1_1'], balance_dex_yeti+1000)
        self.assertEqual(self.yeti.balances[W_MARKETN], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_distr_rewards_yeti'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[W_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[W_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[W_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[W_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(sell_tax, calculated_sell_tax)
    
    # USING DEDUCTING TAX FROM AMOUNT SOLD

    def test_15_spending_from_other_contracts_works_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        balance_chief = self.yeti.balances[W_CHIEF]
        
        self.yeti.approve(signer=W_CHIEF, amount=100, to='qt')
        self.yeti.transfer_from(signer='qt', amount=100, to='qt', main_account=W_CHIEF)

        self.assertEqual(self.yeti.balances[W_CHIEF], balance_chief - 100)
        self.assertEqual(self.yeti.balances['qt'], 100)
        self.assertEqual(self.yeti.balances[W_CHIEF,'qt'], 0) #Approval

    def test_16_other_contracts_should_fail_calling_transfer_from_contract_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        dex = 'con_rocketswap_official_v1_1'
        with self.assertRaises(AssertionError):
            self.yeti_transfer_from_1.transfer_from(signer='con_yeti_lst001', caller=dex, contract=dex, 
                contract_method='sell', amount=1000, to=dex, main_account='kels', tax_amount=10)

    def test_17_owner_created_yeti_market_was_not_taxed_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        # YETI market was created in setupToken()
        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    def test_18_owner_adding_liq_is_not_taxed_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        self.dex.add_liquidity(signer=W_CHIEF, contract='con_yeti_contract', currency_amount=100)

        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    def test_19_user_adding_liq_is_not_taxed_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        self.dex.add_liquidity(signer='kels', contract='con_yeti_contract', currency_amount=100)

        self.assertIsNone(self.yeti.balances[W_MARKETN]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_distr_rewards_yeti'])
        self.assertIsNone(self.yeti.balances[W_LP])
        self.assertIsNone(self.yeti.balances[W_RAIN])
        self.assertIsNone(self.yeti.balances[W_CHARITY])
        self.assertIsNone(self.yeti.balances[W_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])

    def test_20_tax_is_deducted_from_sold_amount(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'
        # print(self.yeti.balances['con_rocketswap_official_v1_1'])
        tax = 600_000*sell_tax
        amount_received_by_dex = 600_000 - tax

        balance_dex_yeti = self.yeti.balances['con_rocketswap_official_v1_1']
        self.dex.sell(signer='kels', contract='con_yeti_contract', token_amount=600_000)

        self.assertEqual(self.yeti.balances['kels'], 0)
        self.assertEqual(self.yeti.balances['con_rocketswap_official_v1_1'], balance_dex_yeti+amount_received_by_dex)

    def test_21_user_selling_yeti_attracts_tax_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        balance_kels_yeti = self.yeti.balances['kels']
        balance_dex_yeti = self.yeti.balances['con_rocketswap_official_v1_1']

        self.dex.sell(signer='kels', contract='con_yeti_contract', token_amount=1000)
        
        tax_amount = 1000 * sell_tax
        amount_credited_to_marketing_fund = tax_amount * marketing_perc
        amount_credited_to_rewards_fund = tax_amount * rewards_perc
        amount_credited_to_LP_fund = tax_amount * LP_perc
        amount_credited_to_rain_fund = tax_amount * rain_perc
        amount_credited_to_charity_fund = tax_amount * charity_perc
        amount_credited_to_buyback_fund = tax_amount * buyback_perc
        amount_credited_to_burn_wallet = tax_amount * burn_perc

        total_credited_to_yeti_fund = amount_credited_to_marketing_fund + \
        amount_credited_to_rewards_fund + amount_credited_to_LP_fund + \
        amount_credited_to_rain_fund

        calculated_sell_tax = total_credited_to_yeti_fund / 1000

        balance_kels_yeti_current = balance_kels_yeti - 1000 
        
        self.assertEqual(self.yeti.balances['kels'], balance_kels_yeti_current)
        self.assertEqual(self.yeti.balances['con_rocketswap_official_v1_1'], balance_dex_yeti+1000-tax_amount)
        self.assertEqual(self.yeti.balances[W_MARKETN], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_distr_rewards_yeti'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[W_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[W_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[W_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[W_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(sell_tax, calculated_sell_tax)

    def test_22_owner_selling_yeti_attracts_2(self):
        self.yeti.metadata['transfer_from_contract'] = 'con_yeti_transfer_from_2'

        balance_chief_yeti = self.yeti.balances[W_CHIEF]
        balance_dex_yeti = self.yeti.balances['con_rocketswap_official_v1_1']

        self.dex.sell(signer=W_CHIEF, contract='con_yeti_contract', 
            token_amount=1000)

        tax_amount = 1000 * sell_tax
        amount_credited_to_marketing_fund = tax_amount * marketing_perc
        amount_credited_to_rewards_fund = tax_amount * rewards_perc
        amount_credited_to_LP_fund = tax_amount * LP_perc
        amount_credited_to_rain_fund = tax_amount * rain_perc
        amount_credited_to_charity_fund = tax_amount * charity_perc
        amount_credited_to_buyback_fund = tax_amount * buyback_perc
        amount_credited_to_burn_wallet = tax_amount * burn_perc

        total_credited_to_yeti_fund = amount_credited_to_marketing_fund + \
        amount_credited_to_rewards_fund + amount_credited_to_LP_fund + \
        amount_credited_to_rain_fund

        calculated_sell_tax = total_credited_to_yeti_fund / 1000

        balance_chief_yeti_current = balance_chief_yeti - 1000 
        
        self.assertEqual(self.yeti.balances[W_CHIEF], balance_chief_yeti_current)
        self.assertEqual(self.yeti.balances['con_rocketswap_official_v1_1'], balance_dex_yeti+1000-tax_amount)
        self.assertEqual(self.yeti.balances[W_MARKETN], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_distr_rewards_yeti'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[W_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[W_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[W_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[W_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(sell_tax, calculated_sell_tax)

    def test_23_swapping_marmite_should_pass(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}

        swap_rate = ContractingDecimal('1')
        balance_of_kels_yeti = self.yeti.balances['kels']
        supply_yeti = self.yeti.balances[W_CHIEF]
        supply_after_swap_yeti =  supply_yeti - 400

        self.yeti.swap_token(environment=env_0, signer='kels', amount=400)

        yeti_swap_amount = 400 * swap_rate
        self.assertEqual(self.marmite.balances['yeti_burn_wallet'], yeti_swap_amount)
        self.assertEqual(self.yeti.balances['kels'], balance_of_kels_yeti+yeti_swap_amount)
        self.assertEqual(self.yeti.balances[W_CHIEF], supply_after_swap_yeti)

    def test_24_swapping_marmite_amount_bigger_than_supply_should_fail(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}
        
        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer='kels', amount=100_000_000_000)

    def test_25_blacklisted_wallets_swapping_marmite_should_fail(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}

        blacklisted_wallet = self.yeti.metadata['blacklisted_wallets'][0]

        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer=blacklisted_wallet, amount=400)

        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer=W_CHIEF, amount=400)

        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer=W_CHARITY, amount=400)

    def test_26_contract_swapping_marmite_should_fail(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}


        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer='con_some_contract', amount=400)
    
    def test_27_2_out_of_n_governance_should_pass(self):
        reward_token_before_governance = 'con_lusd_lst001'

        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_before_governance)

        agreement_state_1 = self.yeti.change_metadata(signer=W_CHIEF, key='reward_token', value='con_weth_lst001')   
        agreement_state_2 = self.yeti.change_metadata(signer=W_NIEL, key='reward_token', value='con_weth_lst001')

        reward_token_after_governance = 'con_weth_lst001'
        
        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_after_governance)
        self.assertFalse(agreement_state_1)
        self.assertEqual('reward_token = con_weth_lst001', agreement_state_2)

        # second act of governance
        reward_token_before_2nd_governance = reward_token_after_governance

        agreement_state_3 = self.yeti.change_metadata(signer=W_NIEL, key='reward_token', value='con_lusd_lst001')   
        agreement_state_4 = self.yeti.change_metadata(signer=W_CHIEF, key='reward_token', value='con_lusd_lst001')

        reward_token_after_2nd_governance = 'con_lusd_lst001'
        
        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_after_2nd_governance)
        self.assertFalse(agreement_state_3)
        self.assertEqual('reward_token = con_lusd_lst001', agreement_state_4)
    
    def test_28_a_proposal_without_approving_should_fail(self):
        reward_token_before_governance = 'con_lusd_lst001'

        agreement_state = self.yeti.change_metadata(signer=W_NIEL, key='reward_token', value='con_weth_lst001')

        reward_token_after_governance = self.yeti.metadata['reward_token']
        
        self.assertEqual(reward_token_before_governance, reward_token_after_governance)
        self.assertFalse(agreement_state)

    def test_29_executing_proposal_after_1_month_without_approval_should_pass(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}
        reward_token_before_governance = 'con_lusd_lst001'

        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_before_governance)

        env_1 = {'now': Datetime(year=2023, month=1, day=16)}

        self.yeti.change_metadata(environment=env_0, signer=W_CHIEF, key='reward_token', value='con_weth_lst001')
        self.yeti.execute_proposal_after_a_month(environment=env_1, signer=W_CHIEF, key='reward_token')

        reward_token_after_governance = 'con_weth_lst001'
        
        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_after_governance)

    def test_30_executing_proposal_before_1_month_without_approval_should_fail(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}
        reward_token_before_governance = 'con_lusd_lst001'

        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_before_governance)

        env_1 = {'now': Datetime(year=2023, month=1, day=5)}

        self.yeti.change_metadata(environment=env_0, signer=W_CHIEF, key='reward_token', value='con_weth_lst001')

        with self.assertRaises(AssertionError):
            self.yeti.execute_proposal_after_a_month(environment=env_1, \
                signer=W_CHIEF, key='reward_token')    
        
if __name__ == "__main__":
    unittest.main()

