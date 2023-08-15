// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import {Enums} from "../libraries/types/Enums.sol";
import {ConfigTypes} from "../libraries/types/ConfigTypes.sol";
import {AutomatedVaultERC4626, IAutomatedVaultERC4626} from "./AutomatedVaultERC4626.sol";

/**
TODO:
Guarantee that only factory can instaciate vault(in vault)
Check if new vault addresses are not colliding
Implement remaining univ2 usuful features and vault indexing by user
 */

contract AutomatedVaultsFactory {
    event VaultCreated(
        address vaultAddress,
        address depositAsset,
        uint256[] buyAmounts,
        Enums.BuyFrequency buyFrequency,
        Enums.StrategyType strategyType,
        address creator
    );

    address[] public allVaults;
    mapping(address => address[]) public getUserVaults;

    // mapping(address => bool) public isVaultCreated;

    function allVaultsLength() external view returns (uint) {
        return allVaults.length;
    }

    function createVault(
        ConfigTypes.InitMultiAssetVaultParams
            calldata initMultiAssetVaultParams,
        ConfigTypes.StrategyParams calldata strategyParams
    ) external returns (address vault) {
        require(
            address(initMultiAssetVaultParams.depositAsset) != address(0),
            "ZERO_ADDRESS"
        );
        // bytes memory bytecode = type(AutomatedVaultERC4626).creationCode;
        // address newVaultAddress = _generateAddress(
        //     bytecode,
        //     initMultiAssetVaultParams.creator,
        //     address(initMultiAssetVaultParams.depositAsset),
        //     strategyParams.buyAmounts,
        //     strategyParams.buyFrequency,
        //     strategyParams.strategyType
        // );
        IAutomatedVaultERC4626 newVault = new AutomatedVaultERC4626(
            initMultiAssetVaultParams,
            strategyParams
        );
        emit VaultCreated(
            address(newVault),
            address(initMultiAssetVaultParams.depositAsset),
            strategyParams.buyAmounts,
            strategyParams.buyFrequency,
            strategyParams.strategyType,
            initMultiAssetVaultParams.creator
        );
    }

    // function _generateAddress(
    //     bytes memory bytecode,
    //     address creator,
    //     address underlyingAsset,
    //     uint256[] memory buyAmounts,
    //     Enums.BuyFrequency buyFrequency,
    //     Enums.StrategyType strategyType
    // ) internal pure returns (address) {
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
