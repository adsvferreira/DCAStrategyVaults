from brownie import accounts, config, network
from brownie import AutomatedVaultsFactory, TreasuryVault, StrategyWorker, Controller

CONSOLE_SEPARATOR = "--------------------------------------------------------------------------"

def main():
    #NETWORK
    print(CONSOLE_SEPARATOR)
    print("CURRENT NETWORK: ",network.show_active())
    print(CONSOLE_SEPARATOR)
    dev_wallet = accounts.add(config["wallets"]["from_key_1"])
    print(f"WALLET USED FOR DEPLOYMENT: {dev_wallet.address}")
    dex_router_address = config["networks"][network.show_active()]["dex_router_address"]
    verify_flag  = config["networks"][network.show_active()]["verify"]
    
    # SETUP
    treasury_fixed_fee_on_vault_creation =  1_000_000_000_000_000 #0.01 ETH
    creator_percentage_fee_on_deposit = 25 #0.25%
    treasury_percentage_fee_on_balance_update = 25 #0.25%

    print(CONSOLE_SEPARATOR)
    print("TREASURY VAULT DEPLOYMENT:")
    tx1 = TreasuryVault.deploy({'from': dev_wallet}, publish_source=verify_flag)
    treasury_vault = TreasuryVault[-1]
    treasury_address = treasury_vault.address
    
    print(CONSOLE_SEPARATOR)
    print("CONTROLLER DEPLOYMENT:")
    tx2 = Controller.deploy({'from': dev_wallet}, publish_source=verify_flag)
    controller = Controller[-1]
    controller_address = controller.address 
    
    print(CONSOLE_SEPARATOR)
    print("STRATEGY WORKER DEPLOYMENT:")
    tx3 = StrategyWorker.deploy(dex_router_address, controller_address, {'from': dev_wallet}, publish_source=verify_flag)
    strategy_worker = StrategyWorker[-1]

    print(CONSOLE_SEPARATOR)
    print("STRATEGY VAULTS FACTORY DEPLOYMENT:")
    tx4=AutomatedVaultsFactory.deploy(treasury_address,treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update, {'from': dev_wallet}, publish_source=verify_flag)