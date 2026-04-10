#!/usr/bin/env python3
"""Auto-convert remaining HTML templates to dark theme"""

import os
import re

# Color mapping for light to dark theme
replacements = [
    # Background colors
    ('bg-white', 'bg-slate-900'),
    ('bg-gray-50', 'bg-slate-800'),
    ('bg-gray-100', 'bg-slate-800'),
    ('bg-gray-200', 'bg-slate-700'),
    ('bg-blue-50', 'bg-slate-800/40'),
    ('bg-purple-50', 'bg-slate-800/40'),
    ('bg-green-50', 'bg-slate-800/40'),
    
    # Text colors
    ('text-gray-900', 'text-slate-100'),
    ('text-gray-800', 'text-slate-200'),
    ('text-gray-700', 'text-slate-300'),
    ('text-gray-600', 'text-slate-400'),
    ('text-gray-500', 'text-slate-500'),
    ('text-gray-400', 'text-slate-600'),
    
    # Border colors
    ('border-gray-200', 'border-slate-700'),
    ('border-gray-300', 'border-slate-700'),
    ('border-gray-400', 'border-slate-600'),
    ('border-blue-300', 'border-slate-600'),
    
    # Focus styles
    ('focus:ring-blue-500', 'focus:ring-primary'),
    ('focus:ring-blue-500 focus:border-transparent', 'focus:ring-primary focus:border-slate-700'),
    
    # Shadow hover
    ('hover:shadow-md', 'hover:shadow-lg hover:border-slate-600 hover:bg-slate-800'),
    ('hover:bg-gray-200', 'hover:bg-slate-800'),
    ('hover:bg-gray-300', 'hover:bg-slate-700'),
    ('hover:text-gray-600', 'hover:text-slate-300'),
    ('hover:bg-blue-50', 'hover:bg-slate-800/50 hover:bg-opacity-20'),
    ('hover:bg-red-50', 'hover:bg-slate-800/50 hover:bg-opacity-20'),
    
    # Placeholder
    ('placeholder-gray-400', 'placeholder-slate-500'),
]

def convert_file(filepath):
    """Convert a file to dark theme"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for light, dark in replacements:
            content = content.replace(light, dark)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Converted: {filepath}")
            return True
        else:
            print(f"- No changes: {filepath}")
            return False
    except Exception as e:
        print(f"✗ Error: {filepath} - {e}")
        return False

# Convert all template files
template_dir = 'd:\\Policia\\Projects\\expweb\\templates'
for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        convert_file(filepath)

print("\n✅ Dark theme conversion complete!")
