// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import {Enums} from "./Enums.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

library ConfigTypes {
    struct InitMultiAssetVaultParams {
        string name;
        string symbol;
        address treasury;
        address creator;
        address factory;
        bool isActive;
        IERC20 depositAsset;
        IERC20[] buyAssets;
        uint256 creatorPercentageFeeOnDeposit;
    }
    struct InitMultiAssetVaultFactoryParams {
        string name;
        string symbol;
        IERC20 depositAsset;
        IERC20[] buyAssets;
    }
    struct StrategyParams {
        uint256[] buyAmounts;
        Enums.BuyFrequency buyFrequency;
        Enums.StrategyType strategyType;
    }
}
