import sys
from brownie import accounts, config
from brownie import AutomatedVaultsFactory, AutomatedVaultERC4626, TreasuryVault, StrategyWorker, Controller

# Goerli testing addresses (old):
# Treasury: 0x964FF99Ff53DbAaCE609eB2dA09953F9b9CAeec3
# Factory: 0x3bBc24e06285E4229d25c1a7b1BcaB9482F1288c
# Vault: 0x205eb5673D825ED50Be3FcF4532A8201bdcDE4A7

# Arbitrum mainnet testing addresses (old):
# Treasury: 0xA87c2b2dB83E849Ba1FFcf40C8F56F4984CFbC69
# Factory: 0x87899933E5E989Ae4F028FD09D77E47F8912D229
# Vault: 0x35A816b3b2E53d64d9a135fe1f4323e59A73645b

# dev_wallet = accounts[0]
dev_wallet = accounts.add(config["wallets"]["from_key_1"])
dev_wallet_2 = accounts.add(config["wallets"]["from_key_2"])

# # MAINNET ADDRESSES:
# usdce_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
# vault_name = "weth/wbtc vault"
# vault_symbol = "WETH/WBTC"
# weth_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
# wbtc_address = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"

# ARBITRUM MAINNET ADDRESSES (arbitrum-main-fork):
usdce_address = "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8"
vault_name = "weth/arb vault"
vault_symbol = "WETH/ARB"
weth_address = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
# wbtc_address = "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f"
arb_address = "0x912ce59144191c1204e64559fe8253a0e49e6548"


treasury_fixed_fee_on_vault_creation =  1_000_000_000_000_000 #0.01 ETH
creator_percentage_fee_on_deposit = 25 #0.25%
treasury_percentage_fee_on_balance_update = 25 #0.25%

# PROTOCOL TREASURY
tx1=TreasuryVault.deploy({'from': dev_wallet}) # owner must be protocol EOA
# TreasuryVault.deploy({'from': dev_wallet}, publish_source=true)
treasury_vault = TreasuryVault[-1]
treasury_address = treasury_vault.address

# CONTROLLER
tx2 = Controller.deploy({'from': dev_wallet})
controller = Controller[-1]
controller_address = controller.address 

# STRATEGY WORKER
dex_router_address = "0xbee5c10cf6e4f68f831e11c1d9e59b43560b3642" # ARBITRUM Trader Joe
tx3 = StrategyWorker.deploy(dex_router_address, controller_address, {'from': dev_wallet})
strategy_worker = StrategyWorker[-1]
strategy_worker_address = strategy_worker.address

# AutomatedVaultsFactory.deploy(treasury_address,treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update, {'from': dev_wallet}, publish_source=true)
tx4=AutomatedVaultsFactory.deploy(treasury_address,treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update, {'from': dev_wallet})

vaults_factory = AutomatedVaultsFactory[-1]

# Test initual vaults length
vaults_factory.allVaultsLength()

init_vault_from_factory_params=(vault_name, vault_symbol, usdce_address, [weth_address, arb_address])
strategy_params=([100_000, 100_000], 0, 0, strategy_worker_address) #Amounts in USDC 
# Remix formated params:
# ["weth/wbtc vault", "WETH/WBTC", "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", ["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"]]
# [[1000000000000000000,10000000],0,0]

tx5=vaults_factory.createVault(init_vault_from_factory_params, strategy_params, {'from':dev_wallet, "value":1_000_000_000_000_000})

protocol_treasury_balance = treasury_vault.balance()
print("TREASURY BALANCE: ", protocol_treasury_balance)
print("ALL VAULTS LENGTH: ", vaults_factory.allVaultsLength())
print("WALLET STRATEGIES", vaults_factory.getUserVaults(dev_wallet.address, 0))

created_strategy_vault_address = vaults_factory.allVaults(0)
created_strategy_vault = AutomatedVaultERC4626.at(created_strategy_vault_address)

