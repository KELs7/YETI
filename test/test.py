import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal


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

        with open('dex.py') as f:
            dex = f.read()
            self.c.submit(dex, name='con_rocketswap_official_v1_1')

        self.dex = self.c.get_contract('con_rocketswap_official_v1_1')

        with open('../con_yeti_rewards.py') as f:
            code = f.read()
            self.c.submit(code, name='con_yeti_rewards')
            
        self.con_yeti_rewards = self.c.get_contract('currency')
       
        self.setupToken()

    def setupToken(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
        # Approvals
        blacklisted_wallets = self.yeti.metadata['blacklisted_wallets'][0]
        self.currency.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.currency.approve(signer=WALLET_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        self.currency.approve(signer='kels', amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.rswp.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.rswp.approve(signer=WALLET_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.yeti.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.yeti.approve(signer=WALLET_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        self.yeti.approve(signer='kels', amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.marmite.approve(signer=WALLET_NIEL, amount=999999999, to='con_yeti_contract')
        self.marmite.approve(signer=blacklisted_wallets, amount=999999999, to='con_yeti_contract')
        self.marmite.approve(signer='kels', amount=999999999, to='con_yeti_contract')
        self.lusd.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')

        # TAU, YETi, and MARMITE transfers to WALLET_CHIEF
        self.currency.transfer(signer='sys', amount=6000000, to=WALLET_CHIEF)
        self.currency.transfer(signer='sys', amount=60000, to='kels')
        self.marmite.transfer(signer='sys', amount=1000000, to=WALLET_NIEL)
        self.marmite.transfer(signer='sys', amount=1000000, to=blacklisted_wallets)
        self.marmite.transfer(signer='sys', amount=1000000, to='kels')
        self.yeti.transfer(signer=WALLET_CHIEF, amount=60000, to='kels')

        # Create TAU-RSWP pool
        self.dex.create_market(signer='sys', contract='con_rswp_lst001', currency_amount=1000000, token_amount=1000000)
        
        # Create TAU-YETI pool
        self.dex.create_market(signer=WALLET_CHIEF, contract='con_yeti_contract', currency_amount=2000000, token_amount=200000)

        # Create TAU-LUSD pool
        self.dex.create_market(signer='sys', contract='con_lusd_lst001', currency_amount=2000000, token_amount=200000)


    def tearDown(self):
        self.c.flush()
    
    def test_01_transfering_to_user_attracts_no_tax(self):
        WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
        self.yeti.transfer(signer='kels', amount=300, to='benji')
        balance_of_benji = 300

        self.assertEqual(self.yeti.balances['benji'], balance_of_benji)
    
    def test_02_buying_yeti_attracts_tax(self):
        WALLET_YETI_LP = 'a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca'
        WALLET_YETI_RAIN = 'e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73'
        WALLET_YETI_MARKETING = '3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9'
        WALLET_YETI_CHARITY = '4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94'
        WALLET_YETI_BUYBACK = 'b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc'

        buy_tax = ContractingDecimal('0.02') #2%
        marketing_perc = ContractingDecimal('0.5') #50% of tax
        rewards_perc = ContractingDecimal('0.1') #10% of tax
        LP_perc = ContractingDecimal('0.35') #35% of tax
        rain_perc = ContractingDecimal('0.05') #5% of tax
        charity_perc = ContractingDecimal('0.00') #0% of tax
        buyback_perc = ContractingDecimal('0.00') #0% of tax
        burn_perc = ContractingDecimal('0.00') #0% of tax

        token_amount_purchased = self.dex.buy(signer='kels', contract='con_yeti_contract', \
            currency_amount=1000, minimum_received=0, token_fees=False)

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
        
        self.assertEqual(self.yeti.balances[WALLET_YETI_MARKETING], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_yeti_rewards'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(buy_tax, calculated_buy_tax)

    def test_03_owner_buying_yeti_attracts_no_tax(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_YETI_LP = 'a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca'
        WALLET_YETI_RAIN = 'e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73'
        WALLET_YETI_MARKETING = '3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9'
        WALLET_YETI_CHARITY = '4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94'
        WALLET_YETI_BUYBACK = 'b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc'

        self.dex.buy(signer=WALLET_CHIEF, contract='con_yeti_contract', 
            currency_amount=1000, minimum_received=0, token_fees=False)
        
        self.assertIsNone(self.yeti.balances[WALLET_YETI_MARKETING]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_yeti_rewards'])
        self.assertIsNone(self.yeti.balances[WALLET_YETI_LP])
        self.assertIsNone(self.yeti.balances[WALLET_YETI_RAIN])
       
    def test_04_selling_yeti_attracts_tax(self):
        WALLET_YETI_LP = 'a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca'
        WALLET_YETI_RAIN = 'e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73'
        WALLET_YETI_MARKETING = '3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9'
        WALLET_YETI_CHARITY = '4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94'
        WALLET_YETI_BUYBACK = 'b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc'
        
        sell_tax = ContractingDecimal('0.05') #2%
        marketing_perc = ContractingDecimal('0.5') #50% of tax
        rewards_perc = ContractingDecimal('0.1') #10% of tax
        LP_perc = ContractingDecimal('0.35') #35% of tax
        rain_perc = ContractingDecimal('0.05') #5% of tax
        charity_perc = ContractingDecimal('0.00') #0% of tax
        buyback_perc = ContractingDecimal('0.00') #0% of tax
        burn_perc = ContractingDecimal('0.00') #0% of tax
        
        self.dex.sell(signer='kels', contract='con_yeti_contract', token_amount=1000, minimum_received=0, \
            token_fees=False)
        
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
        
        self.assertEqual(self.yeti.balances[WALLET_YETI_MARKETING], amount_credited_to_marketing_fund)
        self.assertEqual(self.yeti.balances['con_yeti_rewards'], amount_credited_to_rewards_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_LP], amount_credited_to_LP_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_RAIN], amount_credited_to_rain_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_CHARITY], amount_credited_to_charity_fund)
        self.assertEqual(self.yeti.balances[WALLET_YETI_BUYBACK], amount_credited_to_buyback_fund)
        self.assertEqual(self.yeti.balances['yeti_burn_wallet'], amount_credited_to_burn_wallet)
        self.assertEqual(sell_tax, calculated_sell_tax)
        
    def test_05_owner_selling_yeti_attracts_no_tax(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_YETI_LP = 'a690e68d8a049ea7c8ad4e16b166e321bd5ebc0dba4dc10d2ea01bf6eed84cca'
        WALLET_YETI_RAIN = 'e8dc708028e049397b5baf9579924dde58ce5bebee5655da0b53066117572e73'
        WALLET_YETI_MARKETING = '3466e7576d1b70aef675ee4149b0d83cf21f69f4cfade801249d5afaad7c7ac9'
        WALLET_YETI_CHARITY = '4c66b7ba687222d44df2c3c989ae4cc50185abfcee8ea5356afcc5344c4a5f94'
        WALLET_YETI_BUYBACK = 'b22e0df3949428211989867c4e4febd851af3c1c044a8d892e8a07b7034e94dc'
        
        self.dex.sell(signer=WALLET_CHIEF, contract='con_yeti_contract', 
            token_amount=1000, minimum_received=0, token_fees=False)

        self.assertIsNone(self.yeti.balances[WALLET_YETI_MARKETING]) #in local testing default initial value is None
        self.assertIsNone(self.yeti.balances['con_yeti_rewards'])
        self.assertIsNone(self.yeti.balances[WALLET_YETI_LP])
        self.assertIsNone(self.yeti.balances[WALLET_YETI_RAIN])
        self.assertIsNone(self.yeti.balances[WALLET_YETI_CHARITY])
        self.assertIsNone(self.yeti.balances[WALLET_YETI_BUYBACK])
        self.assertIsNone(self.yeti.balances['yeti_burn_wallet'])
 
    def test_06_swapping_marmite_should_pass(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}

        swap_rate = ContractingDecimal('1')
        balance_of_kels_yeti = self.yeti.balances['kels']
        supply_yeti = self.yeti.balances[WALLET_CHIEF]
        supply_after_swap_yeti =  supply_yeti - 400

        self.yeti.swap_token(environment=env_0, signer='kels', amount=400)

        yeti_swap_amount = 400 * swap_rate
        self.assertEqual(self.marmite.balances['yeti_burn_wallet'], yeti_swap_amount)
        self.assertEqual(self.yeti.balances['kels'], balance_of_kels_yeti+yeti_swap_amount)
        self.assertEqual(self.yeti.balances[WALLET_CHIEF], supply_after_swap_yeti)

    def test_07_swapping_marmite_amount_bigger_than_supply_should_fail(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}
        
        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer='kels', amount=100_000_000_000)

    def test_08_blacklisted_wallets_swapping_marmite_should_fail(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
        
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}

        blacklisted_wallet = self.yeti.metadata['blacklisted_wallets'][0]

        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer=blacklisted_wallet, amount=400)

        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer=WALLET_CHIEF, amount=400)

        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer=WALLET_NIEL, amount=400)

    def test_09_contract_swapping_marmite_should_fail(self):
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}


        with self.assertRaises(AssertionError):
            self.yeti.swap_token(environment=env_0, signer='con_some_contract', amount=400)
    
    def test_10_2_out_of_n_governance_should_pass(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
        reward_token_before_governance = 'con_lusd_lst001'

        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_before_governance)

        agreement_state_1 = self.yeti.change_metadata(signer=WALLET_CHIEF, key='reward_token', value='con_weth_lst001')   
        agreement_state_2 = self.yeti.change_metadata(signer=WALLET_NIEL, key='reward_token', value='con_weth_lst001')

        reward_token_after_governance = 'con_weth_lst001'
        
        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_after_governance)
        self.assertFalse(agreement_state_1)
        self.assertEqual('reward_token = con_weth_lst001', agreement_state_2)

        # second act of governance

        reward_token_before_2nd_governance = reward_token_after_governance

        agreement_state_3 = self.yeti.change_metadata(signer=WALLET_NIEL, key='reward_token', value='con_lusd_lst001')   
        agreement_state_4 = self.yeti.change_metadata(signer=WALLET_CHIEF, key='reward_token', value='con_lusd_lst001')

        reward_token_after_2nd_governance = 'con_lusd_lst001'
        
        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_after_2nd_governance)
        self.assertFalse(agreement_state_3)
        self.assertEqual('reward_token = con_lusd_lst001', agreement_state_4)
    
    def test_11_a_proposal_without_confirmation_should_fail(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
        reward_token_before_governance = 'con_lusd_lst001'

        agreement_state = self.yeti.change_metadata(signer=WALLET_NIEL, key='reward_token', value='con_weth_lst001')

        reward_token_after_governance = self.yeti.metadata['reward_token']
        
        self.assertEqual(reward_token_before_governance, reward_token_after_governance)
        self.assertFalse(agreement_state)

    def test_12_executing_proposal_after_1_month_when_there_is_no_confirmatio_should_pass(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        WALLET_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}
        reward_token_before_governance = 'con_lusd_lst001'

        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_before_governance)

        env_1 = {'now': Datetime(year=2023, month=1, day=16)}

        self.yeti.change_metadata(environment=env_0, signer=WALLET_CHIEF, key='reward_token', value='con_weth_lst001')
        self.yeti.execute_proposal_after_a_month(environment=env_1, signer=WALLET_CHIEF, key='reward_token')

        reward_token_after_governance = 'con_weth_lst001'
        
        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_after_governance)

    def test_13_executing_proposal_before_1_month_when_there_is_no_confirmation_should_fail(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        env_0 = {'now': Datetime(year=2022, month=12, day=16)}
        reward_token_before_governance = 'con_lusd_lst001'

        self.assertEqual(self.yeti.metadata['reward_token'], reward_token_before_governance)

        env_1 = {'now': Datetime(year=2023, month=1, day=5)}

        self.yeti.change_metadata(environment=env_0, signer=WALLET_CHIEF, key='reward_token', value='con_weth_lst001')

        with self.assertRaises(AssertionError):
            self.yeti.execute_proposal_after_a_month(environment=env_1, \
                signer=WALLET_CHIEF, key='reward_token')
   
    def test_14_distributing_rewards_should_pass(self):
        WALLET_CHIEF = 'ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
        reward_token = 'con_lusd_lst001'
        address_list = ['me','greedyme', 'stillgreedy']

        #assigned balances
        self.yeti.balances['me'] = 600_000_000
        self.yeti.balances['greedyme'] = 700_000_000
        self.yeti.balances['stillgreedy'] = 800_000_000
        self.yeti.balances['con_yeti_rewards'] = 5000 #assigned value for taxes

        me_yeti = self.yeti.balances['me']
        greedyme_yeti = self.yeti.balances['greedyme']
        stillgreedy_yeti = self.yeti.balances['stillgreedy']
        con_yeti_rewards_bal = self.yeti.balances['con_yeti_rewards']

        #get reserves for reward token purchase calculation
        currency_reserve, token_reserve = self.dex.reserves[reward_token]
        k = currency_reserve * token_reserve

        #distribute reward tokens
        self.yeti.distribute_rewards(signer=WALLET_CHIEF,
            addresses=address_list)    
        
        #percentage deducted before buying reward token 
        fee_cover_tau = self.currency.balances['con_yeti_rewards']
        #amount of TAU from YETI sell
        amount_tau = fee_cover_tau * 20 # 5% * 20 = 100%
        #amount of TAU actually used to buy reward token
        amount_tau -= fee_cover_tau

        new_currency_reserve = currency_reserve + amount_tau
        new_token_reserve = k / new_currency_reserve
        tokens_purchased = token_reserve - new_token_reserve
        
        fee = tokens_purchased * ContractingDecimal('0.003')
        tokens_purchased -= fee
        
        #holder ratios
        m = (me_yeti/100_000_000_000)
        g = (greedyme_yeti/100_000_000_000)
        s = (stillgreedy_yeti/100_000_000_000)
        
        me_reward_lusd = tokens_purchased * ContractingDecimal(f'{m}')
        greedyme_reward_lusd = tokens_purchased * ContractingDecimal(f'{g}')
        stillgreedy_reward_lusd = tokens_purchased * ContractingDecimal(f'{s}')
        
        self.assertEqual(me_reward_lusd, self.lusd.balances['me'])
        self.assertEqual(greedyme_reward_lusd, self.lusd.balances['greedyme'])
        self.assertEqual(stillgreedy_reward_lusd, self.lusd.balances['stillgreedy'])
        
        
if __name__ == "__main__":
    unittest.main()

