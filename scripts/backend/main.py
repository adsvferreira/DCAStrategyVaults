from scripts.backend.strategy_fetcher import StrategyFetcher

# EXECUTE IN PROJECT ROOT:
# brownie run scripts/backend/main.py --network arbitrum-main-fork --interactive

def main():
    strategy_fetcher = StrategyFetcher()
    all_vault_addresses=strategy_fetcher.fetch_vault_addresses()
    print("ALL VAULT ADDRESSES:", all_vault_addresses)
    print()
    all_vaults = strategy_fetcher.fetch_vaults(all_vault_addresses)
    print("ALL VAULTS:", all_vaults)
