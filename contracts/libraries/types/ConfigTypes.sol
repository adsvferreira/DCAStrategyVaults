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
        uint256 treasuryFixedFeeOnVaultCreation;
        uint256 creatorPercentageFeeOnDeposit; // ONE_TEN_THOUSANDTH_PERCENT units (1 = 0.01%)
        uint256 treasuryPercentageFeeOnBalanceUpdate; // ONE_TEN_THOUSANDTH_PERCENT units (1 = 0.01%)
    }
    struct StrategyParams {
        uint256[] buyAmounts;
        Enums.BuyFrequency buyFrequency;
        Enums.StrategyType strategyType;
    }
}
