// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {TreasuryVault} from "./TreasuryVault.sol";
import {StrategiesTreasuryVault} from "./StrategiesTreasuryVault.sol";
import {AutomatedVaultERC4626, IAutomatedVaultERC4626, IERC20} from "./AutomatedVaultERC4626.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {PercentageMath} from "../libraries/math/percentageMath.sol";
import {IUniswapV2Router} from "../interfaces/IUniswapV2Router.sol";
import {ConfigTypes} from "../libraries/types/ConfigTypes.sol";

contract StrategyWorker {
    using SafeERC20 for IERC20;
    using Math for uint256;
    using PercentageMath for uint256;

    address public dexRouter;
    address public controller;
    address public strategiesTreasuryVault;

    event StrategyActionExecuted(
        address indexed vault,
        address indexed depositor,
        address tokenIn,
        uint256 tokenInAmount,
        address[] tokensOut,
        uint256[] tokensOutAmounts,
        uint256 feeAmount
    );

    constructor(
        address _dexRouter,
        address _controller,
        address _strategiesTreasuryVault
    ) {
        controller = _controller;
        dexRouter = _dexRouter;
        strategiesTreasuryVault = _strategiesTreasuryVault;
    }

    modifier onlyController() {
        require(msg.sender == controller, "Only controller can call this");
        _;
    }

    function executeStrategyAction(
        // 1 - Withdraw from vault (after wallet gives allowance) - OK -> TRY TO ALLOW DIRECTLY IN DEPOSIT
        // 2 - Executes a swap in the defined dex for each buyToken/amount
        // 3 - Deposits every swapped token into StrategiesTreasuryVault (Subtracted protocol fee)
        // 4 - Sends protocol fee to TreasuryVault
        // 5 - Updates vault lastUpdate
        // Emits event strategyActionExecuted
        address _strategyVaultAddress,
        address _depositorAddress
    ) external onlyController {
        AutomatedVaultERC4626 _strategyVault = AutomatedVaultERC4626(
            _strategyVaultAddress
        );

        (
            address _depositAsset,
            address[] memory _buyAssets,
            uint256[] memory _buyAmounts
        ) = _getSwapParams(_strategyVault);

        ConfigTypes.InitMultiAssetVaultParams
            memory initMultiAssetVaultParams = _strategyVault
                .getInitMultiAssetVaultParams();

        uint256 _actionFeePercentage = initMultiAssetVaultParams
            .treasuryPercentageFeeOnBalanceUpdate;
        address _protocolTreasuryAddress = initMultiAssetVaultParams.treasury;
        uint256 _amountToWithdraw;
        uint256[] memory _buyAmountsAfterFee;
        uint256 _totalFee;

        (
            _amountToWithdraw,
            _buyAmountsAfterFee,
            _totalFee
        ) = _calculateAmountsAfterFee(_buyAmounts, _actionFeePercentage);

        uint256 _totalBuyAmount = _amountToWithdraw - _totalFee;

        _strategyVault.setLastUpdate();

        _strategyVault.withdraw(
            _amountToWithdraw,
            address(this), //receiver
            _depositorAddress //owner
        );

        uint256[] memory _swappedAssetAmounts = _swapTokens(
            _depositAsset,
            _buyAssets,
            _buyAmountsAfterFee
        );

        // _depositIntoStrategiesTreasury(); Done in swap function

        _depositFeeIntoProtocolTreasury(
            _totalFee,
            _depositAsset,
            _protocolTreasuryAddress
        );

        emit StrategyActionExecuted(
            _strategyVaultAddress,
            _depositorAddress,
            _depositAsset,
            _totalBuyAmount,
            _buyAssets,
            _swappedAssetAmounts,
            _totalFee
        );
    }

    function _getSwapParams(
        AutomatedVaultERC4626 _strategyVault
    )
        private
        view
        returns (
            address _depositAsset,
            address[] memory _buyAssets,
            uint256[] memory _buyAmounts
        )
    {
        ConfigTypes.InitMultiAssetVaultParams
            memory _initMultiAssetVaultParams = _strategyVault
                .getInitMultiAssetVaultParams();
        _depositAsset = address(_initMultiAssetVaultParams.depositAsset);
        _buyAssets = _strategyVault.getBuyAssetAddresses();
        _buyAmounts = _strategyVault.getStrategyParams().buyAmounts;
    }

    function _calculateAmountsAfterFee(
        uint256[] memory _buyAmounts,
        uint256 _actionFeePercentage
    )
        private
        returns (
            uint256 _amountToWithdraw,
            uint256[] memory _buyAmountsAfterFee,
            uint256 _totalFee
        )
    {
        uint256 _buyAmountsLength = _buyAmounts.length;
        _buyAmountsAfterFee = new uint256[](_buyAmountsLength);
        for (uint256 i = 0; i < _buyAmountsLength; i++) {
            uint256 _buyAmount = _buyAmounts[i];
            uint256 _feeAmount = _buyAmount.percentMul(_actionFeePercentage);
            _totalFee += _feeAmount;
            uint256 _buyAmountAfterFee = _buyAmount - _feeAmount;
            _buyAmountsAfterFee[i] = _buyAmountAfterFee;
            _amountToWithdraw += _buyAmount;
        }
        require(
            _amountToWithdraw > 0,
            "Total buyAmount must be greater than zero"
        );
    }

    function _swapTokens(
        address _depositAsset,
        address[] memory _buyAssets,
        uint256[] memory _buyAmountsAfterFee
    ) internal returns (uint256[] memory _amountsOut) {
        uint256 _buyAssetsLength = _buyAssets.length;
        _amountsOut = new uint256[](_buyAssetsLength);
        for (uint256 i = 0; i < _buyAssets.length; i++) {
            uint256 amountOut = _swapToken(
                _depositAsset,
                _buyAssets[i],
                _buyAmountsAfterFee[i]
            );
            _amountsOut[i] = amountOut;
        }
    }

    function _swapToken(
        address _depositAsset,
        address _buyAsset,
        uint256 _buyAmountAfterFee
    ) internal returns (uint256 _amountOut) {
        IERC20(_depositAsset).transferFrom(
            msg.sender,
            address(this),
            _buyAmountAfterFee
        );
        IERC20(_depositAsset).approve(dexRouter, _buyAmountAfterFee);

        address[] memory _path = new address[](2);
        _path[0] = _depositAsset;
        _path[1] = _buyAsset;

        uint256[] memory _amountsOut = IUniswapV2Router(dexRouter)
            .swapExactTokensForTokens(
                _buyAmountAfterFee,
                0, // AmountOutMin (set to 0 for simplicity)
                _path,
                strategiesTreasuryVault, // swapped tokens sent directly ro strategy treasury
                block.timestamp
            );
        uint256 _amountsOutLength = _amountsOut.length;
        _amountOut = _amountsOut[_amountsOutLength - 1]; // amounts out contains results from all the pools in the choosen route
    }

    function _depositFeeIntoProtocolTreasury(
        uint256 _totalFee,
        address _protocolTreasuryAddress,
        address _depositAssetAddress
    ) internal {
        IERC20(_depositAssetAddress).safeTransferFrom(
            address(this),
            _protocolTreasuryAddress,
            _totalFee
        );
    }
}
