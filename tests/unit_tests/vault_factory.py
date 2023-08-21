from brownie import accounts
from brownie import AutomatedVaultsFactory, AutomatedVaultERC4626, TreasuryVault

# dev_wallet = accounts[0]
dev_wallet = accounts.add(config["wallets"]["from_key"])

usdc_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
vault_name = "weth/wbtc vault"
vault_symbol = "WETH/WBTC"
weth_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
wbtc_address = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"


treasury_fixed_fee_on_vault_creation =  1_000_000_000_000_000 #0.01 ETH
creator_percentage_fee_on_deposit = 25 #0.25%
treasury_percentage_fee_on_balance_update = 25 #0.25

# TreasuryVault.deploy({'from': dev_wallet})
TreasuryVault.deploy({'from': dev_wallet}, publish_source=True)
treasury_address = TreasuryVault[-1].address

AutomatedVaultsFactory.deploy(treasury_address,treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update, {'from': dev_wallet}, publish_source=True)
# AutomatedVaultsFactory.deploy(treasury_address,treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update, {'from': dev_wallet})

vaults_factory = AutomatedVaultsFactory[-1]

# Test initual vaults length
vaults_factory.allVaultsLength()

init_vault_from_factory_params=(vault_name, vault_symbol, usdc_address, [weth_address, wbtc_address])
strategy_params=([1_000_000_000_000_000_000, 10_000_000], 0, 0)
# Remix formated params:
# ["weth/wbtc vault", "WETH/WBTC", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", ["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"]]
# [[1000000000000000000,10000000],0,0]

tx=vaults_factory.createVault(init_vault_from_factory_params, strategy_params, {'from':dev_wallet, "value":1_000_000_000_000_000})

print("TREASURY BALANCE: ", TreasuryVault[-1].balance())
print("ALL VAULTS LENGTH: ", vaults_factory.allVaultsLength())
print("WALLET STRATEGIES", vaults_factory.getUserVaults(dev_wallet.address, 0))

created_strategy_vault_address = vaults_factory.allVaults(0)
created_strategy_vault = AutomatedVaultERC4626.at("created_strategy_vault_address")

print("INITIAL STRATEGY BALANCE", created_strategy_vault.balanceOf(dev_wallet))
print("INIT VAULT PARAMS:", created_strategy_vault.initMultiAssetVaultParams())
print("VAULT STRATEGY PARAMS:", created_strategy_vault.strategyParams())

# Goerli testing addresses:
# Treasury: 0x964FF99Ff53DbAaCE609eB2dA09953F9b9CAeec3
# Factory: 0x3bBc24e06285E4229d25c1a7b1BcaB9482F1288c
# Vault: 0x205eb5673D825ED50Be3FcF4532A8201bdcDE4A7