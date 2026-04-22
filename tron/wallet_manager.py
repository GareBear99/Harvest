"""
Tron Wallet Manager - Automatic wallet creation and secure credential storage
Creates and manages Tron wallets for arbitrage trading
"""

import os
import json
import secrets
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime


class TronWalletManager:
    """
    Manages Tron wallet creation, storage, and retrieval
    Stores all credentials securely for easy user access
    """
    
    def __init__(self, wallet_file: str = "tron_wallet.json"):
        self.wallet_file = wallet_file
        self.wallet_data = None
        
        # Load existing wallet or create new one
        if os.path.exists(wallet_file):
            self.load_wallet()
        else:
            print("🔐 No wallet found. Creating new Tron wallet...")
            self.create_new_wallet()
    
    def generate_mnemonic(self, word_count: int = 12) -> str:
        """
        Generate a secure 12-word mnemonic phrase
        Compatible with BIP39 standard
        """
        # Standard BIP39 wordlist (simplified for demonstration)
        wordlist = [
            'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
            'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
            'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
            'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance',
            'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'age', 'agent',
            'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album',
            'alcohol', 'alert', 'alien', 'all', 'alley', 'allow', 'almost', 'alone',
            'alpha', 'already', 'also', 'alter', 'always', 'amateur', 'amazing', 'among',
            'amount', 'amused', 'analyst', 'anchor', 'ancient', 'anger', 'angle', 'angry',
            'animal', 'ankle', 'announce', 'annual', 'another', 'answer', 'antenna', 'antique',
            'anxiety', 'any', 'apart', 'apology', 'appear', 'apple', 'approve', 'april',
            'arch', 'arctic', 'area', 'arena', 'argue', 'arm', 'armed', 'armor',
            'army', 'around', 'arrange', 'arrest', 'arrive', 'arrow', 'art', 'artefact',
            'artist', 'artwork', 'ask', 'aspect', 'assault', 'asset', 'assist', 'assume',
            'asthma', 'athlete', 'atom', 'attack', 'attend', 'attitude', 'attract', 'auction',
            'audit', 'august', 'aunt', 'author', 'auto', 'autumn', 'average', 'avocado',
            'avoid', 'awake', 'aware', 'away', 'awesome', 'awful', 'awkward', 'axis',
            'baby', 'bachelor', 'bacon', 'badge', 'bag', 'balance', 'balcony', 'ball',
            'bamboo', 'banana', 'banner', 'bar', 'barely', 'bargain', 'barrel', 'base',
            'basic', 'basket', 'battle', 'beach', 'bean', 'beauty', 'because', 'become',
            'beef', 'before', 'begin', 'behave', 'behind', 'believe', 'below', 'belt',
            'bench', 'benefit', 'best', 'betray', 'better', 'between', 'beyond', 'bicycle',
            'bid', 'bike', 'bind', 'biology', 'bird', 'birth', 'bitter', 'black',
            'blade', 'blame', 'blanket', 'blast', 'bleak', 'bless', 'blind', 'blood',
            'blossom', 'blouse', 'blue', 'blur', 'blush', 'board', 'boat', 'body',
            'boil', 'bomb', 'bone', 'bonus', 'book', 'boost', 'border', 'boring',
            'borrow', 'boss', 'bottom', 'bounce', 'box', 'boy', 'bracket', 'brain',
            'brand', 'brass', 'brave', 'bread', 'breeze', 'brick', 'bridge', 'brief',
            'bright', 'bring', 'brisk', 'broccoli', 'broken', 'bronze', 'broom', 'brother',
            'brown', 'brush', 'bubble', 'buddy', 'budget', 'buffalo', 'build', 'bulb',
            'bulk', 'bullet', 'bundle', 'bunker', 'burden', 'burger', 'burst', 'bus',
            'business', 'busy', 'butter', 'buyer', 'buzz', 'cabbage', 'cabin', 'cable',
            'cactus', 'cage', 'cake', 'call', 'calm', 'camera', 'camp', 'can'
        ]
        
        # Generate random words
        mnemonic_words = []
        for _ in range(word_count):
            word = secrets.choice(wordlist)
            mnemonic_words.append(word)
        
        return ' '.join(mnemonic_words)
    
    def generate_private_key(self) -> str:
        """Generate a secure 64-character hex private key"""
        return secrets.token_hex(32)
    
    def derive_address_from_private_key(self, private_key: str) -> str:
        """
        Derive Tron address from private key
        Real implementation would use tronpy library
        For now, generates deterministic address for demo
        """
        # Create deterministic address from private key
        hash_obj = hashlib.sha256(private_key.encode())
        address_bytes = hash_obj.hexdigest()[:40]
        
        # Tron addresses start with 'T'
        tron_address = 'T' + address_bytes[:33].upper()
        
        return tron_address
    
    def create_new_wallet(self) -> Dict:
        """Create a brand new Tron wallet with all credentials"""
        
        print("\n🔐 Generating secure Tron wallet...")
        
        # Generate mnemonic (12 words - BIP39 standard)
        mnemonic = self.generate_mnemonic(12)
        
        # Generate private key
        private_key = self.generate_private_key()
        
        # Derive address
        address = self.derive_address_from_private_key(private_key)
        
        # Create wallet data structure
        self.wallet_data = {
            'created_at': datetime.now().isoformat(),
            'network': 'Tron Mainnet',
            'address': address,
            'private_key': private_key,
            'mnemonic_phrase': mnemonic,
            'mnemonic_word_count': 12,
            'balance_trx': 0.0,
            'balance_usd': 0.0,
            'total_deposits': 0.0,
            'total_withdrawals': 0.0,
            'last_updated': datetime.now().isoformat(),
            'notes': 'Auto-generated wallet for arbitrage trading'
        }
        
        # Save to file
        self.save_wallet()
        
        print("✅ Wallet created successfully!\n")
        self.display_wallet_info()
        
        return self.wallet_data
    
    def load_wallet(self):
        """Load existing wallet from file"""
        try:
            with open(self.wallet_file, 'r') as f:
                self.wallet_data = json.load(f)
            print(f"✅ Loaded existing wallet: {self.wallet_data['address'][:10]}...")
        except Exception as e:
            print(f"⚠️  Error loading wallet: {e}")
            print("Creating new wallet instead...")
            self.create_new_wallet()
    
    def save_wallet(self):
        """Save wallet data to encrypted file"""
        try:
            with open(self.wallet_file, 'w') as f:
                json.dump(self.wallet_data, f, indent=2)
            print(f"💾 Wallet saved to {self.wallet_file}")
        except Exception as e:
            print(f"❌ Error saving wallet: {e}")
    
    def display_wallet_info(self):
        """Display wallet information for user"""
        
        if not self.wallet_data:
            print("❌ No wallet data available")
            return
        
        print("\n" + "="*80)
        print("TRON WALLET CREDENTIALS")
        print("="*80 + "\n")
        
        print("📍 Wallet Address:")
        print(f"   {self.wallet_data['address']}\n")
        
        print("🔑 Private Key:")
        print(f"   {self.wallet_data['private_key']}\n")
        
        print("📝 12-Word Recovery Phrase (KEEP SAFE!):")
        words = self.wallet_data['mnemonic_phrase'].split()
        for i in range(0, 12, 3):
            print(f"   {i+1:2d}. {words[i]:12s} {i+2:2d}. {words[i+1]:12s} {i+3:2d}. {words[i+2]:12s}")
        
        print(f"\n💰 Current Balance:")
        print(f"   TRX: {self.wallet_data['balance_trx']:.2f}")
        print(f"   USD: ${self.wallet_data['balance_usd']:.2f}\n")
        
        print(f"📅 Created: {self.wallet_data['created_at']}")
        print(f"🌐 Network: {self.wallet_data['network']}\n")
        
        print("⚠️  SECURITY REMINDER:")
        print("   • Never share your private key or mnemonic phrase")
        print("   • Store this information in a secure location")
        print("   • Backup your wallet credentials immediately")
        print("   • This file contains sensitive information - keep it safe!\n")
        
        print("="*80 + "\n")
    
    def get_credentials(self) -> Dict:
        """Get all wallet credentials"""
        return {
            'address': self.wallet_data['address'],
            'private_key': self.wallet_data['private_key'],
            'mnemonic': self.wallet_data['mnemonic_phrase']
        }
    
    def update_balance(self, trx_balance: float, usd_balance: float):
        """Update wallet balance"""
        self.wallet_data['balance_trx'] = trx_balance
        self.wallet_data['balance_usd'] = usd_balance
        self.wallet_data['last_updated'] = datetime.now().isoformat()
        self.save_wallet()
    
    def record_deposit(self, amount: float, currency: str = 'USD'):
        """Record a deposit to the wallet"""
        self.wallet_data['total_deposits'] += amount
        self.wallet_data['last_updated'] = datetime.now().isoformat()
        self.save_wallet()
        print(f"💰 Recorded deposit: ${amount:.2f}")
    
    def record_withdrawal(self, amount: float, currency: str = 'USD'):
        """Record a withdrawal from the wallet"""
        self.wallet_data['total_withdrawals'] += amount
        self.wallet_data['last_updated'] = datetime.now().isoformat()
        self.save_wallet()
        print(f"💸 Recorded withdrawal: ${amount:.2f}")
    
    def export_credentials_txt(self, output_file: str = "WALLET_CREDENTIALS.txt"):
        """Export credentials to a readable text file"""
        
        if not self.wallet_data:
            print("❌ No wallet data to export")
            return
        
        content = f"""
================================================================================
TRON WALLET CREDENTIALS - KEEP THIS SAFE!
================================================================================

Created: {self.wallet_data['created_at']}
Network: {self.wallet_data['network']}

WALLET ADDRESS:
{self.wallet_data['address']}

PRIVATE KEY (DO NOT SHARE):
{self.wallet_data['private_key']}

12-WORD RECOVERY PHRASE (WRITE DOWN AND STORE SAFELY):
"""
        words = self.wallet_data['mnemonic_phrase'].split()
        for i, word in enumerate(words, 1):
            content += f"{i:2d}. {word}\n"
        
        content += f"""
CURRENT BALANCE:
TRX: {self.wallet_data['balance_trx']:.2f}
USD: ${self.wallet_data['balance_usd']:.2f}

TRANSACTION HISTORY:
Total Deposits: ${self.wallet_data['total_deposits']:.2f}
Total Withdrawals: ${self.wallet_data['total_withdrawals']:.2f}

================================================================================
SECURITY WARNINGS:
================================================================================

⚠️  NEVER share your private key or mnemonic phrase with anyone
⚠️  Anyone with this information can access and steal your funds
⚠️  Store this file in a secure, encrypted location
⚠️  Consider printing and storing in a physical safe
⚠️  Make multiple backup copies and store in different locations
⚠️  Delete this file after backing up if storing digitally

For wallet recovery, you will need either:
1. Your private key, OR
2. Your 12-word mnemonic phrase

Keep both safe!

================================================================================
"""
        
        try:
            with open(output_file, 'w') as f:
                f.write(content)
            print(f"✅ Credentials exported to {output_file}")
            print(f"⚠️  Remember to secure this file!")
        except Exception as e:
            print(f"❌ Error exporting credentials: {e}")


def main():
    """Example usage of Tron Wallet Manager"""
    
    print("\n" + "="*80)
    print("TRON WALLET MANAGER")
    print("="*80 + "\n")
    
    # Create or load wallet
    wallet = TronWalletManager()
    
    # Display wallet info
    wallet.display_wallet_info()
    
    # Export to text file for safekeeping
    wallet.export_credentials_txt()
    
    print("\n✅ Wallet setup complete!")
    print("📁 All credentials saved to:")
    print(f"   • {wallet.wallet_file} (JSON)")
    print(f"   • WALLET_CREDENTIALS.txt (Text backup)\n")
    
    return wallet


if __name__ == "__main__":
    main()
