from time import time
from scripts.backend.strategy_fetcher import StrategyFetcher
from scripts.backend.controller_executor import ControllerExecutor
from scripts.backend.helpers import buy_frequency_enum_to_seconds_map

# EXECUTE IN PROJECT ROOT:
# brownie run scripts/backend/main.py --network arbitrum-main-fork --interactive

def main():
    bot_start_time = time()
    strategy_fetcher = StrategyFetcher()
    controller_executor = ControllerExecutor()
    all_vault_addresses=strategy_fetcher.fetch_vault_addresses()
    print("ALL VAULT ADDRESSES:", all_vault_addresses)
    all_vaults = strategy_fetcher.fetch_vaults(all_vault_addresses)
    print("ALL VAULTS:", all_vaults)
    
    print("UPDATING STRATEGY VAULTS...")
    for vault in all_vaults:
        for depositor_address in vault.depositor_addresses:
            controller_executor.trigger_strategy_action(vault.address, depositor_address)

    print("STRATEGY VAULTS UPDATED!!!!!")
