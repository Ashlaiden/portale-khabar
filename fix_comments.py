"""
One-off script: convert multi-line {# ... #} Django comments to
{% comment %}...{% endcomment %} blocks so they don't leak into rendered HTML.

Django's {# #} syntax only works for SINGLE-LINE comments. Multi-line
{# #} blocks are treated as literal text and appear in the output.
"""
import os
import re

TEMPLATE_DIRS = [
    'templates',
    'apps/news/templates',
    'apps/interactions/templates',
    'apps/pages/templates',
]

# Match a {# ... #} block that spans multiple lines (contains at least one \n).
# Using DOTALL so . matches newlines.
PATTERN = re.compile(r'\{#(.*?)#\}', re.DOTALL)

def convert(content):
    """Convert multi-line {# #} comments to {% comment %} blocks."""
    def replacer(m):
        inner = m.group(1)
        if '\n' in inner:
            # Multi-line: use {% comment %} block.
            return '{% comment %}' + inner + '{% endcomment %}'
        # Single-line: keep as-is (works fine).
        return m.group(0)
    return PATTERN.sub(replacer, content)

def main():
    changed = []
    for d in TEMPLATE_DIRS:
        if not os.path.isdir(d):
            continue
        for root, dirs, files in os.walk(d):
            for fn in files:
                if not fn.endswith('.html'):
                    continue
                path = os.path.join(root, fn)
                with open(path, 'r', encoding='utf-8') as f:
                    original = f.read()
                converted = convert(original)
                if converted != original:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(converted)
                    changed.append(path)
    print(f'Converted {len(changed)} file(s):')
    for p in changed:
        print(f'  {p}')

if __name__ == '__main__':
    main()
