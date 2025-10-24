#!/usr/bin/env python3
"""
Setup script for Hyperliquid token deployment.
This script helps you set up the configuration files.
"""

import os
import shutil
import sys

def main():
    print("🚀 Hyperliquid Token Deployment Setup")
    print("=" * 40)
    
    # Check if config.json exists
    if not os.path.exists("config.json"):
        if os.path.exists("config.example.json"):
            shutil.copy("config.example.json", "config.json")
            print("✅ Created config.json from config.example.json")
        else:
            print("❌ config.example.json not found!")
            return 1
    
    # Check if .env exists
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            shutil.copy("env.example", ".env")
            print("✅ Created .env from env.example")
            print("⚠️  Please edit .env with your actual credentials!")
        else:
            print("❌ env.example not found!")
            return 1
    else:
        print("ℹ️  .env already exists")
    
    print("\n📝 Next steps:")
    print("1. Edit .env with your wallet address and private key")
    print("2. Edit config.json with your token specifications")
    print("3. Run: python deploy_spot.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

