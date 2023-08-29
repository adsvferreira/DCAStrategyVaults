// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract StrategiesTreasuryVault {
    using SafeERC20 for IERC20;

    mapping(address => mapping(address => uint256)) public claimableBalances;
    address public strategyWorker;

    constructor(address _strategyWorker) {
        strategyWorker = _strategyWorker;
    }

    modifier onlyStrategyWorker() {
        require(
            msg.sender == strategyWorker,
            "Only strategyWorker can call this"
        );
        _;
    }

    function deposit(
        address _depositorAddress,
        address[] calldata _assetAddresses,
        uint256[] calldata _amounts
    ) external onlyStrategyWorker {
        require(
            _assetAddresses.length == _amounts.length,
            "assetAddresses and amounts arrays length mismatch"
        );

        for (uint256 i = 0; i < _assetAddresses.length; i++) {
            address assetAddress = _assetAddresses[i];
            uint256 amount = _amounts[i];

            require(amount > 0, "Amount must be greater than 0");
            require(
                IERC20(assetAddress).balanceOf(strategyWorker) >= amount,
                "strategyWorker insufficient balances"
            );

            IERC20(assetAddress).safeTransferFrom(
                strategyWorker,
                address(this),
                amount
            );

            claimableBalances[_depositorAddress][assetAddress] += amount;
        }
    }

    function claim(address[] calldata _assetAddresses) external {
        require(
            _assetAddresses.length > 0,
            "No claimable token addresses specified"
        );

        uint256 totalClaimable = 0;

        for (uint256 i = 0; i < _assetAddresses.length; i++) {
            address assetAddress = _assetAddresses[i];
            uint256 balance = claimableBalances[msg.sender][assetAddress];

            if (balance > 0) {
                // Transfer tokens from the contract to the caller using transferFrom
                IERC20(assetAddress).safeTransferFrom(
                    address(this),
                    msg.sender,
                    balance
                );
                totalClaimable += balance;
                claimableBalances[msg.sender][assetAddress] = 0;
            }
        }

        require(totalClaimable > 0, "No claimable balance");
    }
}
