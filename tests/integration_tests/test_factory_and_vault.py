import pytest
from typing import List
from docs.abis import erc20_abi
from helpers import get_account_from_pk
from brownie import network, config, Contract
from brownie import AutomatedVaultERC4626, AutomatedVaultsFactory
from scripts.deploy import deploy_treasury_vault, deploy_controller, deploy_strategy_worker, deploy_automated_vaults_factory

# RUN ON ARBITRUM LOCAL FORK: brownie test -s --network arbitrum-main-fork

dev_wallet = get_account_from_pk(1)

@pytest.fixture()
def configs():
    active_network_configs = config["networks"][network.show_active()]
    protocol_params = config["protocol-params"]
    strategy_params = config["strategy-params"]
    return {
        "dex_main_token_address":active_network_configs["dex_main_token_address"],
        "dex_router_address":active_network_configs["dex_router_address"],
        "dex_factory_address":active_network_configs["dex_factory_address"],
        "deposit_token_address":active_network_configs["deposit_token_address"],
        "buy_token_addresses":active_network_configs["buy_token_addresses"],
        "vault_name":active_network_configs["vault_name"],
        "vault_symbol":active_network_configs["vault_symbol"],
        "treasury_fixed_fee_on_vault_creation": protocol_params["treasury_fixed_fee_on_vault_creation"],
        "creator_percentage_fee_on_deposit": protocol_params["creator_percentage_fee_on_deposit"],
        "treasury_percentage_fee_on_balance_update": protocol_params["treasury_percentage_fee_on_balance_update"],
        "buy_amounts": strategy_params["buy_amounts"],
        "buy_frequency": strategy_params["buy_frequency"],
        "strategy_type": strategy_params["strategy_type"]
    }

def test_create_new_vault(configs):
    print(network.show_active())
    # Arrange
    verify_flag = config["networks"][network.show_active()]["verify"]
    if network.show_active() == "development" or "fork" not in network.show_active():
        pytest.skip("Only for mainnet-fork testing!")
    # Act
    treasury_vault = deploy_treasury_vault(dev_wallet, verify_flag)
    treasury_address = treasury_vault.address
    controller = deploy_controller(dev_wallet, verify_flag)
    controller_address = controller.address
    worker = deploy_strategy_worker(dev_wallet, verify_flag, configs["dex_router_address"], configs["dex_main_token_address"], controller_address)
    worker_address = worker.address
    vaults_factory = deploy_automated_vaults_factory(dev_wallet, verify_flag, configs["dex_factory_address"], configs["dex_main_token_address"], treasury_address, configs["treasury_fixed_fee_on_vault_creation"], configs["creator_percentage_fee_on_deposit"], configs["treasury_percentage_fee_on_balance_update"])
    init_vault_from_factory_params=(configs["vault_name"], configs["vault_symbol"], configs["deposit_token_address"], configs["buy_token_addresses"])
    strategy_params=(configs["buy_amounts"], configs["buy_frequency"], configs["strategy_type"], worker_address)
    vaults_factory.createVault(init_vault_from_factory_params, strategy_params, {'from':dev_wallet, "value":100_000_000_000_000})
    # Assert
    assert vaults_factory.allVaultsLength() == 1
    assert bool(vaults_factory.getUserVaults(dev_wallet,0))

def test_created_vault_init_params(configs):
    # Arrange
    strategy_vault = __get_strategy_vault()    
    name, symbol, treasury_address, creator_address, factory_address, is_active, deposit_asset, buy_assets, creator_perc_fee, treasury_perc_fee = strategy_vault.getInitMultiAssetVaultParams()
    # Act
    # Assert
    assert name == configs["vault_name"]


def test_created_vault_strategy_params(configs):
    pass

def test_created_vault_buy_tokens(configs):
    # Arrange
    strategy_vault = __get_strategy_vault()    
    buy_token_addresses = strategy_vault.getBuyAssetAddresses()
    # Act
    # Assert
    assert strategy_vault.buyAssetsLength() == len(configs["buy_token_addresses"])
    assert buy_token_addresses == configs["buy_token_addresses"]
    assert __get_tokens_decimals(buy_token_addresses) == __get_vault_buy_token_decimals(strategy_vault)
    assert strategy_vault.asset() == configs["deposit_token_address"]

# TODO: Test all contract validations

def __get_strategy_vault() -> AutomatedVaultERC4626:
    created_strategy_vault_address = AutomatedVaultsFactory[-1].allVaults(0)
    return AutomatedVaultERC4626.at(created_strategy_vault_address)

def __get_vault_buy_token_decimals(strategy_vault: AutomatedVaultERC4626) -> List[str]:
    return[strategy_vault.buyAssetsDecimals(i) for i in range(strategy_vault.buyAssetsLength())]

def __get_tokens_decimals(token_addresses: List[str]) -> int:
    return [Contract.from_abi("ERC20", token_address, erc20_abi).decimals() for token_address in token_addresses]
