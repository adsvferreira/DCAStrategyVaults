import pytest
from brownie import network, config
from helpers import get_account_from_pk
from scripts.deploy import deploy_treasury_vault, deploy_controller, deploy_strategy_worker, deploy_automated_vaults_factory

dev_wallet = get_account_from_pk(1)

def test_create_new_vault():
    print(network.show_active())
    verify_flag = config["networks"][network.show_active()]["verify"]
    # Arrange
    if network.show_active() == "development" or "fork" not in network.show_active():
        pytest.skip("Only for mainnet-fork testing!")
    
    dex_main_token_address = config["networks"][network.show_active()]["dex_main_token_address"]
    dex_router_address = config["networks"][network.show_active()]["dex_router_address"] 
    dex_factory_address = config["networks"][network.show_active()]["dex_factory_address"] 
    deposit_token_address = config["networks"][network.show_active()]["deposit_token_address"]
    buy_tokens_addresses = config["networks"][network.show_active()]["buy_token_addresses"]
    vault_name = config["networks"][network.show_active()]["vault_name"]
    vault_symbol = config["networks"][network.show_active()]["vault_symbol"]
    treasury_fixed_fee_on_vault_creation =  config["protocol-params"]["treasury_fixed_fee_on_vault_creation"]
    creator_percentage_fee_on_deposit = config["protocol-params"]["creator_percentage_fee_on_deposit"]
    treasury_percentage_fee_on_balance_update = config["protocol-params"]["treasury_percentage_fee_on_balance_update"]
    buy_amounts = config["strategy-params"]["buy_amounts"]
    buy_frequency = config["strategy-params"]["buy_frequency"]
    strategy_type = config["strategy-params"]["strategy_type"]
    # Act
    treasury_vault = deploy_treasury_vault(dev_wallet, verify_flag)
    treasury_address = treasury_vault.address
    controller = deploy_controller(dev_wallet, verify_flag)
    controller_address = controller.address
    worker = deploy_strategy_worker(dev_wallet, verify_flag, dex_router_address, dex_main_token_address, controller_address)
    worker_address = worker.address
    vaults_factory = deploy_automated_vaults_factory(dev_wallet, verify_flag, dex_factory_address, dex_main_token_address, treasury_address, treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update)
    init_vault_from_factory_params=(vault_name, vault_symbol, deposit_token_address, buy_tokens_addresses)
    strategy_params=(buy_amounts, buy_frequency, strategy_type, worker_address)
    vaults_factory.createVault(init_vault_from_factory_params, strategy_params, {'from':dev_wallet, "value":100_000_000_000_000})
    # Assert
    assert vaults_factory.allVaultsLength() == 1
