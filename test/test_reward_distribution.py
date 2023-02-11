import unittest

from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal

W_CHIEF='ec9decc889a17d4ea22afbd518f767a136f36301a0b1aa9a660f3f71d61f5b2b'
W_NIEL = '1910513066afbe592d6140c0055de3cb068fe7c17584a654a704ac7e60b2df04'


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
            
        self.yeti_rewards = self.c.get_contract('con_yeti_rewards')
       
        self.setupToken()

    def setupToken(self):
        # Approvals 
        self.currency.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.currency.approve(signer=W_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.rswp.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        self.rswp.approve(signer=W_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')

        self.lusd.approve(signer='sys', amount=999999999, to='con_rocketswap_official_v1_1')
        
        self.yeti.approve(signer=W_CHIEF, amount=999999999, to='con_rocketswap_official_v1_1')

        # TAU transfer to W_CHIEF
        self.currency.transfer(signer='sys', amount=6000000, to=W_CHIEF)

        # Create TAU-RSWP pool
        self.dex.create_market(signer='sys', contract='con_rswp_lst001', currency_amount=1000000, token_amount=1000000)

        # Create TAU-YETI pool
        self.dex.create_market(signer=W_CHIEF, contract='con_yeti_contract', currency_amount=2000000, token_amount=200000)

        # Create TAU-LUSD pool
        self.dex.create_market(signer='sys', contract='con_lusd_lst001', currency_amount=2000000, token_amount=200000)


    def test_01_other_operators_calling_reward_contract_should_fail(self):
        # transfer yeti and tau to rewards contract
        self.currency.transfer(amount=500, to='con_yeti_rewards')
        self.yeti.transfer(signer=W_CHIEF, amount=2000, to='con_yeti_rewards')

        address_list = ['chief', 'niel','dev']

        with self.assertRaises(AssertionError):
            self.yeti_rewards.distribute_rewards(signer=W_CHIEF, contract='con_lusd_lst001', addresses=address_list, 
                holder_min=50_000_000, cost_of_distr=1400, eligible_total_balance=250_000)

    def test_02_when_distr_cost_exceeds_tau_purchased_distr_fails(self):
        cost_of_distr = 105 
        self.yeti.transfer(signer=W_CHIEF, amount=10, to='con_yeti_rewards')  
        
        address_list = ['chief', 'niel','dev']
        
        with self.assertRaises(AssertionError):
            self.yeti.distribute_rewards(signer=W_CHIEF, addresses=address_list, 
                cost_of_distr=cost_of_distr, eligible_total_balance=250_000)
            print(self.currency.balances['con_yeti_rewards'])

    def test_03_distributing_reward_token_other_than_tau_works(self):
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to='con_yeti_rewards')  
        self.yeti.transfer(signer=W_CHIEF, amount=200, to='chief') 
        self.yeti.transfer(signer=W_CHIEF, amount=400, to='niel') 
        self.yeti.transfer(signer=W_CHIEF, amount=800, to='dev') 
        
        address_list = ['chief', 'niel','dev']
        
        self.yeti.distribute_rewards(signer=W_CHIEF, addresses=address_list, 
            holder_min=200, cost_of_distr=cost_of_distr, eligible_total_balance=1400)

        tau_bought = 99.69501524918922288
        tau_to_buy_lusd = tau_bought - cost_of_distr
        lusd_bought = 0.966588334799842734689347949841
        tau_left_for_distr_fee = tau_bought - tau_to_buy_lusd
        
        self.assertAlmostEqual(self.currency.balances['con_yeti_rewards'], tau_left_for_distr_fee)
        self.assertAlmostEqual(self.lusd.balances['chief'], lusd_bought*(200/1400))
        self.assertAlmostEqual(self.lusd.balances['niel'], lusd_bought*(400/1400))
        self.assertAlmostEqual(self.lusd.balances['dev'], lusd_bought*(800/1400))

    def test_04_distributing_tau_as_rewards_works(self):
        self.yeti.metadata['reward_token'] = 'currency'
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to='con_yeti_rewards')  
        self.yeti.transfer(signer=W_CHIEF, amount=200, to='chief') 
        self.yeti.transfer(signer=W_CHIEF, amount=400, to='niel') 
        self.yeti.transfer(signer=W_CHIEF, amount=800, to='dev') 
        
        address_list = ['chief', 'niel','dev']
        
        self.yeti.distribute_rewards(signer=W_CHIEF, addresses=address_list, 
            holder_min=200, cost_of_distr=cost_of_distr, eligible_total_balance=1400)

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr
        tau_left_for_distr_fee = tau_bought - tau_to_distr
        
        self.assertAlmostEqual(self.currency.balances['con_yeti_rewards'], tau_left_for_distr_fee)
        self.assertAlmostEqual(self.currency.balances['chief'], tau_to_distr*(200/1400))
        self.assertAlmostEqual(self.currency.balances['niel'], tau_to_distr*(400/1400))
        self.assertAlmostEqual(self.currency.balances['dev'], tau_to_distr*(800/1400))

    def test_05_holder_with_less_than_minimum_does_not_receive_rewards(self):
        self.yeti.metadata['reward_token'] = 'currency'
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to='con_yeti_rewards')  
        self.yeti.transfer(signer=W_CHIEF, amount=200, to='chief') 
        self.yeti.transfer(signer=W_CHIEF, amount=400, to='niel') 
        self.yeti.transfer(signer=W_CHIEF, amount=800, to='dev') 
        
        address_list = ['chief', 'niel','dev']
        
        self.yeti.distribute_rewards(signer=W_CHIEF, addresses=address_list, 
            holder_min=300, cost_of_distr=cost_of_distr, eligible_total_balance=1400)

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr
        tau_left_for_distr_fee = tau_bought - tau_to_distr

        undistr_amount = tau_to_distr*(200/1400)
        
        self.assertAlmostEqual(self.currency.balances['con_yeti_rewards'], tau_left_for_distr_fee+undistr_amount)
        self.assertIsNone(self.currency.balances['chief']) #does not get rewarded
        self.assertAlmostEqual(self.currency.balances['niel'], tau_to_distr*(400/1400))
        self.assertAlmostEqual(self.currency.balances['dev'], tau_to_distr*(800/1400))
        
        # TODO: contract part of address list

    def test_06_contracts_are_excluded_from_reward_distribution(self):
        self.yeti.metadata['reward_token'] = 'currency'
        cost_of_distr = 90
        # yeti transfers
        self.yeti.transfer(signer=W_CHIEF, amount=10, to='con_yeti_rewards')  
        self.yeti.transfer(signer=W_CHIEF, amount=200, to='con_am_contract') 
        self.yeti.transfer(signer=W_CHIEF, amount=400, to='niel') 
        self.yeti.transfer(signer=W_CHIEF, amount=800, to='dev') 
        
        address_list = ['con_am_contract', 'niel','dev']
        
        self.yeti.distribute_rewards(signer=W_CHIEF, addresses=address_list, 
            holder_min=300, cost_of_distr=cost_of_distr, eligible_total_balance=1400)

        tau_bought = 99.69501524918922288
        tau_to_distr = tau_bought - cost_of_distr
        tau_left_for_distr_fee = tau_bought - tau_to_distr

        undistr_amount = tau_to_distr*(200/1400)
        
        self.assertAlmostEqual(self.currency.balances['con_yeti_rewards'], tau_left_for_distr_fee+undistr_amount)
        self.assertIsNone(self.currency.balances['con_am_contract']) #does not get rewarded
        self.assertAlmostEqual(self.currency.balances['niel'], tau_to_distr*(400/1400))
        self.assertAlmostEqual(self.currency.balances['dev'], tau_to_distr*(800/1400))          

if __name__ == "__main__":
    unittest.main()