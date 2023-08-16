// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

/**
 * @title   Automated ERC-4626 Vault Factory.
 * @author  André Ferreira

  * @dev    VERSION: 1.0
 *          DATE:    2023.08.15
*/

/**

TODO:
- implements most of the ERC4626 functions - OK
- %treasury fee must de set in constructor - OK
- controller address set in constructor - OK
- router address set in constructor - OK
- accrues fees to creator in each deposit of others - OK
- accrues fees to Treasury in vault creation - fixed amount - TODO - implement at factory level (transfer in constructor is bad) - OK
- only factory can instanciate - OK
- give allowance to worker to spend all deposits - Allowance given by the user. Flow: 1-create vault/2-deposit underlying/3-allow worker to spend all lp's
- transfer fees to treasury in each worker interaction (withdraw) - TODO  - implement at worker level
*/

import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {Enums} from "../libraries/types/Enums.sol";
import {PercentageMath} from "../libraries/math/percentageMath.sol";
import {ConfigTypes} from "../libraries/types/ConfigTypes.sol";
import {IAutomatedVaultERC4626} from "../interfaces/IAutomatedVaultERC4626.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ERC4626, IERC4626} from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import {IERC20Metadata, IERC20, ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract AutomatedVaultERC4626 is ERC4626, IAutomatedVaultERC4626 {
    using Math for uint256;
    using PercentageMath for uint256;
    using SafeERC20 for IERC20;
    ConfigTypes.InitMultiAssetVaultParams public initMultiAssetVaultParams;
    ConfigTypes.StrategyParams public strategyParams;

    uint8 public constant MAX_NUMBER_OF_BUY_ASSETS = 10;

    uint8[] private _buyAssetsDecimals;
    uint8 public immutable buyAssetsLength;

    event CreatorFeeTransfered(
        address indexed vault,
        address indexed depositor,
        address indexed creator,
        uint256 shares
    );

    /**
     * @dev Attempted to deposit more assets than the max amount for `receiver`.
     */
    error ERC4626ExceededMaxDeposit(
        address receiver,
        uint256 assets,
        uint256 max
    );

    /**
     * @dev Underlying asset contracts must be ERC20-compatible contracts (ERC20 or ERC777) whitelisted at factory level.
     */
    constructor(
        ConfigTypes.InitMultiAssetVaultParams memory _initMultiAssetVaultParams,
        ConfigTypes.StrategyParams memory _strategyParams
    )
        ERC4626(_initMultiAssetVaultParams.depositAsset)
        ERC20(
            _initMultiAssetVaultParams.name,
            _initMultiAssetVaultParams.symbol
        )
    {
        require(msg.sender == _initMultiAssetVaultParams.factory, "FORBIDDEN");
        _validateInputs(
            _initMultiAssetVaultParams.buyAssets,
            strategyParams.buyAmounts
        );
        initMultiAssetVaultParams = _initMultiAssetVaultParams;
        strategyParams = _strategyParams;
        _setBuyAssetsDecimals(_initMultiAssetVaultParams.buyAssets);
        initMultiAssetVaultParams.isActive = false;
    }

    /** @dev See {IERC4626-deposit}. */
    function deposit(
        uint256 assets,
        address receiver
    ) public override(ERC4626, IERC4626) returns (uint256) {
        uint256 maxAssets = maxDeposit(receiver);
        if (assets > maxAssets) {
            revert ERC4626ExceededMaxDeposit(receiver, assets, maxAssets);
        }

        uint256 shares = previewDeposit(assets);
        _deposit(_msgSender(), receiver, assets, shares);
        return shares;
    }

    function _validateInputs(
        IERC20[] memory buyAssets,
        uint256[] memory buyAmounts
    ) internal pure {
        // Check if max number of deposited assets was not exceeded
        require(
            buyAssets.length <= uint256(MAX_NUMBER_OF_BUY_ASSETS),
            "MAX_NUMBER_OF_BUY_ASSETS exceeded"
        );
        // Check if both arrays have the same length
        require(
            buyAmounts.length == buyAssets.length,
            "buyAmounts and buyAssets arrays must have the same length"
        );
    }

    function _setBuyAssetsDecimals(IERC20[] memory buyAssets) internal {
        for (uint8 i = 0; i < buyAssets.length; i++) {
            _buyAssetsDecimals[i] = _getAssetDecimals(buyAssets[i]);
        }
    }

    function _getAssetDecimals(
        IERC20 depositAsset
    ) private view returns (uint8) {
        (bool success, uint8 assetDecimals) = _tryGetAssetDecimals(
            depositAsset
        );
        uint8 finalAssetDecimals = success ? assetDecimals : 18;
        return finalAssetDecimals;
    }

    /**
     * @dev Attempts to fetch the asset decimals. A return value of false indicates that the attempt failed in some way.
     */
    function _tryGetAssetDecimals(
        IERC20 asset_
    ) private view override returns (bool, uint8) {
        (bool success, bytes memory encodedDecimals) = address(asset_)
            .staticcall(abi.encodeCall(IERC20Metadata.decimals, ()));
        if (success && encodedDecimals.length >= 32) {
            uint256 returnedDecimals = abi.decode(encodedDecimals, (uint256));
            if (returnedDecimals <= type(uint8).max) {
                return (true, uint8(returnedDecimals));
            }
        }
        return (false, 0);
    }

    /**
     * @dev Deposit/mint common workflow.
     */
    function _deposit(
        address caller,
        address receiver,
        uint256 assets,
        uint256 shares
    ) internal virtual override {
        // **************************************** ERC4262 ****************************************
        // If _asset is ERC777, `transferFrom` can trigger a reentrancy BEFORE the transfer happens through the
        // `tokensToSend` hook. On the other hand, the `tokenReceived` hook, that is triggered after the transfer,
        // calls the vault, which is assumed not malicious.
        //
        // Conclusion: we need to do the transfer before we mint so that any reentrancy would happen before the
        // assets are transferred and before the shares are minted, which is a valid state.
        // slither-disable-next-line reentrancy-no-eth
        // **************************************** CUSTOM ****************************************
        // After underlying transfer and before vault lp mint _afterUnderlyingTransferHook was added
        // where vault creator fee logic is implemented
        address depositAsset = asset();
        SafeERC20.safeTransferFrom(
            IERC20(depositAsset),
            caller,
            address(this),
            assets
        );
        _afterUnderlyingTransferHook(receiver, shares);
        emit Deposit(caller, receiver, assets, shares);
    }

    function _afterUnderlyingTransferHook(
        address receiver,
        uint256 shares
    ) internal {
        if (receiver == initMultiAssetVaultParams.creator) {
            _mint(receiver, shares);
        } else {
            // if deposit is not from vault creator, a fee will be removed
            // from depositor and added to creator balance
            uint256 creatorPercentage = initMultiAssetVaultParams
                .creatorPercentageFeeOnDeposit;
            uint256 depositorPercentage = 1 - creatorPercentage;
            uint256 creatorShares = shares.percentMul(creatorPercentage);
            uint256 depositorShares = shares.percentMul(depositorPercentage);
            _mint(receiver, depositorShares);
            _mint(initMultiAssetVaultParams.creator, creatorShares);
            emit CreatorFeeTransfered(
                address(this),
                initMultiAssetVaultParams.creator,
                receiver,
                creatorShares
            );
        }
        // Activates vault after 1st deposit
        if (initMultiAssetVaultParams.isActive == false) {
            initMultiAssetVaultParams.isActive == true;
        }
    }
}
