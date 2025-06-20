#!/usr/bin/env python3
"""
Example-based formatter showing exact desired output
"""

import os
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from book_cleaning.book_formatter_v2 import BookFormatterV2

class ExampleBasedFormatter(BookFormatterV2):
    def create_enhanced_formatting_prompt(self, config):
        """Create prompt with exact examples"""
        
        return '''You are formatting a French language textbook. Apply ONLY formatting, never change content.

EXAMPLE TRANSFORMATIONS:

INPUT:
```
Vous êtes français.
(statement)
Vous êtes français?
(question)
```

OUTPUT:
```
**Vous êtes français.** (statement)
**Vous êtes français?** (question)
```

INPUT:
```
Elle habite en Angleterre, à Coventry.
She lives in England, in Coventry.
```

OUTPUT:
```
**Elle _habite_ en Angleterre, à Coventry.**
She lives in England, in Coventry.
```

INPUT:
```
## Did you notice?
```

OUTPUT:
```
### Did you notice?
```

INPUT:
```
téléphoner to phone
```

OUTPUT:
```
**téléphoner** to phone
```

RULES:
1. French sentences: **bold** with _verb_ emphasis when followed by translation
2. English translations: plain text (not italics unless in source)
3. Grammatical terms in text: **bold**
4. Section headers: Use appropriate level (##, ###)
5. DO NOT add translations or content
6. Keep EXACT order from source
7. Preserve all CD references like (CD 1; 2)

Format this text using ONLY these patterns:'''


def main():
    # Check API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("❌ Please set MISTRAL_API_KEY environment variable")
        return
    
    # Test just page 20 first
    pdf_path = Path("Colloquial French 1.pdf").resolve()
    config_path = Path("smart_config.yaml").resolve()
    
    formatter = ExampleBasedFormatter(pdf_path, "./formatted_output")
    
    result = formatter.process_with_pipeline(
        mode="sample",
        start_page=20,
        end_page=20,  # Just one page to test
        config_path=str(config_path),
        preview=False
    )
    
    print(f"✅ Example-based result: {result}")

if __name__ == "__main__":
    main()