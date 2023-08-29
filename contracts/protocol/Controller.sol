// SPDX-License-Identifier: MIT
pragma solidity 0.8.21;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {StrategyWorker} from "./StrategyWorker.sol";

contract Controller is Ownable {
    address strategyWorkerAddress;

    constructor(address _strategyWorkerAddress) {
        strategyWorkerAddress = _strategyWorkerAddress;
    }

    // Only Callable by Pulsar Deployer EOA Address
    function triggerStrategyAction(
        address _strategyVaultAddress,
        address _depositorAddress
    ) public onlyOwner {
        StrategyWorker strategyWorker = StrategyWorker(strategyWorkerAddress);
        strategyWorker.executeStrategyAction(
            _strategyVaultAddress,
            _depositorAddress
        );
    }
}
