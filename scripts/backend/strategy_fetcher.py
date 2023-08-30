from brownie import Contract, accounts, config
from scripts.backend.dataclasses import StrategyVault

BACKEND_BOT_WALLET = accounts.add(config["wallets"]["from_key_1"])
factory_address = "0x5d2ffdb504ea97c191deeeda364832b1cc72246f"
vaults_factory = Contract.from_explorer(factory_address)

# dataclass Vault

class StrategyFetcher:

    def fetch_vault_addresses() -> list[str]:
        number_of_vaults = vaults_factory.allVaultsLength()
        return [vaults_factory.allVaults(i) for i in range(number_of_vaults)]


    def fetch_vaults(vault_addresses:list[str], buy_frequency_timestamp:int|None = None) -> list[StrategyVault]:
        for vault_address in vault_addresses:
            vault_contract = Contract.from_abi("AutomatedVaultERC4626", vault_address, vault_abi)
            number_of_users = vault_contract.allUsersLength()
        return []
