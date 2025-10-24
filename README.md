# 🚀 Hyperliquid Token Deployment Script


## Detailed Setup

### 1. Prerequisites

- Python 3.7+
- A Hyperliquid wallet with sufficient funds for deployment
- Basic understanding of token deployment concepts

### 2. Installation

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install hyperliquid-python-sdk python-dotenv
```

### 3. Configuration Files

The script uses two main configuration files:

- **`.env`** - Sensitive credentials (wallet address, private key)
- **`config.json`** - Token specifications and deployment parameters

## Configuration Guide

### Environment Variables (`.env` file)

```bash
# Required: Your wallet credentials
HL_ACCOUNT_ADDRESS=0xYourMainWalletAddress...
HL_SECRET_KEY=your_private_key_hex_without_0x_prefix

# Optional: Network and API overrides
HL_MAINNET=true                    # true for mainnet, false for testnet
HL_API_URL=https://api.hyperliquid.xyz  # Custom API URL
```

### Token Configuration (`config.json`)

#### Network Settings
```json
{
  "network": {
    "mainnet": true,
    "api_url": null
  }
}
```

#### Token Specifications
```json
{
  "token": {
    "name": "SIL",              // Token ticker (≤6 chars recommended)
    "sz_decimals": 3,           // Display decimals on order book
    "wei_decimals": 18,         // On-chain atomic decimals
    "full_name": "Silhouette",  // Optional full name
    "quote_ticker": "USDC"      // Quote currency
  }
}
```

#### Genesis Distribution
```json
{
  "genesis": {
    "users": [
      {
        "address": "0xYourAddr1...",
        "amount_wei": "1000000000000000000000"  // Amount in wei
      }
    ],
    "existing_token_wei": []  // For token migrations
  }
}
```

#### Trading Parameters
```json
{
  "trading": {
    "start_price": "1.00",        // Initial price vs quote
    "order_size": "100",          // Size per ladder order
    "n_orders": 10,               // Number of ladder orders
    "n_seeded_usdc_levels": 0     // USDC-seeded levels
  }
}
```

#### Fees & Deployment
```json
{
  "fees": {
    "deployer_fee_share": "50%"   // Your fee share
  },
  "deployment": {
    "max_gas": 5000000,           // Gas limit
    "timeout_seconds": 60         // Registration timeout
  }
}
```

### Environment Variable Priority

1. **Command line** environment variables
2. **`.env` file** variables
3. **System** environment variables
4. **config.json** values (fallback)

## Usage

### Basic Deployment
```bash
python deploy_spot.py
```

### With Environment Override
```bash
HL_MAINNET=false python deploy_spot.py
```

### With Custom API
```bash
HL_API_URL=https://api.hyperliquid.xyz python deploy_spot.py
```

## Deployment Process

The script performs these steps automatically:

1. **Validation** - Checks configuration and credentials
2. **RegisterToken2** - Registers your token on Hyperliquid
3. **UserGenesis** - Distributes initial tokens to specified addresses
4. **Genesis** - Finalizes maximum supply and token economics
5. **RegisterSpot** - Creates the trading pair (TOKEN/USDC)
6. **SetDeployerTradingFeeShare** - Sets your fee share (optional)
7. **RegisterHyperliquidity** - Seeds initial liquidity with ladder orders

### Expected Output
```
HIP-1 token 'SIL' deployed. BaseIndex=123. Pair SIL/USDC ready with HIP-2.
```

## Troubleshooting

### Common Issues

#### Missing Credentials
```
Error: HL_ACCOUNT_ADDRESS and HL_SECRET_KEY must be set in environment variables
```
**Solution**: Create a `.env` file with your credentials

#### Invalid Configuration
```
Error: Missing required configuration section: token
```
**Solution**: Check your `config.json` file structure

#### Network Timeout
```
TimeoutError: Timed out waiting for token to appear in spotMeta.universe
```
**Solution**: Increase `timeout_seconds` in config or check network connectivity

#### Gas Issues
```
Error: Transaction failed due to insufficient gas
```
**Solution**: Increase `max_gas` in configuration

### Debug Mode

For detailed logging, you can modify the script to add debug prints or use Python's logging module.

### Testnet Testing

Always test your configuration on testnet first:

```json
{
  "network": {
    "mainnet": false
  }
}
```

## Additional Resources

- [Hyperliquid Documentation](https://docs.hyperliquid.xyz/)
- [HIP-1 Token Standard](https://docs.hyperliquid.xyz/developers/hyperliquid-protocol/hyperliquid-improvement-proposals/hip-1)
- [HIP-2 Liquidity Protocol](https://docs.hyperliquid.xyz/developers/hyperliquid-protocol/hyperliquid-improvement-proposals/hip-2)


## Disclaimer

This script is provided as-is for educational and development purposes. Always:
- Test on testnet before mainnet
- Verify all transactions manually
- Understand the risks of token deployment
- Keep your private keys secure
