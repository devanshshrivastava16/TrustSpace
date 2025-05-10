// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EscrowPayment {
    struct Payment {
        address sender;
        address recipient;
        uint256 amount;
        uint256 deadline;
        bool isReleased;
        bool isRefunded;
    }

    mapping(string => Payment) public payments;
    address public owner;

    event PaymentDeposited(string paymentId, address sender, address recipient, uint256 amount);
    event PaymentReleased(string paymentId, address recipient);
    event PaymentRefunded(string paymentId, address sender);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function deposit(
        string memory paymentId,
        address _recipient,
        uint256 _deadline
    ) public payable {
        require(msg.value > 0, "Amount must be greater than 0");
        require(_deadline > block.timestamp, "Deadline must be in the future");
        require(!payments[paymentId].isReleased && !payments[paymentId].isRefunded, "Payment already processed");

        payments[paymentId] = Payment({
            sender: msg.sender,
            recipient: _recipient,
            amount: msg.value,
            deadline: _deadline,
            isReleased: false,
            isRefunded: false
        });

        emit PaymentDeposited(paymentId, msg.sender, _recipient, msg.value);
    }

    function releasePayment(string memory paymentId) public onlyOwner {
        Payment storage payment = payments[paymentId];
        require(payment.amount > 0, "Payment does not exist");
        require(!payment.isReleased && !payment.isRefunded, "Payment already processed");
        require(block.timestamp >= payment.deadline, "Payment deadline not reached");

        payment.isReleased = true;
        payable(payment.recipient).transfer(payment.amount);

        emit PaymentReleased(paymentId, payment.recipient);
    }

    function refundPayment(string memory paymentId) public onlyOwner {
        Payment storage payment = payments[paymentId];
        require(payment.amount > 0, "Payment does not exist");
        require(!payment.isReleased && !payment.isRefunded, "Payment already processed");
        require(block.timestamp < payment.deadline, "Payment deadline reached");

        payment.isRefunded = true;
        payable(payment.sender).transfer(payment.amount);

        emit PaymentRefunded(paymentId, payment.sender);
    }

    function getPayment(string memory paymentId) public view returns (
        address sender,
        address recipient,
        uint256 amount,
        uint256 deadline,
        bool isReleased,
        bool isRefunded
    ) {
        Payment memory payment = payments[paymentId];
        return (
            payment.sender,
            payment.recipient,
            payment.amount,
            payment.deadline,
            payment.isReleased,
            payment.isRefunded
        );
    }
} 