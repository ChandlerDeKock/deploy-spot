# pip install hyperliquid-python-sdk python-dotenv
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import time
import os
import json
import sys
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file with validation."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required sections
        required_sections = ['network', 'token', 'genesis', 'trading', 'fees', 'deployment']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Please copy 'config.example.json' to 'config.json' and fill in your values.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration values."""
    # Check environment variables for credentials
    account_address = os.getenv("HL_ACCOUNT_ADDRESS")
    secret_key = os.getenv("HL_SECRET_KEY")
    
    if not account_address or not secret_key:
        print("Error: HL_ACCOUNT_ADDRESS and HL_SECRET_KEY must be set in environment variables")
        print("Please create a .env file with your credentials (see env.example)")
        sys.exit(1)
    
    # Check token name length
    if len(config['token']['name']) > 6:
        print("Warning: Token name should be <= 6 characters for best compatibility")
    
    # Validate genesis users format
    for user in config['genesis']['users']:
        if 'address' not in user or 'amount_wei' not in user:
            print("Error: Each genesis user must have 'address' and 'amount_wei' fields")
            sys.exit(1)
    
    # Validate existing token wei format
    for token in config['genesis']['existing_token_wei']:
        if not isinstance(token, list) or len(token) != 2:
            print("Error: existing_token_wei entries must be [tokenIndex, wei] format")
            sys.exit(1)

# Load and validate configuration
config = load_config()
validate_config(config)

# Extract configuration values
MAINNET = config['network']['mainnet']
# Allow environment variable to override network setting
if os.getenv("HL_MAINNET") is not None:
    MAINNET = os.getenv("HL_MAINNET").lower() in ('true', '1', 'yes', 'on')

API_URL = config['network']['api_url'] or os.getenv("HL_API_URL") or (constants.MAINNET_API_URL if MAINNET else constants.TESTNET_API_URL)

# Credentials from environment variables
ACCOUNT_ADDRESS = os.getenv("HL_ACCOUNT_ADDRESS")
SECRET_KEY = os.getenv("HL_SECRET_KEY")
QUOTE_TICKER = config['token']['quote_ticker']

# Token specifications
TOKEN_NAME = config['token']['name']
SZ_DECIMALS = config['token']['sz_decimals']
WEI_DECIMALS = config['token']['wei_decimals']
FULL_NAME = config['token']['full_name']

# Genesis distribution
GENESIS_USERS = [(user['address'], user['amount_wei']) for user in config['genesis']['users']]
EXISTING_TOKEN_WEI = config['genesis']['existing_token_wei']

# Max supply checksum (must equal sum of all userGenesis + existingToken allocations)
MAX_SUPPLY_WEI = str(sum(int(x[1]) for x in GENESIS_USERS) + sum(int(x[1]) for x in EXISTING_TOKEN_WEI))

# Trading parameters
START_PRICE = config['trading']['start_price']
ORDER_SIZE = config['trading']['order_size']
N_ORDERS = config['trading']['n_orders']
N_SEEDED_USDC_LEVELS = config['trading']['n_seeded_usdc_levels']

# Fee settings
SET_FEE_SHARE = config['fees']['deployer_fee_share']

# Deployment settings
MAX_GAS = config['deployment']['max_gas']
TIMEOUT_SECONDS = config['deployment']['timeout_seconds']

def wait_for_spot_meta(info: Info, ticker: str, timeout_s=None):
    """Poll the spot metadata until our token appears and return indices."""
    if timeout_s is None:
        timeout_s = TIMEOUT_SECONDS
    t_end = time.time() + timeout_s
    while time.time() < t_end:
        meta = info.spot_meta()
        # meta["universe"] is a list of dicts with fields like {"tokens": [{"ticker":"PURR",...}, {"ticker":"USDC",...}], ...}
        # We also need the token index for our base asset (by ticker) and the spot index for the pair base/USDC.
        universe = meta.get("universe", [])
        # 1) get base token index in the tokens registry
        #    The docs: spot orders use "asset = 10000 + index", where index is in spotMeta.universe. We'll also need pair spot index.
        #    We'll find pair entries that include our ticker and USDC to grab the spot index.
        base_index = None
        usdc_index = None
        spot_index = None
        # First, find global token->index map
        token_map = {}  # ticker -> token index
        # Gather tokens list from meta if present (depends on SDK response shape)
        tokens = meta.get("tokens", [])
        if tokens:
            for i, tok in enumerate(tokens):
                token_map[tok.get("ticker")] = i
        # Fallback: some deployments may not expose a flat 'tokens' map; try to parse from universe entries.
        for entry in universe:
            toks = entry.get("tokens", [])
            for i, tok in enumerate(toks):
                if tok.get("ticker") not in token_map:
                    token_map[tok.get("ticker")] = tok.get("index", None)

        base_index = token_map.get(ticker)
        usdc_index = token_map.get(QUOTE_TICKER)

        # 2) find the spot pair index
        for i, entry in enumerate(universe):
            toks = entry.get("tokens", [])
            tickers = [t.get("ticker") for t in toks]
            if ticker in tickers and QUOTE_TICKER in tickers:
                spot_index = i
                break

        if base_index is not None and usdc_index is not None and spot_index is not None:
            return base_index, usdc_index, spot_index
        time.sleep(1)
    raise TimeoutError("Timed out waiting for token to appear in spotMeta.universe")

def main():
    info = Info(API_URL, skip_ws=True)
    ex = Exchange(API_URL, ACCOUNT_ADDRESS, SECRET_KEY, MAINNET)

    # --- 1) RegisterToken2 ---
    # spec: { name, szDecimals, weiDecimals }, plus optional fullName and a gas cap (docs require maxGas)
    action = {
        "type": "spotDeploy",
        "registerToken2": {
            "spec": {
                "name": TOKEN_NAME,
                "szDecimals": SZ_DECIMALS,
                "weiDecimals": WEI_DECIMALS,
            },
            "maxGas": MAX_GAS,  # configurable gas limit
            "fullName": FULL_NAME,
        },
    }
    ex.action(action)  # signs and POSTs to /exchange

    # We need the base token index for subsequent steps; it will be assigned after RegisterToken2.
    # Depending on network, this can be near-instant; we poll the info endpoint to discover indices.
    base_index, usdc_index, _ = wait_for_spot_meta(info, TOKEN_NAME)

    # --- 2) UserGenesis (can be called multiple times) ---
    if GENESIS_USERS or EXISTING_TOKEN_WEI:
        action = {
            "type": "spotDeploy",
            "userGenesis": {
                "token": base_index,
                "userAndWei": GENESIS_USERS,               # list[ [addr, wei] ]
                "existingTokenAndWei": EXISTING_TOKEN_WEI, # list[ [tokenIndex, wei] ]
                # "blacklistUsers": [ [addr, True], ...]   # optional
            },
        }
        ex.action(action)

    # --- 3) Genesis (finalize max supply; checksum must match cumulative userGenesis allocations) ---
    action = {
        "type": "spotDeploy",
        "genesis": {
            "token": base_index,
            "maxSupply": MAX_SUPPLY_WEI,
            # "noHyperliquidity": True,  # uncomment to skip HIP-2 at launch
        },
    }
    ex.action(action)

    # --- 4) RegisterSpot (create pair base/USDC) ---
    action = {
        "type": "spotDeploy",
        "registerSpot": {
            "tokens": [base_index, usdc_index],  # [base, quote]
        },
    }
    ex.action(action)

    # (Optional) fee share tweak — defaults to 100%; you may only DEcrease
    if SET_FEE_SHARE is not None:
        action = {
            "type": "spotDeploy",
            "setDeployerTradingFeeShare": {
                "token": base_index,
                "share": SET_FEE_SHARE,  # e.g. "50%"
            },
        }
        ex.action(action)

    # --- 5) RegisterHyperliquidity (seed HIP-2 passive liquidity for the pair) ---
    # First, get the pair's spot index (different from base token index)
    _, _, spot_index = wait_for_spot_meta(info, TOKEN_NAME)
    action = {
        "type": "spotDeploy",
        "registerHyperliquidity": {
            "spot": spot_index,
            "startPx": START_PRICE,            # string
            "orderSz": ORDER_SIZE,             # string; FLOAT units, not wei
            "nOrders": N_ORDERS,
            "nSeededLevels": N_SEEDED_USDC_LEVELS,  # optional
        },
    }
    ex.action(action)

    print(f"HIP-1 token '{TOKEN_NAME}' deployed. BaseIndex={base_index}. Pair {TOKEN_NAME}/{QUOTE_TICKER} ready with HIP-2.")

if __name__ == "__main__":
    main()