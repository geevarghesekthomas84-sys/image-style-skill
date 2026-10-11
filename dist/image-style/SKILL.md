---
name: image-style
description: Slash-command style modifiers for AI image generation. Use whenever the user writes an image/picture/photo/art request containing slash tokens such as /8k /cinematic /goldenhour /droneview /macro /cyberpunk /oilpainting /chiaroscuro (any of 362 style tokens), aspect ratios (/16:9 /9:16 /square), avoid-commands (/clean /nodeform) or a target model (/mj /sd /flux /dalle /gemini), or asks for /styles. Expands each token into precise prompt language, composes one final prompt, and generates the image.
---

# Image Style Modifiers (362 style + 10 aspect + 8 negative + 8 model commands)

## How it works

The user writes an image request and adds one or more slash modifiers, e.g.
`a lone lighthouse /storm /dramaticlighting /8k /wideangle`.

0. **Plain English works too.** If the user writes no slashes ("Create me a cinematic album double exposure, size 16:9 and 9:16"),
   treat style words/phrases that match a command name (cinematic, double exposure, golden hour, 8k...) and ratios (16:9, 9:16) as
   those commands, remove them from the subject, and drop filler ("create me a", "size", "ratio", "frame", "both"). Do not treat
   ordinary subject words (forest, space, rain, beach) as styles unless written with a slash. Several ratios = one prompt per ratio.
1. **Extract** every `/token` from the message. Normalize: lowercase, remove spaces, hyphens and
   underscores (`/Rule Of Thirds`, `/rule-of-thirds` → `ruleofthirds`; `/freeezeaction` → `freezeaction`).
