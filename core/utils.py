"""Utility functions for SGLI system."""

from decimal import Decimal
import locale
from typing import Union

def formatar_moeda_brasileira(valor: Union[Decimal, float, int]) -> str:
    """
    Format currency in Brazilian Real format.
    
    Args:
        valor: Numeric value to format
    
    Returns:
        str: Formatted currency string (e.g., "R$ 1.234,56")
    """
    if valor is None:
        return "R$ 0,00"
    
    try:
        # Convert to Decimal for precision
        if not isinstance(valor, Decimal):
            valor = Decimal(str(valor))
        
        # Format with Brazilian pattern
        valor_str = f"{valor:.2f}"
        partes = valor_str.split('.')
        inteira = partes[0]
        decimal = partes[1]
        
        # Add thousands separators
        if len(inteira) > 3:
            inteira_formatada = ""
            for i, digit in enumerate(reversed(inteira)):
                if i > 0 and i % 3 == 0:
                    inteira_formatada = "." + inteira_formatada
                inteira_formatada = digit + inteira_formatada
        else:
            inteira_formatada = inteira
        
        return f"R$ {inteira_formatada},{decimal}"
    
    except (ValueError, TypeError, AttributeError):
        return "R$ 0,00"

def converter_moeda_para_decimal(valor_str: str) -> Decimal:
    """
    Convert Brazilian currency string to Decimal.
    
    Args:
        valor_str: Currency string (e.g., "R$ 1.234,56")
    
    Returns:
        Decimal: Converted value
    """
    if not valor_str:
        return Decimal('0.00')
    
    try:
        # Remove currency symbol and spaces
        clean_value = valor_str.replace('R$', '').strip()
        # Replace Brazilian format with standard format
        clean_value = clean_value.replace('.', '').replace(',', '.')
        return Decimal(clean_value)
    except (ValueError, TypeError):
        return Decimal('0.00')

class MoneyField:
    """Helper class for money field formatting."""
    
    @staticmethod
    def format_display(value: Union[Decimal, float, int]) -> str:
        """Format for display purposes."""
        return formatar_moeda_brasileira(value)
    
    @staticmethod
    def format_input(value: str) -> Decimal:
        """Format for input processing."""
        return converter_moeda_para_decimal(value)

