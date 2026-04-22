#!/usr/bin/env python3
"""
Calculation Validator
Pre-validates all calculations before execution with detailed explanations
"""

from typing import Dict, Optional, Tuple


class CalculationValidator:
    """
    Validates all trading calculations before execution
    Provides detailed explanations in simple terms
    """
    
    def __init__(self):
        self.validation_log = []
        self.error_log = []
    
    def validate_position_entry(
        self,
        balance: float,
        entry_price: float,
        leverage: float,
        risk_pct: float,
        tp_pct: float,
        sl_pct: float
    ) -> Tuple[bool, Dict, str]:
        """
        Validate position entry calculations before execution
        
        Returns:
            (is_valid, calculations, explanation)
        """
        
        # Calculate position details
        risk_amount = balance * (risk_pct / 100)
        position_value = risk_amount / (sl_pct / 100)
        max_position_value = balance * leverage
        position_value = min(position_value, max_position_value)
        margin = position_value / leverage
        position_size = position_value / entry_price
        
        # Calculate TP/SL prices (SHORT position)
        tp_price = entry_price * (1 - tp_pct / 100)
        sl_price = entry_price * (1 + sl_pct / 100)
        
        # Calculate potential PnL
        potential_profit = (entry_price - tp_price) * position_size
        potential_loss = (entry_price - sl_price) * position_size
        
        # Calculate PnL percentages
        profit_pct = (potential_profit / margin) * 100
        loss_pct = (potential_loss / margin) * 100
        
        # Validation checks
        is_valid = True
        issues = []
        
        if margin > balance:
            is_valid = False
            issues.append(f"❌ Margin ${margin:.2f} exceeds balance ${balance:.2f}")
        
        if position_value <= 0:
            is_valid = False
            issues.append(f"❌ Invalid position value: ${position_value:.2f}")
        
        if leverage < 1 or leverage > 125:
            is_valid = False
            issues.append(f"❌ Leverage {leverage}× outside valid range (1-125)")
        
        if sl_pct <= 0 or tp_pct <= 0:
            is_valid = False
            issues.append(f"❌ Invalid TP/SL percentages: TP={tp_pct:.2f}% SL={sl_pct:.2f}%")
        
        # Build explanation
        explanation = f"""
📊 POSITION ENTRY CALCULATION CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input Parameters:
  • Current Balance: ${balance:.2f}
  • Entry Price: ${entry_price:.2f}
  • Leverage: {leverage:.0f}× (your buying power multiplier)
  • Risk: {risk_pct:.1f}% of balance (${risk_amount:.2f})
  
Position Calculations:
  • Position Value: ${position_value:.2f} (total trade size)
  • Margin Required: ${margin:.2f} (money locked from your balance)
  • Position Size: {position_size:.4f} units
  • Max Position: ${max_position_value:.2f} (balance × leverage)

Price Targets (SHORT):
  • Take Profit: ${tp_price:.2f} ({tp_pct:.2f}% below entry)
  • Stop Loss: ${sl_price:.2f} ({sl_pct:.2f}% above entry)

Potential Outcomes:
  ✅ If Take Profit Hit:
     Profit: +${potential_profit:.2f} ({profit_pct:+.1f}% return on margin)
     New Balance: ${balance + potential_profit:.2f}
  
  ❌ If Stop Loss Hit:
     Loss: ${potential_loss:.2f} ({loss_pct:.1f}% return on margin)
     New Balance: ${balance + potential_loss:.2f}

Risk/Reward Ratio: {abs(potential_profit / potential_loss):.2f}:1
"""
        
        if not is_valid:
            explanation += "\n⚠️  VALIDATION ISSUES:\n"
            for issue in issues:
                explanation += f"  {issue}\n"
        else:
            explanation += "\n✅ All calculations valid - position can be entered\n"
        
        calculations = {
            'risk_amount': risk_amount,
            'position_value': position_value,
            'max_position_value': max_position_value,
            'margin': margin,
            'position_size': position_size,
            'tp_price': tp_price,
            'sl_price': sl_price,
            'potential_profit': potential_profit,
            'potential_loss': potential_loss,
            'profit_pct': profit_pct,
            'loss_pct': loss_pct,
            'risk_reward_ratio': abs(potential_profit / potential_loss) if potential_loss != 0 else 0
        }
        
        # Log validation
        self.validation_log.append({
            'type': 'position_entry',
            'valid': is_valid,
            'calculations': calculations,
            'issues': issues if not is_valid else None
        })
        
        return is_valid, calculations, explanation
    
    def validate_pnl_calculation(
        self,
        entry_price: float,
        exit_price: float,
        position_size: float,
        margin: float,
        expected_outcome: str
    ) -> Tuple[bool, Dict, str]:
        """
        Validate PnL calculation accuracy
        
        Args:
            expected_outcome: 'TP', 'SL', or 'TIME'
        """
        
        # Calculate PnL (SHORT position)
        pnl = (entry_price - exit_price) * position_size
        pnl_pct = (pnl / margin) * 100
        
        # Double-check calculation
        price_change = exit_price - entry_price
        price_change_pct = (price_change / entry_price) * 100
        
        # For SHORT: profit when price goes down, loss when price goes up
        expected_direction = "down" if expected_outcome == "TP" else "up" if expected_outcome == "SL" else "any"
        actual_direction = "down" if price_change < 0 else "up" if price_change > 0 else "flat"
        
        is_valid = True
        issues = []
        
        # Validate direction matches outcome
        if expected_outcome == "TP" and pnl <= 0:
            is_valid = False
            issues.append("❌ Take Profit should result in positive PnL")
        
        if expected_outcome == "SL" and pnl >= 0:
            is_valid = False
            issues.append("❌ Stop Loss should result in negative PnL")
        
        # Check calculation accuracy
        recalculated_pnl = (entry_price - exit_price) * position_size
        if abs(pnl - recalculated_pnl) > 0.01:
            is_valid = False
            issues.append(f"❌ PnL calculation error: ${pnl:.2f} vs ${recalculated_pnl:.2f}")
        
        explanation = f"""
💰 PNL CALCULATION VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Position Details:
  • Entry Price: ${entry_price:.2f}
  • Exit Price: ${exit_price:.2f}
  • Position Size: {position_size:.4f} units
  • Margin Used: ${margin:.2f}
  • Outcome Type: {expected_outcome}

Price Movement:
  • Price Change: ${price_change:+.2f} ({price_change_pct:+.2f}%)
  • Direction: {actual_direction}
  • Expected: {expected_direction}

PnL Calculation (SHORT position):
  Formula: (Entry Price - Exit Price) × Position Size
  Calculation: (${entry_price:.2f} - ${exit_price:.2f}) × {position_size:.4f}
  Result: ${pnl:+.2f}

Return on Margin:
  • PnL: ${pnl:+.2f}
  • Margin: ${margin:.2f}
  • Return: {pnl_pct:+.1f}%
  
Explanation:
  SHORT positions profit when price FALLS (we sell high, buy back low)
  • If price drops: positive PnL (we win) ✅
  • If price rises: negative PnL (we lose) ❌
"""
        
        if not is_valid:
            explanation += "\n⚠️  VALIDATION ISSUES:\n"
            for issue in issues:
                explanation += f"  {issue}\n"
        else:
            explanation += "\n✅ PnL calculation verified correct\n"
        
        calculations = {
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'direction': actual_direction
        }
        
        return is_valid, calculations, explanation
    
    def validate_leverage_calculation(
        self,
        balance: float,
        margin: float,
        position_value: float
    ) -> Tuple[bool, Dict, str]:
        """Validate leverage calculation"""
        
        calculated_leverage = position_value / margin if margin > 0 else 0
        margin_from_position = position_value / calculated_leverage if calculated_leverage > 0 else 0
        
        is_valid = True
        issues = []
        
        if abs(margin - margin_from_position) > 0.01:
            is_valid = False
            issues.append(f"❌ Margin mismatch: ${margin:.2f} vs ${margin_from_position:.2f}")
        
        if margin > balance:
            is_valid = False
            issues.append(f"❌ Margin ${margin:.2f} exceeds balance ${balance:.2f}")
        
        margin_pct = (margin / balance) * 100 if balance > 0 else 0
        
        explanation = f"""
⚖️  LEVERAGE CALCULATION CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Understanding Leverage:
  Leverage is borrowed buying power that multiplies your position size.
  Example: 10× leverage means $100 margin controls $1,000 position.

Your Numbers:
  • Balance Available: ${balance:.2f}
  • Margin Required: ${margin:.2f} ({margin_pct:.1f}% of balance)
  • Position Value: ${position_value:.2f} (actual trade size)
  • Effective Leverage: {calculated_leverage:.1f}×

How It Works:
  Formula: Position Value = Margin × Leverage
  Check: ${position_value:.2f} = ${margin:.2f} × {calculated_leverage:.1f}×
  
Risk Explanation:
  • You're risking ${margin:.2f} of your ${balance:.2f} balance
  • This controls a ${position_value:.2f} position
  • If position moves 1%, your margin changes by {calculated_leverage:.1f}%
"""
        
        if not is_valid:
            explanation += "\n⚠️  VALIDATION ISSUES:\n"
            for issue in issues:
                explanation += f"  {issue}\n"
        else:
            explanation += "\n✅ Leverage calculation verified\n"
        
        calculations = {
            'calculated_leverage': calculated_leverage,
            'margin_pct_of_balance': margin_pct,
            'margin_from_position': margin_from_position
        }
        
        return is_valid, calculations, explanation
    
    def get_validation_summary(self) -> str:
        """Get summary of all validations"""
        total = len(self.validation_log)
        valid = sum(1 for v in self.validation_log if v['valid'])
        invalid = total - valid
        
        summary = f"""
📋 VALIDATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Validations: {total}
  ✅ Valid: {valid}
  ❌ Invalid: {invalid}
  
Success Rate: {(valid/total)*100:.1f}%
"""
        
        if invalid > 0:
            summary += "\n⚠️  Issues Found:\n"
            for v in self.validation_log:
                if not v['valid'] and v.get('issues'):
                    for issue in v['issues']:
                        summary += f"  {issue}\n"
        
        return summary
    
    def clear_logs(self):
        """Clear validation logs"""
        self.validation_log = []
        self.error_log = []


