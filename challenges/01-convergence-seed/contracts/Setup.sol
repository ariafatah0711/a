// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Challenge.sol";

contract Setup {
    address public immutable player;
    Challenge public challenge;

    constructor(address player_, bytes32 targetSecret) {
        require(player_ != address(0), "invalid player");
        player = player_;
        challenge = new Challenge(player_, targetSecret);
    }

    function isSolved() external view returns (bool) {
        return challenge.solved();
    }
}