print("INITIAL STRATEGY BALANCE", created_strategy_vault.balanceOf(dev_wallet))
print("INIT VAULT PARAMS:", created_strategy_vault.initMultiAssetVaultParams())
print("VAULT STRATEGY PARAMS:", created_strategy_vault.strategyParams())

usdc = Contract.from_explorer(usdce_address)
usdc_dev_balance = usdc.balanceOf(dev_wallet)
print("USDC DEV BALANCE:", usdc_dev_balance)

# APROVE ERC-20
tx6 = usdc.approve(created_strategy_vault_address, 100000, {'from': dev_wallet})
# tx2.wait(1)  # Wait for 1 confirmation

# CREATOR DEPOSIT
tx7=created_strategy_vault.deposit(20000, dev_wallet.address, {'from': dev_wallet})
created_strategy_vault.balanceOf(dev_wallet)
created_strategy_vault.totalSupply()

# WITHDRAW
tx8=created_strategy_vault.withdraw(10000, dev_wallet, dev_wallet, {'from': dev_wallet})
created_strategy_vault.balanceOf(dev_wallet)
created_strategy_vault.totalSupply()

# APROVE ERC-20
tx9 = usdc.approve(created_strategy_vault_address, 300000, {'from': dev_wallet_2})

# NON-CREATOR DEPOSIT
tx10=created_strategy_vault.deposit(300000, dev_wallet_2.address, {'from': dev_wallet_2})
created_strategy_vault.balanceOf(dev_wallet_2)
created_strategy_vault.balanceOf(dev_wallet)

# WITHDRAW PROTOCOL TREASURY BALANCE (OWNER)
tx11 = treasury_vault.withdrawNative(protocol_treasury_balance, {'from': dev_wallet})
print("TREASURY BALANCE: ", treasury_vault.balance())

# TEST STRATEGY WORKER
created_strategy_vault.balanceOf(dev_wallet)
created_strategy_vault.balanceOf(dev_wallet_2)

# USER NEEDS TO GIVE UNLIMITED ALLOWANCE TO WORKER FOR USING VAULT LP BALANCES
tx12 = created_strategy_vault.approve(strategy_worker_address, sys.maxsize, {'from': dev_wallet_2})

weth = Contract.from_explorer(weth_address)
arb = Contract.from_explorer(arb_address)
print("VAULT DEPOSITOR BALANCES BEFORE ACTION:")
print(f"WETH: {weth.balanceOf(dev_wallet_2)}")
print(f"ARB: {arb.balanceOf(dev_wallet_2)}")

# EXECUTE STRATEGY ACTION FOR dev_wallet_2
tx13 = controller.triggerStrategyAction(strategy_worker_address, created_strategy_vault_address, dev_wallet_2, {'from': dev_wallet})
print("VAULT DEPOSITOR BALANCES AFTER ACTION:")
print(f"WETH: {weth.balanceOf(dev_wallet_2)}")
print(f"ARB: {arb.balanceOf(dev_wallet_2)}")

# TODO (Future Improvements): 
# 1 - Improve swap path (now a pool between two assets needs to exist)
# 2 - Create Vault view function for vaults where user has balance