2. **Look up** each token in the table below. Unknown token → treat it as free text (keep the word,
   don't invent a meaning) and mention it in one short line.
3. **Strip** the tokens from the subject text; what remains is the *subject*. If no subject is given
   but a previous image prompt exists in the conversation, reuse that subject.
4. **Compose** one final prompt: `subject, <modifier phrases in order given>`.
   - Put the subject first, then camera/angle, then lighting/weather, then style/color/quality last.
   - If two modifiers conflict (e.g. `/blackandwhite` + `/vibrantcolors`, `/highkeylighting` + `/lowkeylighting`),
     keep the one that appears **last** and say which was dropped.
   - **Cap at 8 style modifiers** (reference commands don't count). Models ignore long stacks. If more are given, keep subject, genre/style, angle, camera, light first and drop quality/era/color extras last; say what was dropped.
   - **One winner per slot:** resolution (/hdreal /4k /8k /8ktextures), realism (/photorealistic /hyperrealistic /ultrarealistic /rawphoto), focal length (/14mm../200mm) and aperture (/f1.4 /f2.8 /f8): keep the last given.
   - Deduplicate overlapping phrases (`/8k` + `/4k` → keep the last resolution).
5. **Generate**: if an image-generation tool is available, call it with the composed prompt.
   Otherwise output the composed prompt in a code block, ready to paste into an image model.
   Always show the final prompt used.
6. If the user sends only modifiers with no subject and no prior prompt, ask what to draw.
7. Camera/lens commands (/85mm /f1.4 /tiltshift) matter more for realism than style words. Motion commands (/dolly /orbit /handheld /slowmotion) are for video tools (Kling, Flow); for a still image ignore them and say so.
8. **Subject controls** (category `subject`: /age30s /smile /walking /suit /longhair ...) describe the person and are placed right after the subject. One winner per group: age, expression, pose, gaze (/lookingatcamera vs /lookingaway), hair length.
9. **Reference commands** (/sameface /samestyle /samepose /samecomposition /samecolors /samelighting) need a reference image the user attached or linked. If none is present, ask for one. Midjourney: /sameface -> `--cref <url>`, /samestyle -> `--sref <url>`; other tools: say "use the attached reference". Only use reference images the user owns or has permission to use; never use them to imitate a private person without consent.
10. `/styles` or `/modifiers` → list the available categories (and a category's tokens if named).

Do not add extra creative elements the user didn't ask for; modifiers only change *how* the image
looks, never *what* is in it.

## Modifier table

### quality

- `/hdreal` → HD, true-to-life realism, clean sharp detail
- `/4k` → 4K resolution, ultra-sharp detail
- `/8k` → 8K resolution, extreme fine detail
- `/cinematic` → cinematic look, movie-still composition, filmic lighting and color
- `/ultrarealistic` → ultra-realistic, indistinguishable from a real photograph
- `/photorealistic` → photorealistic, true-to-life
- `/hyperrealistic` → hyperrealistic, extreme lifelike detail beyond normal photography
- `/rawphoto` → RAW photo, unprocessed natural capture, realistic sensor look
- `/professionalphotography` → professional photography, expert composition, lighting and exposure
- `/8ktextures` → 8K textures, intricate surface detail
- `/highdetail` → highly detailed, intricate fine details
- `/sharpfocus` → tack-sharp focus on the subject
- `/crispdetails` → crisp, clean, well-defined details

### angle

- `/droneview` → drone view, elevated aerial vantage point looking down at the scene
- `/topdown` → top-down view, camera directly overhead looking straight down
- `/highangle` → high-angle shot, camera above subject looking down
- `/lowangle` → low-angle shot, camera below subject looking up, imposing perspective
- `/sideview` → side view, profile perspective
- `/aerialview` → aerial view from high altitude, wide sweeping scene
- `/closeup` → close-up shot, subject fills the frame
- `/extremecloseup` → extreme close-up, tiny details filling the frame
- `/wideangle` → wide-angle lens, expansive field of view
- `/fisheye` → fisheye lens, strong barrel distortion, ultra-wide curved view
- `/pov` → first-person point-of-view shot
- `/overtheshoulder` → over-the-shoulder shot, foreground shoulder framing the subject
- `/birdseyeview` → bird's-eye view, high overhead perspective
- `/wormseyeview` → worm's-eye view, from ground level looking steeply up

### weather

- `/fog` → thick atmospheric fog, low visibility, soft diffused depth
- `/mist` → light drifting mist, soft hazy atmosphere
- `/rainynight` → rainy night, wet reflective surfaces, glowing lights in rain
- `/rain` → steady rainfall, wet surfaces, raindrops
- `/storm` → violent storm, dark roiling clouds, lightning, wind
- `/snow` → falling snow, snow-covered surfaces, cold winter air

### light

- `/sunset` → sunset, warm orange-pink sky, low sun
- `/sunrise` → sunrise, soft early light, gentle warm horizon glow
- `/goldenhour` → golden hour, warm low-angle sunlight, long soft shadows
- `/bluehour` → blue hour, deep blue twilight, cool ambient glow
- `/moonlight` → moonlit scene, cool silvery light, deep night shadows
- `/neonlights` → vivid neon lights, glowing signs, colorful light spill
- `/darkmoody` → dark and moody, deep shadows, low-key brooding atmosphere
- `/softlighting` → soft diffused lighting, gentle shadows, flattering glow
- `/dramaticlighting` → dramatic lighting, strong contrast between light and shadow
- `/rimlight` → rim light outlining the subject's edges
- `/backlight` → backlit subject, glowing edges, light from behind
- `/godrays` → god rays, visible beams of light through atmosphere
- `/volumetriclight` → volumetric lighting, light beams in hazy air
- `/studio` → professional studio setup, controlled lighting, clean backdrop
- `/underwatercaustics` → underwater caustics, dancing light patterns
- `/sunbeams` → sunbeams streaming through gaps
- `/moonbeam` → moonbeam, silvery shaft of moonlight
- `/candlelight` → candlelit, warm flickering glow
- `/firelight` → firelit, warm orange flickering light
- `/neonrimlight` → neon rim light, colorful glowing edge light
- `/practicallighting` → practical lighting from in-scene lamps and fixtures
- `/threepointlighting` → three-point lighting, key, fill and back light
- `/chiaroscuro` → chiaroscuro, strong light-dark contrast, Renaissance drama
- `/butterflylighting` → butterfly lighting, light from above front, shadow under the nose
- `/rembrandtlighting` → Rembrandt lighting, triangle of light on the cheek
- `/splitlighting` → split lighting, half the face lit, half in shadow
- `/looplighting` → loop lighting, small nose shadow on the cheek
- `/clamshelllighting` → clamshell lighting, soft light from above and below
- `/highkeylighting` → high-key lighting, bright, minimal shadows
- `/lowkeylighting` → low-key lighting, dark, dominant shadows
- `/silkylighting` → silky smooth lighting, gentle gradient transitions
- `/ambientlighting` → ambient lighting, even natural environmental light
- `/naturalwindowlight` → natural window light, soft directional daylight
- `/overcastlighting` → overcast lighting, soft even cloud-diffused light

### style

- `/cyberpunk` → cyberpunk, neon-drenched dystopian city, high-tech low-life, rain and holograms
- `/oldmoney` → old money aesthetic, understated heritage elegance, classic tailoring, refined interiors
- `/luxury` → luxury, opulent materials, premium high-end finish
- `/minimalist` → minimalist, clean composition, few elements, lots of space
- `/editorial` → editorial photography, polished magazine-style composition
- `/fashion` → high-fashion photography, styled wardrobe, runway-grade polish
- `/streetstyle` → street style photography, candid urban fashion
- `/magazinecover` → magazine cover layout, strong hero subject, space for masthead and headlines
- `/noir` → film noir, high-contrast black and white, hard shadows, moody
- `/detective` → hard-boiled detective vibe, trench coat, smoky office, rainy streets
- `/samurai` → samurai, feudal Japan, traditional armor and katana
- `/medieval` → medieval setting, castles, stone, period clothing
- `/superhero` → superhero, heroic pose, dynamic cape and costume, comic-epic lighting
- `/dreamcore` → dreamcore, surreal nostalgic liminal dreamlike atmosphere, soft haze

### lens

- `/filmgrain` → visible film grain, analog texture
- `/anamorphic` → anamorphic lens, widescreen cinematic framing, horizontal flares, oval bokeh
- `/bokeh` → beautiful bokeh, creamy out-of-focus highlights
- `/shallowdepth` → shallow depth of field, sharp subject, blurred background
- `/motionblur` → motion blur, sense of speed and movement
- `/longexposure` → long exposure, light streaks, smooth flowing water or motion trails
- `/freezeaction` → high-speed capture, frozen action mid-motion, crisp detail
- `/softfocus` → soft focus, dreamy gentle blur
- `/lensflare` → lens flare, streaks of light across the frame
- `/sunflare` → sun flare, bright sun starburst and glow
- `/chromaticaberration` → chromatic aberration, color fringing at edges
- `/halation` → halation, red-orange glow bleeding around bright highlights

### era

- `/vintage` → vintage aesthetic, aged look, muted nostalgic tones
- `/retro` → retro style, throwback design and colors

### film

- `/polaroid` → Polaroid instant photo look, white border, soft faded colors
- `/disposablecamera` → disposable camera snapshot, direct flash, grainy, imperfect candid
- `/35mmfilm` → shot on 35mm film, natural grain, organic color
- `/instantphoto` → instant photo, soft focus, washed colors, nostalgic frame

### scene

- `/underwater` → underwater scene, light rays from the surface, floating particles, blue-green tint
- `/space` → outer space, stars, deep cosmic void
- `/desert` → vast desert, dunes, arid light, heat haze
- `/forest` → dense forest, tall trees, dappled light
- `/mountains` → majestic mountain range, rugged peaks, epic scale
- `/beach` → sandy beach, ocean waves, coastal light
- `/futuristic` → futuristic design, advanced technology, sleek forms
- `/fantasy` → fantasy world, magical, epic imaginative setting
- `/scifi` → science fiction, advanced technology, otherworldly design
- `/nightcity` → city at night, lit windows, streetlights, urban glow
- `/postapocalyptic` → post-apocalyptic wasteland, ruins, overgrown decay, survival gear
- `/cityscape` → sweeping cityscape, skyline, dense architecture
- `/floatingcity` → floating city, structures suspended in the sky
- `/undergroundcity` → underground city, vast cavern metropolis
- `/spacecolony` → space colony, habitats on a distant world or orbit
- `/alienplanet` → alien planet, otherworldly terrain and sky
- `/robotics` → advanced robotics, mechanical joints, precision machines
- `/mechdesign` → mech design, giant armored piloted robot, hard-surface detail
- `/cybernetic` → cybernetic, human-machine fusion, implants
- `/technologicaldystopia` → technological dystopia, oppressive surveillance tech, grim megacity

### material

- `/glassart` → glass art, translucent refractive forms, light passing through glass
- `/chrome` → polished chrome, mirror-like metallic reflections
- `/holographic` → holographic, iridescent shifting rainbow foil sheen
- `/glassmorphism` → glassmorphism, frosted translucent panels, blur, soft light borders
- `/neumorphism` → neumorphism, soft extruded shapes, subtle inner and outer shadows
- `/metallic` → metallic surfaces, shiny reflective metal
- `/iridescent` → iridescent, color-shifting pearlescent sheen
- `/translucent` → translucent materials, light passing softly through
- `/crystalline` → crystalline, faceted crystals, refractive
- `/liquidmetal` → liquid metal, flowing mercury-like chrome

### technique

- `/doubleexposure` → double exposure, two images blended and overlaid
- `/silhouette` → silhouette, dark subject shape against bright background
- `/reflection` → prominent reflections, mirrored surfaces or water
- `/mirror` → mirror reflection, symmetrical mirrored composition

### effect

- `/fire` → flames, fire, fiery orange glow
- `/smoke` → swirling smoke, wispy atmospheric plumes
- `/glitch` → digital glitch, RGB split, scan-line distortion
- `/bioluminescent` → bioluminescent, glowing organisms, soft blue-green light in darkness
- `/glowingeffects` → glowing effects, luminous halos
- `/particles` → floating particles, drifting dust and motes
- `/embers` → glowing embers drifting upward
- `/sparks` → flying sparks, bright points of light
- `/energywaves` → energy waves, radiating pulses of power
- `/lighttrails` → light trails, streaking glowing paths
- `/electricity` → electric arcs, crackling lightning bolts
- `/plasma` → plasma, glowing ionized flowing energy
- `/magicalglow` → magical glow, enchanted luminous aura
- `/rainbow` → rainbow, full-spectrum arc of color
- `/aurora` → aurora, shimmering green and violet ribbons of light
- `/stardust` → stardust, sparkling cosmic glitter

### color

- `/naturalcolors` → natural, true-to-life color
- `/colorgraded` → professionally color graded, cohesive palette
- `/cinematiccolorgrading` → cinematic color grading, filmic contrast and palette
- `/tealandorange` → teal and orange color grade
- `/monochrome` → monochrome, single-hue palette
- `/blackandwhite` → black and white, rich tonal range
- `/desaturated` → desaturated, muted subdued colors
- `/pastelcolors` → soft pastel color palette
- `/vibrantcolors` → vibrant saturated colors
- `/duotone` → duotone, two-color palette
- `/colorpop` → selective color pop against muted surroundings
- `/warmtones` → warm tones, golden amber hues
- `/cooltones` → cool tones, blue-teal hues
- `/highcontrast` → high contrast, deep blacks and bright highlights
- `/lowcontrast` → low contrast, soft flat tonal range
- `/overexposed` → overexposed, blown-out bright highlights, washed light
- `/underexposed` → underexposed, dark crushed shadows, dim mood

### portrait

- `/portrait` → portrait photograph, subject-centered, flattering framing
- `/headshot` → professional headshot, head and shoulders
- `/fullbody` → full-body shot, head to toe in frame
- `/halfbody` → half-body shot, waist up
- `/profileportrait` → profile portrait, side-facing head shot
- `/candid` → candid, unposed natural moment
- `/beautyshot` → beauty shot, flawless skin detail, polished lighting
- `/environmentalportrait` → environmental portrait, subject shown in their meaningful surroundings
- `/groupportrait` → group portrait, multiple people arranged naturally
- `/facialdetail` → detailed face, visible skin texture, realistic eyes

### macro

- `/macro` → macro photography, extreme magnification
- `/macrophoto` → macro photo, close-focus fine detail
- `/microscopic` → microscopic view, cellular-scale detail
- `/productmacro` → product macro, extreme close-up of materials and craftsmanship
- `/texturestudy` → texture study, close look at surface patterns
- `/abstractmacro` → abstract macro, close-up forms and colors
- `/naturemacro` → nature macro, petals, leaves, dew in fine detail
- `/insectmacro` → insect macro, compound eyes, hairs, wings in detail
- `/eyedetail` → detailed eye close-up, iris texture, reflections
- `/waterdroplets` → water droplets, glistening beads, refraction

### genre

- `/productphotography` → product photography, clean hero shot, clean background, commercial lighting
- `/commercialphotography` → commercial photography, polished advertising quality
- `/foodphotography` → food photography, appetizing, styled plating, fresh textures
- `/architecturalphotography` → architectural photography, clean lines, precise perspective
- `/automotivephotography` → automotive photography, sleek car, glossy reflections, dynamic angle
- `/jewelryphotography` → jewelry photography, sparkling gems, precise lighting, macro detail
- `/watchphotography` → watch photography, crisp dial detail, metallic reflections
- `/cosmeticphotography` → cosmetic photography, glossy products, clean luxury styling
- `/realestatephotography` → real estate photography, bright wide interiors, straight verticals
- `/travelphotography` → travel photography, evocative destination scene, authentic atmosphere
- `/streetphotography` → street photography, candid urban life, decisive moment
- `/documentary` → documentary photography, honest unstaged storytelling
- `/photojournalism` → photojournalism, news-style raw real-moment capture
- `/sportsphotography` → sports photography, peak action, fast shutter
- `/wildlifephotography` → wildlife photography, animal in natural habitat, telephoto
- `/landscapephotography` → landscape photography, sweeping vista, deep depth of field
- `/astrophotography` → astrophotography, crisp stars, night sky detail
- `/underwaterphotography` → underwater photography, clear water, natural blue light
- `/aerialphotography` → aerial photography, high-altitude vantage point
- `/nightphotography` → night photography, low light, long exposure, artificial lights

### composition

- `/isometric` → isometric view, 30-degree angled orthographic projection
- `/orthographic` → orthographic view, no perspective distortion
- `/symmetrical` → perfectly symmetrical composition
- `/asymmetrical` → asymmetrical, balanced off-center composition
- `/centeredcomposition` → centered composition, subject in the middle
- `/ruleofthirds` → rule of thirds composition
- `/leadinglines` → leading lines drawing the eye to the subject
- `/negativespace` → generous negative space around the subject
- `/framing` → natural framing, subject framed by foreground elements
- `/diagonalcomposition` → diagonal composition, dynamic slanted lines

### art

- `/abstract` → abstract art, non-representational forms, color and shape
- `/surrealism` → surrealism, dreamlike impossible imagery
- `/minimalart` → minimal art, extreme simplicity and restraint
- `/conceptart` → concept art, production-design style illustration
- `/digitalpainting` → digital painting, painterly brushwork, rich detail
- `/mattepainting` → matte painting, grand cinematic environment
- `/oilpainting` → oil painting, thick brushstrokes, rich color blending
- `/watercolor` → watercolor, translucent washes, soft bleeding edges
- `/acrylicpainting` → acrylic painting, bold opaque color, visible brushwork
- `/pencilsketch` → pencil sketch, graphite shading and hatching
- `/charcoal` → charcoal drawing, smudged expressive tones
- `/inkdrawing` → ink drawing, bold pen lines and hatching
- `/lineart` → clean line art, outline-only, no fill
- `/vectorart` → vector art, flat shapes, crisp edges, scalable
- `/papercut` → papercut art, layered cut paper, depth shadows
- `/collage` → collage, assembled mixed fragments and cutouts
- `/mixedmedia` → mixed media, combined materials and techniques
- `/pixelart` → pixel art, retro low-resolution sprites, limited palette
- `/lowpoly` → low-poly, faceted geometric 3D surfaces
- `/voxelart` → voxel art, cube-built 3D blocks

### render

- `/3drender` → 3D render, clean CGI
- `/unrealengine` → Unreal Engine render, real-time photoreal game graphics
- `/octanerender` → Octane render, high-end GPU path-traced look
- `/raytracing` → ray tracing, accurate reflections and shadows
- `/globalillumination` → global illumination, realistic bounced light
- `/subsurfacescattering` → subsurface scattering, translucent skin, wax or leaf glow
- `/ambientocclusion` → ambient occlusion, soft contact shadows in crevices
- `/depthoffield` → depth of field, focused subject with blurred planes
- `/physicallybasedrendering` → physically based rendering, realistic materials
- `/isometric3d` → isometric 3D render, miniature diorama look
- `/clayrender` → clay render, matte untextured sculpt look
- `/wireframe` → wireframe, visible mesh edges
- `/wireframe3d` → 3D wireframe, glowing mesh model

### space

- `/galaxy` → galaxy, spiral arms, billions of stars
- `/nebula` → colorful nebula, glowing gas clouds
- `/cosmicdust` → cosmic dust clouds, particle haze among stars
- `/eclipse` → solar eclipse, glowing corona around dark disc
- `/supernova` → supernova, explosive stellar burst
- `/blackhole` → black hole, accretion disk, gravitational lensing
- `/wormhole` → wormhole, warped spacetime tunnel

### landscape

- `/foggyforest` → foggy forest, misty trees, quiet depth layers
- `/tropicaljungle` → dense tropical jungle, lush foliage, humid light
- `/autumnforest` → autumn forest, red-orange-gold leaves
- `/cherryblossom` → cherry blossoms in bloom, pink petals falling
- `/frozenlake` → frozen lake, cracked ice, cold stillness
- `/volcaniclandscape` → volcanic landscape, lava, ash, dark rock
- `/waterfall` → waterfall, cascading water, mist
- `/coralreef` → vibrant coral reef, tropical fish, clear water
- `/saltflats` → salt flats, vast white flat plain, mirror-like reflections
- `/canyon` → deep canyon, layered rock walls, dramatic light
- `/northernlights` → northern lights over a night landscape
- `/starrysky` → starry night sky, countless stars
- `/milkyway` → Milky Way arching across the night sky
- `/desertnight` → desert at night, cold starlit dunes
- `/tropicalisland` → tropical island, palms, turquoise water, white sand
- `/coastline` → rugged coastline, waves crashing on rocks
- `/cliffside` → cliffside, steep drop overlooking the sea or valley
- `/lavenderfield` → lavender field, purple rows to the horizon
- `/wildflowermeadow` → wildflower meadow, colorful blooms in tall grass
- `/bambooforest` → bamboo forest, tall green stalks, filtered light

### architecture

- `/ancientruins` → ancient ruins, weathered stone, overgrown history
- `/abandonedbuilding` → abandoned building, decay, peeling paint, broken windows
- `/hauntedhouse` → haunted house, eerie decrepit mansion, ominous mood
- `/gothicarchitecture` → gothic architecture, pointed arches, spires, ornate stone
- `/brutalistarchitecture` → brutalist architecture, raw concrete, massive geometry
- `/modernarchitecture` → modern architecture, clean lines, glass and steel
- `/parametricarchitecture` → parametric architecture, flowing algorithmic curves
- `/futuristicinterior` → futuristic interior, sleek high-tech space
- `/luxuryinterior` → luxury interior, premium materials, elegant decor
- `/scandinavianinterior` → Scandinavian interior, light wood, white, cozy minimalism
- `/industrialdesign` → industrial design, product form study, exposed materials
- `/organicarchitecture` → organic architecture, building flowing with nature

### camera

- `/14mm` → 14mm ultra-wide lens, dramatic perspective stretch
- `/24mm` → 24mm wide lens, environmental context with natural perspective
- `/35mm` → 35mm lens, natural documentary field of view
- `/50mm` → 50mm lens, natural human-eye perspective
- `/85mm` → 85mm portrait lens, flattering compression, creamy background
- `/135mm` → 135mm telephoto lens, strong background compression
- `/200mm` → 200mm telephoto lens, extreme compression, isolated subject
- `/f1.4` → aperture f/1.4, razor-thin focus plane, heavy background blur
- `/f2.8` → aperture f/2.8, soft background separation
- `/f8` → aperture f/8, deep depth of field, edge-to-edge sharpness
- `/tiltshift` → tilt-shift lens, miniature-scale effect, selective focus band
- `/telephoto` → telephoto compression, distant subject pulled close
- `/macrolens` → 100mm macro lens, true close-focus detail

### motion

- `/dolly` → slow dolly camera move toward the subject
- `/pan` → smooth horizontal pan across the scene
- `/orbit` → camera orbiting around the subject
- `/handheld` → handheld camera, subtle natural shake, documentary feel
- `/tracking` → tracking shot following the subject
- `/zoomin` → slow push-in zoom toward the subject
- `/zoomout` → slow pull-back revealing the wider scene
- `/crane` → crane shot rising over the scene
- `/slowmotion` → slow motion, fluid dramatic movement
- `/timelapse` → time-lapse, rapid passage of time, moving clouds and light

### subject

- `/age20s` → person in their twenties
- `/age30s` → person in their thirties
- `/age40s` → person in their forties
- `/age50s` → person in their fifties
- `/elderly` → elderly person, weathered expressive features
- `/smile` → warm natural smile
- `/serious` → serious focused expression
- `/laughing` → genuine laughter, joyful expression
- `/thoughtful` → thoughtful pensive expression
- `/surprised` → surprised wide-eyed expression
- `/calm` → calm serene expression
- `/standing` → standing pose
- `/sitting` → seated pose
- `/walking` → mid-stride walking pose
- `/running` → running, dynamic athletic motion
- `/leaning` → casually leaning pose
- `/armscrossed` → arms crossed, confident stance
- `/lookingatcamera` → looking directly at the camera
- `/lookingaway` → looking away from the camera, candid gaze
- `/suit` → tailored suit, sharp formal tailoring
- `/casualwear` → relaxed casual clothing
- `/streetwear` → contemporary streetwear outfit
- `/traditionalwear` → traditional cultural attire, rich fabric and detail
- `/eveninggown` → elegant evening gown, flowing fabric
- `/uniform` → crisp uniform, structured fit
- `/longhair` → long flowing hair
- `/shorthair` → short styled hair
- `/curlyhair` → natural curly hair
- `/beard` → well-groomed beard

### reference

- `/sameface` → keep the same face and identity as the attached reference image
- `/samestyle` → match the visual style of the attached reference image
- `/samepose` → match the pose of the attached reference image
- `/samecomposition` → match the composition and framing of the attached reference image
- `/samecolors` → match the color palette of the attached reference image
- `/samelighting` → match the lighting of the attached reference image

### couple

- `/couple` → couple portrait of two adults close together, natural connection and warmth
- `/prewedding` → pre-wedding photoshoot, romantic adult couple in elegant coordinated styling
- `/engagement` → engagement photo, adult couple celebrating, joyful intimacy, ring visible
- `/wedding` → wedding photograph, bride and groom in formal wedding attire, celebratory mood
- `/anniversary` → anniversary portrait of a long-married couple, deep familiarity and affection
- `/romantic` → romantic mood, tender glances, soft intimacy
- `/holdinghands` → couple holding hands, gentle connected gesture
- `/embrace` → couple in a gentle warm embrace
- `/foreheadtouch` → couple with foreheads touching, quiet tenderness
- `/walkingtogether` → couple walking together side by side, relaxed natural stride
- `/dancingcouple` → couple dancing together, flowing movement, joyful
- `/laughingtogether` → couple laughing together, genuine shared joy
- `/backtoback` → couple standing back to back, playful confident pose
- `/candidcouple` → candid couple moment, unposed natural interaction
- `/silhouettecouple` → couple silhouette against a bright sky, shared outline
- `/sunsetcouple` → couple at sunset, warm backlight, golden rim light on both

## Aspect-ratio commands
Accept ratios written as `/16:9`, `/16x9` or `/16-9`, plus the named aliases below. If several
are given, produce ONE prompt per ratio (labelled), not just the last. The pixel size is for models that need it (sd, flux).
- `/square` -> 1:1 (1024x1024 px) 1:1 aliases: square instagram
- `/4:3` -> 4:3 (1152x896 px) standard landscape
- `/3:2` -> 3:2 (1216x832 px) classic photo landscape
- `/16:9` -> 16:9 (1344x768 px) widescreen; aliases: wallpaper thumbnail youtube
- `/21:9` -> 21:9 (1536x640 px) ultrawide; aliases: ultrawide cinemascope
- `/9:16` -> 9:16 (768x1344 px) vertical phone; aliases: story reel tiktok phonewallpaper
- `/2:3` -> 2:3 (832x1216 px) portrait photo; aliases: poster
- `/3:4` -> 3:4 (896x1152 px) portrait
- `/4:5` -> 4:5 (896x1120 px) instagram portrait
- `/3:1` -> 3:1 (1728x576 px) banner; aliases: banner panorama

## Negative commands (things to avoid)
These do NOT add to the image; they build the "avoid" list. Merge every negative command used
into one list, deduplicated. Show it as a separate `Negative:` / `--no` / sentence per the model.
- `/clean` -> avoid: text, watermark, logo, signature, caption, username
- `/nodeform` -> avoid: extra fingers, missing fingers, deformed hands, extra limbs, malformed anatomy, distorted face, cross-eyed
- `/sharpclean` -> avoid: blurry, low resolution, jpeg artifacts, noise, pixelated, out of focus
- `/nopeople` -> avoid: people, humans, faces, crowds
- `/notext` -> avoid: text, letters, words, typography, numbers
- `/nocrop` -> avoid: cropped, cut off, out of frame, partial subject
- `/nooversat` -> avoid: oversaturated, neon colors, harsh contrast, burnt highlights
- `/noai` -> avoid: plastic skin, waxy texture, over-smoothed, uncanny, cgi look, oversharpened halos

## Presets (one command = a tested bundle)
Expand a preset into its commands, then process as normal. The user's own ratio overrides the preset's default ratio; user commands that conflict with the preset win.
- `/productshot` (Product hero shot) = /productphotography /studio /softlighting /shallowdepth /85mm /sharpfocus /clean (default ratio /square)
- `/linkedinheadshot` (Professional headshot) = /headshot /studio /softlighting /85mm /f1.4 /naturalcolors /nodeform /clean (default ratio /4:5)
- `/albumcover` (Album cover art) = /cinematic /dramaticlighting /centeredcomposition /filmgrain /colorgraded (default ratio /square)
- `/youtubethumb` (YouTube thumbnail) = /closeup /dramaticlighting /highcontrast /vibrantcolors /sharpfocus (default ratio /16:9)
- `/moviepost` (Movie poster) = /cinematic /dramaticlighting /anamorphic /tealandorange /filmgrain (default ratio /2:3)
- `/streetportrait` (Street portrait) = /streetphotography /candid /35mm /goldenhour /filmgrain (default ratio /3:2)
- `/foodhero` (Food hero shot) = /foodphotography /macrolens /naturalwindowlight /softlighting /shallowdepth (default ratio /4:5)
- `/realestate` (Real-estate interior) = /realestatephotography /14mm /naturalwindowlight /highdetail (default ratio /16:9)
- `/fashioneditorial` (Fashion editorial) = /fashion /editorial /dramaticlighting /85mm /colorgraded (default ratio /4:5)
- `/cyberpunkcity` (Cyberpunk city) = /cyberpunk /nightcity /rainynight /neonlights /anamorphic (default ratio /21:9)
- `/epicfantasy` (Epic fantasy scene) = /fantasy /mattepainting /godrays /wideangle /highdetail (default ratio /16:9)
- `/portraitpro` (Pro portrait) = /portrait /85mm /f1.4 /softlighting /bokeh /naturalcolors /nodeform (default ratio /3:4)
- `/couplepro` (Couple portrait) = /couple /romantic /candid /85mm /softlighting /goldenhour /naturalcolors /nodeform (default ratio /4:5)
- `/weddingclassic` (Classic wedding photo) = /wedding /50mm /softlighting /naturalcolors /colorgraded /nodeform /clean (default ratio /3:2)

## Output-format commands (target model)
At most one. If none is given, use `/generic`. Adapt the final prompt to the model's style:
- `/mj` -> **Midjourney**: Comma-separated phrases. Append `--ar W:H` for aspect, `--no a, b, c` for negatives, and `--style raw` when /rawphoto, /photorealistic or /ultrarealistic is used. No pixel sizes.
- `/sd` -> **Stable Diffusion / SDXL**: Comma-separated keywords. Output two lines: `Prompt:` and `Negative prompt:` (always include "lowres, blurry, bad anatomy, watermark" plus any /no-commands). Output `Size: WxH` from the pixel column. May weight key terms like `(golden hour:1.2)`.
- `/flux` -> **Flux**: Natural descriptive sentences, no weights and no negative prompt (Flux ignores them: fold avoidances in as positive wording, e.g. "clean image without text"). Output `Size: WxH` from the pixel column.
- `/dalle` -> **DALL-E / ChatGPT images**: One or two natural English sentences. No flags. Negatives become positive phrasing ("no text" -> "with no text or lettering"). Aspect: nearest of 1024x1024, 1792x1024 (wide), 1024x1792 (tall).
- `/gemini` -> **Gemini / Imagen**: Natural English paragraph. State the aspect ratio in words and pass it as the tool's aspect_ratio parameter if one exists. Negatives become positive phrasing.
- `/flow` -> **Google Flow (Veo / Imagen)**: Natural English: subject, setting, camera/angle, lighting, style as one flowing paragraph. Aspect is chosen in Flow settings (video: 16:9 or 9:16 only), so print `Set aspect ratio to X` as a separate line. Negatives become positive phrasing, or go in Flow's negative field if shown.
- `/kling` -> **Kling AI**: Descriptive natural English in this order: subject, environment, camera, lighting, style (under 2500 chars). Print a separate `Negative prompt:` line for Kling's negative field. Print `Aspect ratio:` (16:9, 9:16 or 1:1 only; map others to the nearest). For video requests also add one line of motion and camera movement.
- `/generic` -> **Default**: Comma-separated prompt, then `Aspect ratio:` and `Avoid:` lines if used.

Final answer layout when you cannot generate directly:
```
<prompt in the target model's format>
<negative / size / flags lines if the model uses them>
```