if __name__ == "__main__":
    # Test the validator
    validator = CalculationValidator()
    
    print("="*80)
    print("TESTING CALCULATION VALIDATOR")
    print("="*80)
    
    # Test 1: Valid position entry
    print("\n" + "="*80)
    print("TEST 1: Valid Position Entry")
    print("="*80)
    valid, calcs, explanation = validator.validate_position_entry(
        balance=100.0,
        entry_price=2000.0,
        leverage=10.0,
        risk_pct=2.0,
        tp_pct=2.0,
        sl_pct=1.0
    )
    print(explanation)
    
    # Test 2: PnL calculation
    print("\n" + "="*80)
    print("TEST 2: PnL Calculation (TP)")
    print("="*80)
    valid, calcs, explanation = validator.validate_pnl_calculation(
        entry_price=2000.0,
        exit_price=1960.0,  # 2% drop (profit for SHORT)
        position_size=0.1,
        margin=20.0,
        expected_outcome='TP'
    )
    print(explanation)
    
    # Test 3: Leverage calculation
    print("\n" + "="*80)
    print("TEST 3: Leverage Calculation")
    print("="*80)
    valid, calcs, explanation = validator.validate_leverage_calculation(
        balance=100.0,
        margin=20.0,
        position_value=200.0
    )
    print(explanation)
    
    # Summary
    print("\n" + "="*80)
    print(validator.get_validation_summary())
