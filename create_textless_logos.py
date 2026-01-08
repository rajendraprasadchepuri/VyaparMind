
import os

# Common Gradients
defs = """
  <defs>
    <linearGradient id="gradRoyal" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#004e92;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#000428;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="gradGold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#daa520;stop-opacity:1" />
    </linearGradient>
     <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
      <feOffset dx="1" dy="1" result="offsetblur"/>
      <feComponentTransfer>
        <feFuncA type="linear" slope="0.3"/>
      </feComponentTransfer>
      <feMerge> 
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/> 
      </feMerge>
    </filter>
  </defs>
"""

# Option 1: The Neural Coin (Pure Symbol)
# Focus: Wealth + Intelligence.
svg_opt1 = f"""<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  {defs}
  <rect width="200" height="200" fill="white" rx="40" />
  
  <g transform="translate(100, 100)" filter="url(#shadow)">
    <!-- Outer Ring -->
    <circle cx="0" cy="0" r="70" fill="none" stroke="url(#gradGold)" stroke-width="6" />
    
    <!-- Central Brain/Chakra Hub -->
    <circle cx="0" cy="0" r="15" fill="url(#gradRoyal)" />
    
    <!-- Radiating Nodes (The Research Network) -->
    <circle cx="0" cy="-45" r="8" fill="#004e92" />
    <circle cx="0" cy="45" r="8" fill="#004e92" />
    <circle cx="-45" cy="0" r="8" fill="#004e92" />
    <circle cx="45" cy="0" r="8" fill="#004e92" />
    
    <!-- Connections -->
    <path d="M0 -15 L0 -45" stroke="#daa520" stroke-width="3" />
    <path d="M0 15 L0 45" stroke="#daa520" stroke-width="3" />
    <path d="M-15 0 L-45 0" stroke="#daa520" stroke-width="3" />
    <path d="M15 0 L45 0" stroke="#daa520" stroke-width="3" />
    
    <!-- Orbital Rings -->
    <circle cx="0" cy="0" r="45" fill="none" stroke="#004e92" stroke-width="1.5" opacity="0.5"/>
  </g>
</svg>"""

# Option 2: Digital Rangoli (Complexity/Research)
# Focus: Traditional Pattern + Data Nodes.
svg_opt2 = f"""<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  {defs}
  <rect width="200" height="200" fill="white" rx="40" />
  
  <g transform="translate(100, 100)">
    <!-- Square Diamonds (Rangoli Style) -->
    <rect x="-50" y="-50" width="100" height="100" fill="none" stroke="url(#gradRoyal)" stroke-width="2" transform="rotate(45)" />
    <rect x="-35" y="-35" width="70" height="70" fill="none" stroke="url(#gradGold)" stroke-width="2" />
    
    <!-- Corner Dots -->
    <circle cx="0" cy="-70" r="6" fill="#daa520" />
    <circle cx="0" cy="70" r="6" fill="#daa520" />
    <circle cx="-70" cy="0" r="6" fill="#daa520" />
    <circle cx="70" cy="0" r="6" fill="#daa520" />
    
    <!-- Center Core -->
    <rect x="-10" y="-10" width="20" height="20" fill="#004e92" transform="rotate(45)" />
    
    <!-- Diagonal Lines -->
    <line x1="-70" y1="0" x2="70" y2="0" stroke="#004e92" stroke-width="1" opacity="0.3"/>
    <line x1="0" y1="-70" x2="0" y2="70" stroke="#004e92" stroke-width="1" opacity="0.3"/>
  </g>
</svg>"""

# Option 3: The Ascending Lotus (Growth/Purity)
# Focus: Minimalist curves.
svg_opt3 = f"""<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  {defs}
  <rect width="200" height="200" fill="white" rx="40" />
  
  <g transform="translate(100, 120)">
    <!-- Central Petal (High Growth) -->
    <path d="M0 40 Q-20 0 0 -60 Q20 0 0 40" fill="url(#gradRoyal)" stroke="white" stroke-width="2"/>
    
    <!-- Side Petals (Support) -->
    <path d="M0 40 Q-40 20 -50 -20 Q-20 0 0 40" fill="url(#gradGold)" stroke="white" stroke-width="2"/>
    <path d="M0 40 Q40 20 50 -20 Q20 0 0 40" fill="url(#gradGold)" stroke="white" stroke-width="2"/>
    
    <!-- Base -->
    <circle cx="0" cy="40" r="10" fill="#000428" />
  </g>
</svg>"""

with open("logo_no_text_1.svg", "w", encoding="utf-8") as f: f.write(svg_opt1)
with open("logo_no_text_2.svg", "w", encoding="utf-8") as f: f.write(svg_opt2)
with open("logo_no_text_3.svg", "w", encoding="utf-8") as f: f.write(svg_opt3)

print("Generated 3 Text-Free options.")
