// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AuditTrail {
    struct Event {
        uint256 timestamp;
        string data;
    }

    Event[] public events;

    function addEvent(string memory _data) public {
        events.push(Event(block.timestamp, _data));
    }
}
