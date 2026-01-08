
import os

# Option 1: Digital Banyan (Growth/Network)
svg_opt1 = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#11998e;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#38ef7d;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" fill="white" rx="20" />
  <path d="M90 180 L90 120 Q90 100 70 80 M110 180 L110 120 Q110 100 130 80" stroke="#333" stroke-width="8" fill="none" stroke-linecap="round"/>
  <g stroke="#11998e" stroke-width="3">
    <line x1="70" y1="80" x2="50" y2="60" />
    <line x1="70" y1="80" x2="90" y2="50" />
    <line x1="130" y1="80" x2="110" y2="50" />
    <line x1="130" y1="80" x2="150" y2="60" />
    <line x1="100" y1="120" x2="100" y2="40" stroke-width="2" stroke-dasharray="5,3"/>
  </g>
  <circle cx="50" cy="60" r="10" fill="url(#grad1)" />
  <circle cx="90" cy="50" r="12" fill="url(#grad1)" />
  <circle cx="110" cy="50" r="12" fill="url(#grad1)" />
  <circle cx="150" cy="60" r="10" fill="url(#grad1)" />
  <circle cx="100" cy="90" r="8" fill="url(#grad1)" />
  <text x="100" y="190" font-family="Arial" font-size="16" fill="#333" text-anchor="middle" font-weight="bold">GROWTH</text>
</svg>"""

# Option 2: The "V" Mind (Abstract/Modern)
svg_opt2 = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FF9966;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FF5E62;stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="100" cy="100" r="90" fill="#FFF5F0" />
  <path d="M50 70 L90 140 L160 50" fill="none" stroke="url(#grad2)" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="50" cy="70" r="8" fill="#333" />
  <circle cx="90" cy="140" r="8" fill="#333" />
  <circle cx="160" cy="50" r="8" fill="#333" />
  <path d="M160 50 Q180 80 170 110" fill="none" stroke="#FF5E62" stroke-width="4" stroke-dasharray="5,5" />
  <circle cx="170" cy="110" r="6" fill="#FF5E62" />
  <text x="100" y="180" font-family="Arial" font-size="16" fill="#FF5E62" text-anchor="middle" font-weight="bold">SUCCESS</text>
</svg>"""

# Option 3: Neuro-Coin (Wealth & Wisdom)
# Removed text Rupee symbol to check if encoding was the issue, replaced with path
svg_opt3 = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad3" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#00c6ff;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0072ff;stop-opacity:1" />
    </linearGradient>
  </defs>
  <path d="M100 20 L170 60 L170 140 L100 180 L30 140 L30 60 Z" fill="url(#grad3)" />
  <path d="M60 120 L80 90 L110 110 L140 70" fill="none" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="60" cy="120" r="5" fill="white"/>
  <circle cx="80" cy="90" r="5" fill="white"/>
  <circle cx="110" cy="110" r="5" fill="white"/>
  <circle cx="140" cy="70" r="5" fill="white"/>
  <!-- Rupee Symbol as Path to avoid text encoding issues -->
  <path d="M85 140 h30 M85 150 h30 M90 140 q0 15 10 15 t10 15 l-15 20" stroke="white" stroke-width="3" fill="none" transform="translate(0, 10)" opacity="0.5"/>
  <text x="100" y="195" font-family="Arial" font-size="12" fill="#0072ff" text-anchor="middle" font-weight="bold">INTELLIGENCE</text>
</svg>"""

with open("logo_opt1.svg", "w", encoding="utf-8") as f: f.write(svg_opt1)
with open("logo_opt2.svg", "w", encoding="utf-8") as f: f.write(svg_opt2)
with open("logo_opt3.svg", "w", encoding="utf-8") as f: f.write(svg_opt3)

print("Generated 3 logo options successfully.")
