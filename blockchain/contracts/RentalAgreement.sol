// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract RentalAgreement {
    struct Agreement {
        address owner;
        address renter;
        uint256 amount;
        uint256 duration;
        uint256 startTime;
        bool isActive;
        bool isCompleted;
    }

    mapping(string => Agreement) public agreements;
    address public owner;

    event AgreementCreated(string propertyId, address owner, address renter, uint256 amount, uint256 duration);
    event AgreementCompleted(string propertyId);
    event AgreementCancelled(string propertyId);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function createAgreement(
        string memory propertyId,
        address _owner,
        address _renter,
        uint256 _amount,
        uint256 _duration
    ) public onlyOwner {
        require(_amount > 0, "Amount must be greater than 0");
        require(_duration > 0, "Duration must be greater than 0");
        require(!agreements[propertyId].isActive, "Agreement already exists");

        agreements[propertyId] = Agreement({
            owner: _owner,
            renter: _renter,
            amount: _amount,
            duration: _duration,
            startTime: block.timestamp,
            isActive: true,
            isCompleted: false
        });

        emit AgreementCreated(propertyId, _owner, _renter, _amount, _duration);
    }

    function completeAgreement(string memory propertyId) public onlyOwner {
        require(agreements[propertyId].isActive, "Agreement does not exist");
        require(!agreements[propertyId].isCompleted, "Agreement already completed");

        agreements[propertyId].isCompleted = true;
        agreements[propertyId].isActive = false;

        emit AgreementCompleted(propertyId);
    }

    function cancelAgreement(string memory propertyId) public onlyOwner {
        require(agreements[propertyId].isActive, "Agreement does not exist");
        require(!agreements[propertyId].isCompleted, "Agreement already completed");

        agreements[propertyId].isActive = false;

        emit AgreementCancelled(propertyId);
    }

    function getAgreement(string memory propertyId) public view returns (
        address _owner,
        address _renter,
        uint256 _amount,
        uint256 _duration,
        uint256 _startTime,
        bool _isActive,
        bool _isCompleted
    ) {
        Agreement memory agreement = agreements[propertyId];
        return (
            agreement.owner,
            agreement.renter,
            agreement.amount,
            agreement.duration,
            agreement.startTime,
            agreement.isActive,
            agreement.isCompleted
        );
    }
} 