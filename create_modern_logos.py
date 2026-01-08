
import os

# Ultra Modern Concept 1: The "Flux" (Gradient Mesh style)
svg_modern1 = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="fluxGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <rect width="200" height="200" fill="#1a1a1a" rx="40" />
  
  <!-- Abstract V Shape made of flowing lines -->
  <path d="M60 60 Q100 200 140 60" fill="none" stroke="url(#fluxGrad)" stroke-width="12" stroke-linecap="round" filter="url(#glow)"/>
  <path d="M60 80 Q100 220 140 80" fill="none" stroke="url(#fluxGrad)" stroke-width="6" stroke-opacity="0.5" stroke-linecap="round"/>
  
  <circle cx="100" cy="130" r="10" fill="#fff" filter="url(#glow)" />
  
  <text x="100" y="180" font-family="'Segoe UI', sans-serif" font-size="14" fill="#ccc" text-anchor="middle" letter-spacing="2">FLUX</text>
</svg>"""

# Ultra Modern Concept 2: The "Nexus" (Dark Mode Glassmorphism)
svg_modern2 = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="glassGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.2" />
      <stop offset="100%" style="stop-color:#ffffff;stop-opacity:0.05" />
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#f093fb;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f5576c;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- Dark Background -->
  <rect width="200" height="200" fill="#0f0f13" rx="40" />
  
  <!-- Hexagon Glass Layer -->
  <path d="M100 30 L160 65 L160 135 L100 170 L40 135 L40 65 Z" fill="url(#glassGrad)" stroke="white" stroke-width="0.5" />
  
  <!-- Inner "Brain" Circuitry -->
  <path d="M100 100 L100 60" stroke="url(#accent)" stroke-width="4" stroke-linecap="round"/>
  <path d="M100 100 L135 120" stroke="url(#accent)" stroke-width="4" stroke-linecap="round"/>
  <path d="M100 100 L65 120" stroke="url(#accent)" stroke-width="4" stroke-linecap="round"/>
  
  <circle cx="100" cy="100" r="8" fill="#fff" />
  <circle cx="100" cy="60" r="5" fill="#f5576c" />
  <circle cx="135" cy="120" r="5" fill="#f5576c" />
  <circle cx="65" cy="120" r="5" fill="#f5576c" />

  <text x="100" y="185" font-family="'Segoe UI', sans-serif" font-size="12" fill="#888" text-anchor="middle" letter-spacing="1">NEXUS</text>
</svg>"""

# Ultra Modern Concept 3: The "Cube" (Isometric 3D)
svg_modern3 = """<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="face1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#43e97b;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#38f9d7;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="face2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#38f9d7;stop-opacity:0.8" />
      <stop offset="100%" style="stop-color:#11998e;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="200" height="200" fill="#f8f9fa" rx="40" />
  
  <!-- Isometric Cube -->
  <path d="M100 40 L160 70 L100 100 L40 70 Z" fill="url(#face1)" />
  <path d="M40 70 L100 100 L100 170 L40 140 Z" fill="url(#face2)" />
  <path d="M160 70 L160 140 L100 170 L100 100 Z" fill="#11998e" />
  
  <!-- White highlight (Brain logic) -->
  <path d="M100 100 L100 140" stroke="white" stroke-width="4" stroke-linecap="round" opacity="0.5"/>
  <path d="M100 100 L140 80" stroke="white" stroke-width="4" stroke-linecap="round" opacity="0.5"/>
  <path d="M100 100 L60 80" stroke="white" stroke-width="4" stroke-linecap="round" opacity="0.5"/>

  <text x="100" y="190" font-family="'Segoe UI', sans-serif" font-size="14" fill="#333" text-anchor="middle" font-weight="900">CORE</text>
</svg>"""

with open("logo_flux.svg", "w", encoding="utf-8") as f: f.write(svg_modern1)
with open("logo_nexus.svg", "w", encoding="utf-8") as f: f.write(svg_modern2)
with open("logo_core.svg", "w", encoding="utf-8") as f: f.write(svg_modern3)

print("Generated 3 Modern logo options.")
