#!/usr/bin/env python3
"""
OCR correction for known issues in Colloquial French
"""

import re

def correct_exercise_numbering(text):
    """Fix exercise numbering that got scrambled by OCR"""
    
    # Pattern to find exercises with scrambled numbers
    exercise_pattern = r'(Exercise \d+.*?)(1.*?2.*?Now answer.*?5.*?6.*?3.*?4.*?7.*?8)'
    
    def fix_numbers(match):
        header = match.group(1)
        content = match.group(2)
        
        # Replace the scrambled numbers
        fixed = content
        fixed = re.sub(r'\n5 ', '\n1 ', fixed)
        fixed = re.sub(r'\n6 ', '\n2 ', fixed)
        fixed = re.sub(r'\n7 ', '\n3 ', fixed)
        fixed = re.sub(r'\n8 ', '\n4 ', fixed)
        
        return header + fixed
    
    return re.sub(exercise_pattern, fix_numbers, text, flags=re.DOTALL)

def add_proper_formatting(text):
    """Add formatting based on content patterns"""
    
    # French sentences followed by English translations
    pattern = r'((?:Elle|Il|Je|Tu|Nous|Vous|Ils|Elles) [^.]+\.)\n((?:She|He|I|You|We|They) [^.]+\.)'
    
    def format_translation(match):
        french = match.group(1)
        english = match.group(2)
        
        # Extract and emphasize the verb in French sentence
        verb_match = re.search(r' (habite|travaille|parle|est|suis|sont) ', french)
        if verb_match:
            verb = verb_match.group(1)
            french = french.replace(f' {verb} ', f' _{verb}_ ')
        
        return f'**{french}**\n_{english}_'
    
    text = re.sub(pattern, format_translation, text)
    
    # Bold grammatical terms
    terms = ['je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 
             '-er', 'habiter', 'travailler', 'parler', 'être']
    
    for term in terms:
        # Only bold when it's a standalone word
        text = re.sub(rf'\b({term})\b(?![*_])', r'**\1**', text, flags=re.IGNORECASE)
    
    return text

def correct_ocr_output(ocr_text):
    """Apply all OCR corrections"""
    
    # Fix exercise numbering
    text = correct_exercise_numbering(ocr_text)
    
    # Add proper formatting
    text = add_proper_formatting(text)
    
    # Fix section headers
    text = re.sub(r'^# Language points\s*\n\s*## (.*?)$', r'## Language points - \1', text, flags=re.MULTILINE)
    text = re.sub(r'^## (Did you notice\?|Giving more information)', r'### \1', text, flags=re.MULTILINE)
    
    return text