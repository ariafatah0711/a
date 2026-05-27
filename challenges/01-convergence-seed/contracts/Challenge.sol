// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Challenge {
    address public immutable player;
    bytes32 public immutable targetSecret;
    bool public solved;

    event Solved(address indexed player);

    constructor(address player_, bytes32 targetSecret_) {
        require(player_ != address(0), "invalid player");
        player = player_;
        targetSecret = targetSecret_;
    }

    modifier onlyPlayer() {
        require(msg.sender == player, "not player");
        _;
    }

    function solve(bytes32 secret) external onlyPlayer {
        require(secret == targetSecret, "bad secret");
        solved = true;
        emit Solved(msg.sender);
    }
}
