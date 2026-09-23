// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract PostVerifier {
    struct Record {
        uint256 timestamp;
        address uploader;
        bool exists;
    }

    mapping(bytes32 => Record) private records;

    event PostRegistered(
        bytes32 indexed fingerprint,
        address indexed uploader,
        uint256 timestamp
    );

    function registerPost(bytes32 fingerprint) external {
        require(fingerprint != bytes32(0), "Invalid fingerprint");
        require(!records[fingerprint].exists, "Fingerprint already registered");

        records[fingerprint] = Record({
            timestamp: block.timestamp,
            uploader: msg.sender,
            exists: true
        });

        emit PostRegistered(
            fingerprint,
            msg.sender,
            block.timestamp
        );
    }

    function verifyPost(bytes32 fingerprint)
        external
        view
        returns (
            bool verified,
            uint256 timestamp,
            address uploader
        )
    {
        Record memory record = records[fingerprint];

        return (
            record.exists,
            record.timestamp,
            record.uploader
        );
    }
}