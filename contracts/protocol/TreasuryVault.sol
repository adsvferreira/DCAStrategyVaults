// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract TreasuryVault is Ownable {
    event TreasuryCreated(address creator, address treasuryAddress);
    event EtherReceived(address indexed sender, uint256 amount);
    event NativeWithdrawal(address indexed owner, uint256 amount);
    event ERC20Withdrawal(
        address indexed owner,
        address indexed token,
        uint256 amount
    );

    constructor() {
        emit TreasuryCreated(msg.sender, address(this));
    }

    receive() external payable {
        emit EtherReceived(msg.sender, msg.value);
    }

    function withdrawNative(uint256 amount) public onlyOwner {
        require(amount <= address(this).balance, "Insufficient balance");
        (bool success, ) = owner().call{value: amount}("");
        require(success, "Ether transfer failed");
        emit NativeWithdrawal(owner(), amount);
    }

    function withdrawERC20(
        address tokenAddress,
        uint256 amount
    ) public onlyOwner {
        IERC20 token = IERC20(tokenAddress);
        require(
            amount <= token.balanceOf(address(this)),
            "Insufficient balance"
        );
        (bool success, ) = tokenAddress.call(
            abi.encodeWithSignature(
                "transfer(address,uint256)",
                owner(),
                amount
            )
        );
        require(success, "Token transfer failed");
        emit ERC20Withdrawal(owner(), tokenAddress, amount);
    }
}
