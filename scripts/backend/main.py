import time
from scripts.backend.strategy_fetcher import StrategyFetcher
from scripts.backend.controller_executor import ControllerExecutor
from scripts.backend.helpers import CONSOLE_SEPARATOR, buy_frequency_enum_to_seconds_map

# EXECUTE IN PROJECT ROOT:
# brownie run scripts/backend/main.py --network arbitrum-main-fork --interactive


def main():
    strategy_fetcher = StrategyFetcher()
    controller_executor = ControllerExecutor()
    all_vault_addresses = strategy_fetcher.fetch_vault_addresses()
    print("ALL VAULT ADDRESSES:", all_vault_addresses)
    all_vaults = strategy_fetcher.fetch_vaults(all_vault_addresses)
    print()
    print("ALL VAULTS:")
    print(all_vaults)
    print(CONSOLE_SEPARATOR)
    
    # # filtered vaults because of reverted transactions
    # all_vaults = [vault for vault in all_vaults if vault.address != "0xCaDf5ba5AB9Cb2f6206d98D7Ae45157D79B66A0A"]
    print("UPDATING STRATEGY VAULTS...")
    for vault in all_vaults:
        for depositor_address in vault.depositor_addresses:
            try:
                tx = controller_executor.trigger_strategy_action(vault.address, depositor_address)
                print(f"WALLET: {depositor_address} BALANCES SWAPPED AND SENT TO DESTINATION WALLET")
            except Exception:
                print(f"TRANSACTION FAILED FOR WALLET: {depositor_address}")
            print("VAULT DETAILS:")
            print(vault)
            print()
            if tx:
                tx.wait(1)
    print("STRATEGY VAULTS FIRST UPDATE CONCLUDED!")
    time.sleep(buy_frequency_enum_to_seconds_map[0])

    print("STARTING SCHEDULER...")
    
    while True:
        print("STARTING NEW ITERATION...")
        current_time = time.time()
        print(f"Current Time: {current_time}")

        print("UPDATING STRATEGY VAULTS...")
        for vault in all_vaults:
            # Check if the difference between current time and last update time is greater than or equal to the interval
            print(f"Vault {vault.address} last updated timestamp: {vault.last_update_timestamp}")
            if current_time - vault.last_update_timestamp >= vault.buy_frequency_timestamp:
                for depositor_address in vault.depositor_addresses:
                    try:
                        tx = controller_executor.trigger_strategy_action(vault.address, depositor_address)
                        print(f"WALLET: {depositor_address} BALANCES SWAPPED AND SENT TO DESTINATION WALLET")
                    except Exception:
                        print(f"TRANSACTION FAILED FOR WALLET: {depositor_address}")
                    if tx:
                        tx.wait(1)
                print("VAULT DETAILS:")
                print(vault)
                print()
        print("STRATEGY VAULTS UPDATED OF WHILE TRUE!!!!!")
        time.sleep(buy_frequency_enum_to_seconds_map[0])
        print("ENDING SLEEP TIME...")
