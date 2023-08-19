// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

/**
 * @title   Automated ERC-4626 Vault.
 * @author  André Ferreira
 * @dev    VERSION: 1.0
 *          DATE:    2023.08.15
 */

/**
TODO:
Guarantee that only factory can instaciate vault(in vault) - OK
Implement remaining univ2 usuful features and vault indexing by user - OK
Check if new vault addresses are not colliding
 */

import {Enums} from "../libraries/types/Enums.sol";
import {ConfigTypes} from "../libraries/types/ConfigTypes.sol";
import {AutomatedVaultERC4626, IAutomatedVaultERC4626, IERC20} from "./AutomatedVaultERC4626.sol";

contract AutomatedVaultsFactory {
    event VaultCreated(
        address indexed creator,
        address indexed depositAsset,
        address[] buyAssets,
        address vaultAddress,
        uint256[] buyAmounts,
        Enums.BuyFrequency buyFrequency,
        Enums.StrategyType strategyType
    );
    event TreasuryFeeTransfered(address creator, uint256 amount);
    // debug only:
    // event CreatingVault(
    //     address creator,
    //     address depositAsset,
    //     address[] buyAssets,
    //     address vaultAddress,
    //     uint256[] buyAmounts,
    //     Enums.BuyFrequency buyFrequency,
    //     Enums.StrategyType strategyType
    // );

    address public treasury;
    uint256 public treasuryFixedFeeOnVaultCreation; // AMOUNT IN NATIVE TOKEN CONSIDERING ALL DECIMALS
    uint256 public creatorPercentageFeeOnDeposit; // ONE_TEN_THOUSANDTH_PERCENT units (1 = 0.01%)
    uint256 public treasuryPercentageFeeOnBalanceUpdate; // ONE_TEN_THOUSANDTH_PERCENT units (1 = 0.01%)

    address[] public allVaults;
    mapping(address => address[]) public getUserVaults;

    // mapping(address => bool) public isVaultCreated;

    constructor(
        address _treasury,
        uint256 _treasuryFixedFeeOnVaultCreation,
        uint256 _creatorPercentageFeeOnDeposit,
        uint256 _treasuryPercentageFeeOnBalanceUpdate
    ) {
        treasury = _treasury;
        treasuryFixedFeeOnVaultCreation = _treasuryFixedFeeOnVaultCreation;
        creatorPercentageFeeOnDeposit = _creatorPercentageFeeOnDeposit;
        treasuryPercentageFeeOnBalanceUpdate = _treasuryPercentageFeeOnBalanceUpdate;
    }

    function allVaultsLength() external view returns (uint) {
        return allVaults.length;
    }

    function createVault(
        ConfigTypes.InitMultiAssetVaultFactoryParams
            memory initMultiAssetVaultFactoryParams,
        ConfigTypes.StrategyParams calldata strategyParams
    ) external returns (address newVaultAddress) {
        _validateCreateVaultInputs(initMultiAssetVaultFactoryParams);
        _transferTreasuryFee();
        ConfigTypes.InitMultiAssetVaultParams
            memory initMultiAssetVaultParams = _buildInitMultiAssetVaultParams(
                initMultiAssetVaultFactoryParams
            );
        // debug only
        // emit CreatingVault(
        //     initMultiAssetVaultParams.creator,
        //     address(initMultiAssetVaultParams.depositAsset),
        //     initMultiAssetVaultFactoryParams.buyAssets,
        //     newVaultAddress,
        //     strategyParams.buyAmounts,
        //     strategyParams.buyFrequency,
        //     strategyParams.strategyType
        // );
        IAutomatedVaultERC4626 newVault = new AutomatedVaultERC4626(
            initMultiAssetVaultParams,
            strategyParams
        );
        newVaultAddress = address(newVault);
        allVaults.push(newVaultAddress);
        _addUserVault(initMultiAssetVaultParams.creator, newVaultAddress);
        emit VaultCreated(
            initMultiAssetVaultParams.creator,
            address(initMultiAssetVaultParams.depositAsset),
            initMultiAssetVaultFactoryParams.buyAssets,
            newVaultAddress,
            strategyParams.buyAmounts,
            strategyParams.buyFrequency,
            strategyParams.strategyType
        );
    }

    function _validateCreateVaultInputs(
        ConfigTypes.InitMultiAssetVaultFactoryParams
            memory initMultiAssetVaultFactoryParams
    ) private view {
        require(
            address(initMultiAssetVaultFactoryParams.depositAsset) !=
                address(0),
            "ZERO_ADDRESS"
        );
        require(msg.sender.balance > treasuryFixedFeeOnVaultCreation);
    }

    function _transferTreasuryFee() private {
        (bool success, ) = msg.sender.call{
            value: treasuryFixedFeeOnVaultCreation
        }("");
        require(success, "Fee transfer to treasurty address failed.");
        emit TreasuryFeeTransfered(
            address(msg.sender),
            treasuryFixedFeeOnVaultCreation
        );
    }

    function _buildInitMultiAssetVaultParams(
        ConfigTypes.InitMultiAssetVaultFactoryParams
            memory _initMultiAssetVaultFactoryParams
    )
        private
        view
        returns (
            ConfigTypes.InitMultiAssetVaultParams
                memory _initMultiAssetVaultParams
        )
    {
        _initMultiAssetVaultParams = ConfigTypes.InitMultiAssetVaultParams(
            _initMultiAssetVaultFactoryParams.name,
            _initMultiAssetVaultFactoryParams.symbol,
            treasury,
            address(msg.sender),
            address(this),
            false,
            IERC20(_initMultiAssetVaultFactoryParams.depositAsset),
            _wrapBuyAddressesIntoIERC20(
                _initMultiAssetVaultFactoryParams.buyAssets
            ),
            creatorPercentageFeeOnDeposit
        );
    }

    function _wrapBuyAddressesIntoIERC20(
        address[] memory buyAddresses
    ) private pure returns (IERC20[] memory iERC20instances) {
        uint256 buyAddressesLength = buyAddresses.length;
        iERC20instances = new IERC20[](buyAddressesLength);
        for (uint256 i = 0; i < buyAddressesLength; i++) {
            iERC20instances[i] = IERC20(buyAddresses[i]);
        }
        return iERC20instances;
    }

    function _addUserVault(address creator, address newVault) private {
        require(
            creator != address(0),
            "Null Address is not a valid creator address"
        );
        require(
            newVault != address(0),
            "Null Address is not a valid newVault address"
        );
        // 2 vaults can't the same address, tx would revert at vault instantiation
        if (getUserVaults[creator].length == 0) {
            getUserVaults[creator].push(newVault);
        } else {
            getUserVaults[creator].push(newVault);
        }
    }

    // Add to createVault in case of address collision:
    // bytes memory bytecode = type(AutomatedVaultERC4626).creationCode;
    // address newVaultAddress = _generateAddress(
    //     bytecode,
    //     initMultiAssetVaultParams.creator,
    //     address(initMultiAssetVaultParams.depositAsset),
    //     strategyParams.buyAmounts,
    //     strategyParams.buyFrequency,
    //     strategyParams.strategyType
    // );
    // transfer fixed fee to treasury address

    // function _generateAddress(
    //     bytes memory bytecode,
    //     address creator,
    //     address underlyingAsset,
    //     uint256[] memory buyAmounts,
    //     Enums.BuyFrequency buyFrequency,
    //     Enums.StrategyType strategyType
    // ) private pure returns (address) {
    //     bytes32 salt = keccak256(
    //         abi.encodePacked(
    //             bytecode,
    //             creator,
    //             underlyingAsset,
    //             buyAmounts,
    //             uint256(buyFrequency),
    //             uint256(strategyType)
    //         )
    //     );
    //     address generatedAddress = address(uint160(uint256(salt)));
    //     return generatedAddress;
    // }
}
