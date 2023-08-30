from brownie import Contract, accounts, config

dev_wallet = accounts.add(config["wallets"]["from_key_1"])
factory_address = "0x5d2ffdb504ea97c191deeeda364832b1cc72246f"
factory_contract = Contract.from_explorer(factory_address)

# dataclass Vault

def fetch_vault_addresses() -> list[str]:
    factory_contract = Contract.from_explorer(factory_address)
    number_of_vaults = factory_contract.allVaultsLength()
    return [factory_contract.allVaults(i) for i in range(number_of_vaults)]


def fetch_user_addresses(vault_addresses:list[str]) -> dict[str, list[str]]:
    for vault_address in vault_addresses:
        vault_contract = Contract.from_abi("AutomatedVaultERC4626", vault_address, vault_abi)
        number_of_users = vault_contract.allUsersLength()
    return ["0xUserAddress1", "0xUserAddress2", ...]
