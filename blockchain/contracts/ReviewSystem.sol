// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReviewSystem {
    struct Review {
        string propertyId;
        address reviewer;
        uint256 rating;
        string comment;
        uint256 timestamp;
        bool isVerified;
    }

    mapping(string => Review[]) public propertyReviews;
    mapping(address => Review[]) public userReviews;
    address public owner;

    event ReviewSubmitted(string propertyId, address reviewer, uint256 rating);
    event ReviewVerified(string propertyId, uint256 reviewIndex);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function submitReview(
        string memory propertyId,
        uint256 rating,
        string memory comment
    ) public {
        require(rating >= 1 && rating <= 5, "Rating must be between 1 and 5");
        require(bytes(comment).length > 0, "Comment cannot be empty");

        Review memory review = Review({
            propertyId: propertyId,
            reviewer: msg.sender,
            rating: rating,
            comment: comment,
            timestamp: block.timestamp,
            isVerified: false
        });

        propertyReviews[propertyId].push(review);
        userReviews[msg.sender].push(review);

        emit ReviewSubmitted(propertyId, msg.sender, rating);
    }

    function verifyReview(string memory propertyId, uint256 reviewIndex) public onlyOwner {
        require(reviewIndex < propertyReviews[propertyId].length, "Review does not exist");
        
        propertyReviews[propertyId][reviewIndex].isVerified = true;
        
        emit ReviewVerified(propertyId, reviewIndex);
    }

    function getPropertyReviews(string memory propertyId) public view returns (
        address[] memory reviewers,
        uint256[] memory ratings,
        string[] memory comments,
        uint256[] memory timestamps,
        bool[] memory isVerified
    ) {
        Review[] memory reviews = propertyReviews[propertyId];
        uint256 length = reviews.length;

        reviewers = new address[](length);
        ratings = new uint256[](length);
        comments = new string[](length);
        timestamps = new uint256[](length);
        isVerified = new bool[](length);

        for (uint256 i = 0; i < length; i++) {
            reviewers[i] = reviews[i].reviewer;
            ratings[i] = reviews[i].rating;
            comments[i] = reviews[i].comment;
            timestamps[i] = reviews[i].timestamp;
            isVerified[i] = reviews[i].isVerified;
        }

        return (reviewers, ratings, comments, timestamps, isVerified);
    }

    function getUserReviews(address user) public view returns (
        string[] memory propertyIds,
        uint256[] memory ratings,
        string[] memory comments,
        uint256[] memory timestamps,
        bool[] memory isVerified
    ) {
        Review[] memory reviews = userReviews[user];
        uint256 length = reviews.length;

        propertyIds = new string[](length);
        ratings = new uint256[](length);
        comments = new string[](length);
        timestamps = new uint256[](length);
        isVerified = new bool[](length);

        for (uint256 i = 0; i < length; i++) {
            propertyIds[i] = reviews[i].propertyId;
            ratings[i] = reviews[i].rating;
            comments[i] = reviews[i].comment;
            timestamps[i] = reviews[i].timestamp;
            isVerified[i] = reviews[i].isVerified;
        }

        return (propertyIds, ratings, comments, timestamps, isVerified);
    }

    function getAverageRating(string memory propertyId) public view returns (uint256) {
        Review[] memory reviews = propertyReviews[propertyId];
        if (reviews.length == 0) return 0;

        uint256 sum = 0;
        for (uint256 i = 0; i < reviews.length; i++) {
            sum += reviews[i].rating;
        }

        return sum / reviews.length;
    }
} 