# ABI LIST (OLD):
vault_abi = [
    {
      "inputs": [
        {
          "components": [
            {
              "internalType": "string",
              "name": "name",
              "type": "string"
            },
            {
              "internalType": "string",
              "name": "symbol",
              "type": "string"
            },
            {
              "internalType": "address payable",
              "name": "treasury",
              "type": "address"
            },
            {
              "internalType": "address payable",
              "name": "creator",
              "type": "address"
            },
            {
              "internalType": "address",
              "name": "factory",
              "type": "address"
            },
            {
              "internalType": "bool",
              "name": "isActive",
              "type": "bool"
            },
            {
              "internalType": "contract IERC20",
              "name": "depositAsset",
              "type": "address"
            },
            {
              "internalType": "contract IERC20[]",
              "name": "buyAssets",
              "type": "address[]"
            },
            {
              "internalType": "uint256",
              "name": "creatorPercentageFeeOnDeposit",
              "type": "uint256"
            }
          ],
          "internalType": "struct ConfigTypes.InitMultiAssetVaultParams",
          "name": "_initMultiAssetVaultParams",
          "type": "tuple"
        },
        {
          "components": [
            {
              "internalType": "uint256[]",
              "name": "buyAmounts",
              "type": "uint256[]"
            },
            {
              "internalType": "enum Enums.BuyFrequency",
              "name": "buyFrequency",
              "type": "uint8"
            },
            {
              "internalType": "enum Enums.StrategyType",
              "name": "strategyType",
              "type": "uint8"
            }
          ],
          "internalType": "struct ConfigTypes.StrategyParams",
          "name": "_strategyParams",
          "type": "tuple"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "max",
          "type": "uint256"
        }
      ],
      "name": "ERC4626ExceededMaxDeposit",
      "type": "error"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "value",
          "type": "uint256"
        }
      ],
      "name": "Approval",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "vault",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "depositor",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "creator",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "CreatorFeeTransfered",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "sender",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "Deposit",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "value",
          "type": "uint256"
        }
      ],
      "name": "Transfer",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "sender",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "Withdraw",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "MAX_NUMBER_OF_BUY_ASSETS",
      "outputs": [
        {
          "internalType": "uint8",
          "name": "",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        }
      ],
      "name": "allowance",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "approve",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "asset",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
      ],
      "name": "balanceOf",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "buyAssetsLength",
      "outputs": [
        {
          "internalType": "uint8",
          "name": "",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "convertToAssets",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        }
      ],
      "name": "convertToShares",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "decimals",
      "outputs": [
        {
          "internalType": "uint8",
          "name": "",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "subtractedValue",
          "type": "uint256"
        }
      ],
      "name": "decreaseAllowance",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        }
      ],
      "name": "deposit",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "spender",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "addedValue",
          "type": "uint256"
        }
      ],
      "name": "increaseAllowance",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "initMultiAssetVaultParams",
      "outputs": [
        {
          "internalType": "string",
          "name": "name",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "symbol",
          "type": "string"
        },
        {
          "internalType": "address payable",
          "name": "treasury",
          "type": "address"
        },
        {
          "internalType": "address payable",
          "name": "creator",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "factory",
          "type": "address"
        },
        {
          "internalType": "bool",
          "name": "isActive",
          "type": "bool"
        },
        {
          "internalType": "contract IERC20",
          "name": "depositAsset",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "creatorPercentageFeeOnDeposit",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "maxDeposit",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "maxMint",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "maxRedeem",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "maxWithdraw",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        }
      ],
      "name": "mint",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "name",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        }
      ],
      "name": "previewDeposit",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "previewMint",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        }
      ],
      "name": "previewRedeem",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        }
      ],
      "name": "previewWithdraw",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "shares",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "redeem",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "strategyParams",
      "outputs": [
        {
          "internalType": "enum Enums.BuyFrequency",
          "name": "buyFrequency",
          "type": "uint8"
        },
        {
          "internalType": "enum Enums.StrategyType",
          "name": "strategyType",
          "type": "uint8"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "symbol",
      "outputs": [
        {
          "internalType": "string",
          "name": "",
          "type": "string"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalAssets",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalSupply",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "transfer",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "from",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "to",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "transferFrom",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "assets",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "receiver",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "withdraw",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]


factory_abi = [
    {
      "inputs": [
        {
          "internalType": "address payable",
          "name": "_treasury",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "_treasuryFixedFeeOnVaultCreation",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "_creatorPercentageFeeOnDeposit",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "_treasuryPercentageFeeOnBalanceUpdate",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "address",
          "name": "creator",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "TreasuryFeeTransfered",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "creator",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "depositAsset",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "address[]",
          "name": "buyAssets",
          "type": "address[]"
        },
        {
          "indexed": False,
          "internalType": "address",
          "name": "vaultAddress",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256[]",
          "name": "buyAmounts",
          "type": "uint256[]"
        },
        {
          "indexed": False,
          "internalType": "enum Enums.BuyFrequency",
          "name": "buyFrequency",
          "type": "uint8"
        },
        {
          "indexed": False,
          "internalType": "enum Enums.StrategyType",
          "name": "strategyType",
          "type": "uint8"
        }
      ],
      "name": "VaultCreated",
      "type": "event"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "allVaults",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "allVaultsLength",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "components": [
            {
              "internalType": "string",
              "name": "name",
              "type": "string"
            },
            {
              "internalType": "string",
              "name": "symbol",
              "type": "string"
            },
            {
              "internalType": "address",
              "name": "depositAsset",
              "type": "address"
            },
            {
              "internalType": "address[]",
              "name": "buyAssets",
              "type": "address[]"
            }
          ],
          "internalType": "struct ConfigTypes.InitMultiAssetVaultFactoryParams",
          "name": "initMultiAssetVaultFactoryParams",
          "type": "tuple"
        },
        {
          "components": [
            {
              "internalType": "uint256[]",
              "name": "buyAmounts",
              "type": "uint256[]"
            },
            {
              "internalType": "enum Enums.BuyFrequency",
              "name": "buyFrequency",
              "type": "uint8"
            },
            {
              "internalType": "enum Enums.StrategyType",
              "name": "strategyType",
              "type": "uint8"
            }
          ],
          "internalType": "struct ConfigTypes.StrategyParams",
          "name": "strategyParams",
          "type": "tuple"
        }
      ],
      "name": "createVault",
      "outputs": [
        {
          "internalType": "address",
          "name": "newVaultAddress",
          "type": "address"
        }
      ],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "creatorPercentageFeeOnDeposit",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "getUserVaults",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "treasury",
      "outputs": [
        {
          "internalType": "address payable",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "treasuryFixedFeeOnVaultCreation",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "treasuryPercentageFeeOnBalanceUpdate",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
  ]

treasury_abi = [
    {
      "inputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "token",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "ERC20Withdrawal",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "sender",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "EtherReceived",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "owner",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "NativeWithdrawal",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "previousOwner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "OwnershipTransferred",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "address",
          "name": "creator",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "address",
          "name": "treasuryAddress",
          "type": "address"
        }
      ],
      "name": "TreasuryCreated",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "renounceOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "transferOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "tokenAddress",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "withdrawERC20",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "withdrawNative",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "stateMutability": "payable",
      "type": "receive"
    }
  ]


# usdc = Contract.from_explorer(usdce_address)
# usdc_dev_balance = usdc.balanceOf(dev_wallet_2)
# # vaults_factory_address = "0x87899933E5E989Ae4F028FD09D77E47F8912D229"
# # factory = Contract.from_abi("AutomatedVaultsFactory", vaults_factory_address, factory_abi)
# tx0=AutomatedVaultsFactory.deploy(treasury_address,treasury_fixed_fee_on_vault_creation, creator_percentage_fee_on_deposit, treasury_percentage_fee_on_balance_update, {'from': dev_wallet})

# vaults_factory = AutomatedVaultsFactory[-1]

# init_vault_from_factory_params=(vault_name, vault_symbol, usdce_address, [weth_address, wbtc_address])
# strategy_params=([1_000_000_000_000_000_000, 10_000_000], 0, 0)

# tx1=factory.createVault(init_vault_from_factory_params, strategy_params, {'from':dev_wallet, "value":1_000_000_000_000_000})
# created_strategy_vault_address = factory.allVaults(1)
# created_strategy_vault = AutomatedVaultERC4626.at(created_strategy_vault_address)
# # created_strategy_vault = Contract.from_abi("AutomatedVaultERC4626", created_strategy_vault_address, vault_abi)
