// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./Setup.sol";

contract ChallengeFactory {
    address public immutable owner;
    bytes32 public constant TARGET_SECRET = bytes32(uint256(0x1337));

    mapping(address => Setup) public setupOf;

    event Spawned(address indexed player, address indexed setup);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function spawnFor(address player) external onlyOwner returns (address) {
        require(player != address(0), "invalid player");
        require(address(setupOf[player]) == address(0), "already spawned");

        Setup setup = new Setup(player, TARGET_SECRET);
        setupOf[player] = setup;

        emit Spawned(player, address(setup));
        return address(setup);
    }

    function isSolved(address player) external view returns (bool) {
        Setup setup = setupOf[player];
        if (address(setup) == address(0)) {
            return false;
        }
        return setup.isSolved();
    }
}
