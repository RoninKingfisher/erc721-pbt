pragma solidity ^0.4.24; 

interface ERC721TokenReceiver {
    function onERC721Received(address _operator, address _from, uint256 _tokenId, bytes _data) returns(bytes4);
}

contract TokenReceiver is ERC721TokenReceiver {

  bytes4 private constant MAGIC = bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"));

  function onERC721Received
  (address _operator, address _from, uint256 _tokenId, bytes  _data) public returns(bytes4) {
     return MAGIC;
  }

  constructor() public { }
}


