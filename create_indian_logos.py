
import os

# Option 1: Diya Growth (The Light of Profit)
# A simplified Diya lamp where the flame is a rising graph.
# Colors: Saffron (Warmth/Trust) + Gold.
svg_diya = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradDiya" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#FF9933;stop-opacity:1" /> <!-- Saffron -->
      <stop offset="100%" style="stop-color:#FF512F;stop-opacity:1" /> <!-- Deep Orange -->
    </linearGradient>
    <linearGradient id="gradFlame" x1="0%" y1="100%" x2="0%" y2="0%">
      <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FFF700;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="200" height="200" fill="white" rx="30" />
  
  <!-- Diya Base (The Business Foundation) -->
  <path d="M50 120 Q100 170 150 120" fill="url(#gradDiya)" stroke="none" />
  <path d="M50 120 L150 120" stroke="#800000" stroke-width="2" />
  
  <!-- The Flame (Rising Graph) -->
  <path d="M100 120 Q80 80 100 40 Q120 80 100 120" fill="url(#gradFlame)" />
  
  <!-- Graph Bars inside Flame (Subtle) -->
  <rect x="90" y="80" width="5" height="40" fill="#cc3300" opacity="0.2"/>
  <rect x="98" y="70" width="5" height="50" fill="#cc3300" opacity="0.2"/>
  <rect x="106" y="60" width="5" height="60" fill="#cc3300" opacity="0.2"/>

  <text x="100" y="180" font-family="Arial" font-size="16" fill="#800000" text-anchor="middle" font-weight="bold">SHUBH LABH</text>
</svg>"""

# Option 2: Lotus Wealth (Lakshmi/Prosperity)
# A geometric lotus.
svg_lotus = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradLotus" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#ec008c;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#fc6767;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="200" height="200" fill="#FFF0F5" rx="30" />
  
  <!-- Center Petal -->
  <path d="M100 140 Q60 100 100 40 Q140 100 100 140" fill="url(#gradLotus)" />
  
  <!-- Side Petals -->
  <path d="M100 140 Q60 120 40 80 Q70 100 100 140" fill="url(#gradLotus)" opacity="0.8"/>
  <path d="M100 140 Q140 120 160 80 Q130 100 100 140" fill="url(#gradLotus)" opacity="0.8"/>
  
  <!-- Rupee Coin in Center -->
  <circle cx="100" cy="110" r="15" fill="#FFD700" stroke="#cc9900" stroke-width="2"/>
  <!-- Rupee Simple Path -->
  <path d="M95 105 h10 M95 108 h10 M95 105 q0 5 5 5 t5 5 l-8 8" stroke="#cc9900" stroke-width="2" fill="none" transform="translate(0, -2)"/>

  <text x="100" y="180" font-family="Arial" font-size="16" fill="#cc3300" text-anchor="middle" font-weight="bold">PROSPERITY</text>
</svg>"""

# Option 3: The Golden Kalash (Traditional Store)
# A pot with coconut -> The classic opening ceremony symbol.
svg_kalash = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gradPot" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#d4af37;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#C5796D;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="200" height="200" fill="#FFFFF0" rx="30" />
  
  <!-- Pot Body -->
  <circle cx="100" cy="130" r="40" fill="url(#gradPot)" />
  <rect x="80" y="80" width="40" height="20" fill="url(#gradPot)" />
  
  <!-- Mango Leaves -->
  <path d="M80 90 Q60 60 80 50 Q90 70 80 90" fill="#228B22" />
  <path d="M120 90 Q140 60 120 50 Q110 70 120 90" fill="#228B22" />
  
  <!-- Coconut -->
  <circle cx="100" cy="55" r="15" fill="#8B4513" />
  
  <!-- Swastik/Symbol on Pot -->
  <path d="M95 130 h10 M100 125 v10" stroke="#800000" stroke-width="3" stroke-linecap="round"/>

  <text x="100" y="190" font-family="Arial" font-size="14" fill="#8B4513" text-anchor="middle" font-weight="bold">VYAPAR</text>
</svg>"""

with open("logo_diya.svg", "w", encoding="utf-8") as f: f.write(svg_diya)
with open("logo_lotus.svg", "w", encoding="utf-8") as f: f.write(svg_lotus)
with open("logo_kalash.svg", "w", encoding="utf-8") as f: f.write(svg_kalash)

print("Generated 3 Indian Retail logo options.")
