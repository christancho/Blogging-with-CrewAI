#!/usr/bin/env python3
"""
Debug utilities for CrewAI Blog Generation System
Simple debugging functions for inspecting text variables
"""

def debug_print_texts(var1: str, var2: str, var3: str, var4: str, 
                     labels: tuple = ("Variable 1", "Variable 2", "Variable 3", "Variable 4")):
    """
    Print 4 text variables separately in the console for debugging purposes
    
    Args:
        var1, var2, var3, var4 (str): Text variables to debug
        labels (tuple): Optional labels for each variable (default: "Variable 1", etc.)
    """
    print("\n" + "="*60)
    print("🔍 DEBUG: Text Variables Inspection")
    print("="*60)
    
    variables = [var1, var2, var3, var4]
    
    for i, (label, var) in enumerate(zip(labels, variables), 1):
        print(f"\n📊 {label}:")
        print("-" * 40)
        print(f"Type: {type(var).__name__}")
        print(f"Length: {len(str(var))} characters")
        print(f"Content:")
        print(f"'{var}'")
        
        # Show first and last 100 characters if content is long
        if len(str(var)) > 200:
            print(f"\n📝 First 100 chars: '{str(var)[:100]}...'")
            print(f"📝 Last 100 chars: '...{str(var)[-100:]}'")
    
    print("\n" + "="*60)
    print("✅ Debug inspection complete")
    print("="*60)

def debug_print_texts_detailed(var1: str, var2: str, var3: str, var4: str,
                              labels: tuple = ("Variable 1", "Variable 2", "Variable 3", "Variable 4")):
    """
    Print 4 text variables with detailed analysis for debugging
    
    Args:
        var1, var2, var3, var4 (str): Text variables to debug
        labels (tuple): Optional labels for each variable
    """
    print("\n" + "="*80)
    print("🔍 DEBUG: Detailed Text Variables Analysis")
    print("="*80)
    
    variables = [var1, var2, var3, var4]
    
    for i, (label, var) in enumerate(zip(labels, variables), 1):
        print(f"\n📊 {label}:")
        print("-" * 50)
        print(f"Type: {type(var).__name__}")
        print(f"Length: {len(str(var))} characters")
        print(f"Word count: {len(str(var).split())} words")
        print(f"Line count: {len(str(var).splitlines())} lines")
        
        # Check for common patterns
        var_str = str(var)
        has_json = var_str.strip().startswith('{') or var_str.strip().startswith('[')
        has_html = '<' in var_str and '>' in var_str
        has_markdown = '#' in var_str or '**' in var_str or '*' in var_str
        
        print(f"Contains JSON: {has_json}")
        print(f"Contains HTML: {has_html}")
        print(f"Contains Markdown: {has_markdown}")
        
        print(f"\nContent preview:")
        print(f"'{var_str[:200]}{'...' if len(var_str) > 200 else ''}'")
        
        if len(var_str) > 200:
            print(f"\nLast 100 characters:")
            print(f"'{var_str[-100:]}'")
    
    print("\n" + "="*80)
    print("✅ Detailed debug analysis complete")
    print("="*80)

# Example usage function
def example_usage():
    """Example of how to use the debug functions"""
    print("🚀 Example usage of debug utilities:")
    
    # Example variables
    sample_var1 = "This is a sample text for debugging"
    sample_var2 = '{"key": "value", "data": [1, 2, 3]}'
    sample_var3 = "# Markdown Header\n\nThis is **bold** text"
    sample_var4 = "<h1>HTML Header</h1><p>This is a paragraph</p>"
    
    # Use the simple debug function
    debug_print_texts(
        sample_var1, sample_var2, sample_var3, sample_var4,
        labels=("Sample Text", "JSON Data", "Markdown", "HTML")
    )
    
    # Use the detailed debug function
    debug_print_texts_detailed(
        sample_var1, sample_var2, sample_var3, sample_var4,
        labels=("Sample Text", "JSON Data", "Markdown", "HTML")
    )

if __name__ == "__main__":
    example_usage()

