**Zero-shot Prompt**



"""



You are an expert geolocation analyst, please predict the geolocation for the provided imagery with utmost precision.



Give the answer that strictly uses the following format in the same line: 


  1. LATITUDE: ; 2. LONGITUDE: ; 3. LOCATION: (the according city, country, and continent)



"""









**Cot Prompt**







"""



You are an expert geolocation analyst, please predict the geolocation for the provided imagery with utmost precision, using systematic, step-by-step, evidence-based reasoning.



Follow the following structured chain-of-thought process:



1: MACRO-GEOGRAPHIC \& ENVIRONMENTAL ANALYSIS



\*\*Climate \& Vegetation:\*\*

\- Describe the climate zone (tropical, temperate, arid, continental, polar)

\- Analyze vegetation types (deciduous, coniferous, tropical, desert, tundra)

\- Note any distinctive plant species or patterns



\*\*Topography \& Landscape:\*\*

\- Describe the terrain (flat, hilly, mountainous, coastal)

\- Identify any water bodies, rock formations, or natural landmarks

\- Note elevation clues from vegetation zones or atmospheric conditions



\*\*Seasonal \& Atmospheric Clues:\*\*

\- Determine season from foliage, weather conditions, shadows

\- Analyze sun position and shadow directions for hemisphere clues

\- Note any unique atmospheric conditions



\*\*Initial Regional Hypotheses:\*\*

Based on above, which continents/regions are possible?

\- Primary hypothesis: 

\- Secondary possibilities: 

\- Eliminated regions: 



2: CULTURAL \& HUMAN-MADE FEATURES ANALYSIS



\*\*Architectural Style:\*\*

\- Building materials (wood, brick, concrete, adobe, glass)

\- Roof types (flat, pitched, tiled, thatched, metal)

\- Window styles, balconies, decorative elements

\- Overall architectural era and influences



\*\*Infrastructure \& Transportation:\*\*

\- Road design, markings, and signage

\- Vehicle types and models (note license plates if visible)

\- Sidewalk design, utility poles, street lighting

\- Public transportation infrastructure



\*\*Language \& Writing Systems:\*\*

\- Identify visible text on signages, advertisements, buildings

\- Determine language and script (Latin, Cyrillic, Arabic, Chinese, etc.)

\- Note specific words that might indicate location names or businesses



\*\*Initial Country/City Hypotheses:\*\*

Based on above, which specific countries/cities become likely?

\- Primary hypothesis: 

\- Supporting evidence: 

\- Alternative possibilities: 



3: SPECIFIC IDENTIFIERS \& UNIQUE FEATURES



\*\*Landmarks \& Notable Structures:

\- Identify any recognizable landmarks, monuments, or unique buildings

\- Note distinctive bridges, towers, or public spaces



Commercial \& Brand Indicators:

\- Store names, restaurant chains, brand logos, chain stores

\- Vehicle dealerships or specific car models common to regions

\- Fast food chains, supermarket brands, coffee shops, convenience stores, gas stations



Regulatory \& Government Signs:

\- Traffic signs design and colour schemes

\- License plate designs and formats

\- Government signage or official building markings



\*\*Natural \& Cultural Specificity:\*\*

\- Unique tree species, flower types, or agricultural patterns

\- Cultural elements (flags, traditional clothing, religious symbols)



STEP 4: SYNTHESIS \& PRECISE PREDICTION



Evidence Integration: 

\- Cross-reference all clues from Steps 1-3

\- Resolve any contradictory evidence

\- Identify the strongest, most location-specific indicators



\*\*Confidence Assessment:\*\*

\- High confidence: Multiple strong, specific indicators align

\- Medium confidence: General regional fit with some specific clues  

\- Low confidence: Only broad regional indicators available



You must ONLY directly give the following answer that strictly uses this format in one single line: 

&#x09;

1\. LATITUDE:  ; 2. LONGITUDE: ;3. LOCATION: (the according city, country, and continent, strictly the three only); 4. REASONING: 





"""

