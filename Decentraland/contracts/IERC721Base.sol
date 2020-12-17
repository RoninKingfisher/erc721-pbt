pragma solidity ^0.4.18;

interface IERC721Base {
  function totalSupply() external view returns (uint256);

  // function exists(uint256 assetId) external view returns (bool);
  function ownerOf(uint256 assetId) external view returns (address);

  function balanceOf(address holder) external view returns (uint256);

  function safeTransferFrom(address from, address to, uint256 assetId) external;
  function safeTransferFrom(address from, address to, uint256 assetId, bytes userData) external;

  function transferFrom(address from, address to, uint256 assetId) external;

  function approve(address operator, uint256 assetId) external;
  function setApprovalForAll(address operator, bool authorized) external;

  function getApprovedAddress(uint256 assetId) external view returns (address);
  function isApprovedForAll(address assetHolder, address operator) external view returns (bool);

  function isAuthorized(address operator, uint256 assetId) external view returns (bool);

  /**
  * @dev Deprecated transfer event. Now we use the standard with three parameters
  * It is only used in the ABI to get old transfer events. Do not remove
  */
  event Transfer(
    address indexed from,
    address indexed to,
    uint256 indexed assetId,
    address operator,
    bytes userData,
    bytes operatorData
  );
  /**
   * @dev Deprecated transfer event. Now we use the standard with three parameters
   * It is only used in the ABI to get old transfer events. Do not remove
   */
  event Transfer(
    address indexed from,
    address indexed to,
    uint256 indexed assetId,
    address operator,
    bytes userData
  );
  event Transfer(
    address indexed _from,
    address indexed _to,
    uint256 indexed _tokenId
  );
  event ApprovalForAll(
    address indexed _owner,
    address indexed _operator,
    bool _approved
  );
  event Approval(
    address indexed _owner,
    address indexed _approved,
    uint256 indexed _tokenId
  );
}
