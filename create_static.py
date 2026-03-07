from pathlib import Path

BASE = Path(__file__).parent

# Create directories
for d in ['static/css', 'static/js', 'static/images']:
    (BASE / d).mkdir(parents=True, exist_ok=True)

# Create basic CSS
css = """
body { font-family: Arial; direction: rtl; margin: 0; padding: 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
header { background: #667eea; color: white; padding: 20px 0; }
nav a { color: white; text-decoration: none; padding: 10px 20px; }
.products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
.product-card { background: white; border-radius: 10px; padding: 20px; margin: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
footer { background: #1a1a2e; color: white; padding: 40px 0; margin-top: 50px; text-align: center; }
"""

(BASE / 'static/css/style.css').write_text(css, encoding='utf-8')

# Create basic JS
js = """
console.log('Static files loaded!');
"""

(BASE / 'static/js/main.js').write_text(js, encoding='utf-8')

print('✓ Static files created')
