// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import {Enums} from "./Enums.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

library ConfigTypes {
    struct InitMultiAssetVaultParams {
        string name;
        string symbol;
        address router;
        address factory;
        address treasury;
        address creator;
        address controller;
        IERC20 depositAsset;
        IERC20[] buyAssets;
        uint256 treasuryFixedFeeOnVaultCreation;
        uint256 creatorPercentageFeeOnDeposit;
        uint256 treasuryPercentageFeeOnBalanceUpdate;
    }
    struct StrategyParams {
        uint256[] buyAmounts;
        Enums.BuyFrequency buyFrequency;
    }
}
