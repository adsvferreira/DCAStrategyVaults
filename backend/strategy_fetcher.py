from brownie import Contract

factory_address = "0xFactoryAddress"

def fetch_vault_addresses():
    factory_contract = Contract.from_explorer(factory_address)
    
    return ["0xVaultAddress1", "0xVaultAddress2", ...]


def fetch_user_addresses():
    # Fetch and return a list of user addresses
    # Replace with actual fetching logic
    return ["0xUserAddress1", "0xUserAddress2", ...]
