# Phase 1 Features & Test Prompts

## ✅ Complete Feature List

### 1. Pre-Generation Dialogue System (4 Modes)

**What it does:** Asks guided questions before generating images to refine your vision

**Modes:**
- **Quick** - 1-2 questions, fast path
- **Guided** - 3-5 questions, balanced (DEFAULT)
- **Explorer** - 6+ questions, deep exploration
- **Skip** - Direct generation, no questions

**Test Prompts:**

#### Guided Mode (Default)
```
"Create a logo for my coffee shop called 'Sunrise Roasters'"
```
**Expected:** 3-5 questions about branding, style, colors, composition
**Success:** Questions are relevant to logos, answers incorporated into final prompt

#### Quick Mode
```
"Create an Instagram post announcing our new product launch"
```
**Expected:** 1-2 focused questions
**Success:** Fast dialogue, still improves prompt quality

#### Explorer Mode
```
"Create a professional presentation background for a tech conference keynote"
```
**Expected:** 6+ detailed questions about audience, mood, colors, composition, etc.
**Success:** Comprehensive exploration leading to detailed prompt

#### Skip Mode (Direct Generation)
```
"Skip dialogue mode. Generate a TRON movie style scene with a figure standing on a glowing digital grid, neon cyan and magenta lights, text overlay saying 'DEATH TO THE SDLC' in futuristic font, cinematic lighting"
```
**Expected:** No questions, immediate generation
**Success:** Image generates directly without dialogue

---

### 2. Automatic Prompt Enhancement

**What it does:** Analyzes prompt quality (0-100 score) and automatically enriches prompts based on image type

**Features:**
- Quality scoring (0-100)
- 9 image types detected (logo, presentation, social_media, portrait, landscape, product, abstract, illustration, general)
- Type-specific optimizations
- Contextual suggestions

**Test Prompts:**

#### Minimal Prompt → Enhanced
```
"Create a logo"
```
**Expected:**
- Quality score: ~25/100 (minimal)
- System detects: logo type
- Auto-adds: "professional quality, scalable vector design, clean lines, suitable for branding"
**Success:** Enhanced prompt has much higher quality score

#### Already Good Prompt → Minimal Enhancement
```
"A serene mountain lake at sunset, photorealistic style, golden hour lighting, reflections on water, dramatic sky with orange and purple clouds, 4K quality"
```
**Expected:**
- Quality score: ~85/100 (already good)
- System detects: landscape type
- Minimal changes needed
**Success:** High quality score, prompt mostly preserved

#### Image Type Detection Test
```
"Design a Facebook cover photo for our bakery"
```
**Expected:**
- Detects: social_media type
- Auto-suggests: 1536x1024 (landscape for cover photo)
- Optimizations: "eye-catching, mobile-friendly, engaging composition"
**Success:** Correct type detected, appropriate size suggested

---

### 3. Image Quality Verification

**What it does:** Automatically checks generated images before delivery with type-specific checklists

**Features:**
- Requirement checklist based on prompt + dialogue responses
- Type-specific verification (logo quality, presentation suitability, etc.)
- Confidence scoring (0-100%)
- Helpful reminders to review key requirements
- Verification results saved to conversation storage

**Test Prompts:**

#### Logo Verification
```
"Create a minimalist tech company logo with blue and white colors"
```
**Expected Verification Checklist:**
- ✓ Subject Matter: Tech company logo
- ✓ Logo Quality: Clean, scalable design suitable for branding
- ✓ Style: Minimalist
- ✓ Colors: Blue and white
- ✓ Overall Quality: Professional quality, no artifacts

**Success:** Checklist mentions logo-specific requirements (scalability, clean design)

#### Text-in-Image Verification
```
"Create a motivational poster with the text 'NEVER GIVE UP' in bold letters"
```
**Expected Verification Checklist:**
- ✓ Subject Matter: Motivational poster
- ✓ Text Presence: "NEVER GIVE UP" should be visible and legible
- ✓ Typography: Bold letters, readable
- ✓ Overall composition

**Success:** Verification explicitly mentions checking for text presence

#### TRON Scene Verification (Your Example)
```
"TRON movie style scene, figure on glowing digital grid, neon cyan and magenta lights, text 'DEATH TO THE SDLC', futuristic font, cinematic lighting"
```
**Expected Verification Checklist:**
- ✓ Subject Matter: TRON-style scene with figure on digital grid
- ✓ Visual Elements: Glowing digital grid, neon lights
- ✓ Text Presence: "DEATH TO THE SDLC" in futuristic font
- ✓ Colors: Cyan and magenta neon lights
- ✓ Style: Cinematic lighting, futuristic aesthetic

**Success:** If image is wrong (like street sign with vines), verification reminds you to check these requirements

---

### 4. Persistent Local Storage

**What it does:** Saves all conversations to local JSON files that survive server restarts

**Features:**
- Location: `~/.openai-images-mcp/conversations/`
- JSON format, human-readable
- Full conversation history (messages, dialogue responses, enhanced prompts, generated images)
- Verification results included
- Survives server restarts

**Test Prompts:**

#### Save & Resume Conversation
```
Step 1: "Create a mountain landscape photograph"
(Answer 2-3 questions, then STOP before completion)
Note the conversation_id

Step 2: Restart Claude Desktop (Cmd+Q, reopen)

Step 3: "Resume conversation [conversation_id]"
```
**Expected:** Conversation loads from storage, remembers previous answers, continues where you left off
**Success:** All previous dialogue responses preserved

#### List All Conversations
```
"List all my image generation conversations"
```
**Expected:** Shows all saved conversations with:
- Conversation IDs
- First prompt from each
- Dialogue mode used
- Number of images generated
- Timestamps

**Success:** Can see all past conversations

#### Search Conversations
```
"Search my conversations for 'logo'"
```
**Expected:** Finds all conversations containing "logo" in prompts or messages
**Success:** Relevant conversations returned

---

### 5. Smart Size Detection

**What it does:** Automatically suggests optimal image dimensions based on image type and context

**Supported Sizes:**
- 1024x1024 (square)
- 1024x1536 (portrait/vertical)
- 1536x1024 (landscape/horizontal)

**Test Prompts:**

#### Logo → Square
```
"Create a logo for my tech startup"
```
**Expected:** Auto-suggests 1024x1024 (square)
**Success:** Square size for versatile logo use

#### Presentation → Landscape
```
"Create a PowerPoint slide background"
```
**Expected:** Auto-suggests 1536x1024 (landscape)
**Success:** Landscape for 16:9 presentations

#### Instagram Story → Portrait
```
"Create an Instagram story about travel"
```
**Expected:** Auto-suggests 1024x1536 (portrait)
**Success:** Vertical format for stories

#### Portrait Photography → Portrait
```
"Professional headshot of a business executive"
```
**Expected:** Auto-suggests 1024x1536 (portrait)
**Success:** Vertical format for portrait

---

### 6. Iterative Refinement with Context

**What it does:** Maintains conversation context across multiple refinements without re-asking dialogue questions

**Test Prompts:**

#### Complete Refinement Workflow
```
1. Initial: "Create a cozy coffee shop interior"
   (Answer dialogue questions)

2. Refinement 1: "Make it more modern with industrial elements"
   (No new dialogue questions)

3. Refinement 2: "Add more plants and warmer lighting"
   (No new dialogue questions)

4. Refinement 3: "Include people working on laptops"
   (No new dialogue questions)
```
**Expected:**
- Dialogue only on initial generation
- Refinements apply directly to previous image
- Context maintained throughout
- All images saved with timestamps

**Success:** Each refinement builds on previous, no redundant questions

---

### 7. Context-Aware Dialogue Questions

**What it does:** Dialogue questions adapt based on detected image type

**Test Prompts:**

#### Logo-Specific Questions
```
"Create a brand icon for our company"
```
**Expected Questions:**
- "What does this logo represent? What should it communicate?"
- "What visual style appeals to you?" (with logo-relevant options)
- "What color palette works best?"
- "How simple or detailed should it be?" (scalability focus)

**Success:** Questions focus on branding, scalability, versatility

#### Presentation-Specific Questions
```
"Design a slide background for a business presentation"
```
**Expected Questions:**
- "What's the presentation about? Who's the audience?"
- "What mood should it convey?"
- "What colors work best for readability?"
- "Any composition preferences?" (text space focus)

**Success:** Questions focus on readability, projector-friendliness, professional context

#### Social Media-Specific Questions
```
"Create a Facebook post image"
```
**Expected Questions:**
- "What's the goal of this post?"
- "What visual style will grab attention?"
- "Any specific colors or branding?"

**Success:** Questions focus on engagement, eye-catching appeal, mobile viewing

---

### 8. Tool Selection Intelligence

**What it does:** Two tools with clear use cases for AI to choose correctly

**Tools:**
- `openai_generate_image` - Direct generation, no dialogue
- `openai_conversational_image` - Dialogue-based generation

**Test Prompts:**

#### Should Use Direct Generation Tool
```
"Create a photorealistic eagle in flight, dramatic lighting, sharp details, wildlife photography style, cloudy sky background"
```
**Expected:** AI chooses `openai_generate_image`, no dialogue
**Success:** Immediate generation because prompt is detailed and complete

#### Should Use Conversational Tool
```
"Create a poster for my event"
```
**Expected:** AI chooses `openai_conversational_image`, starts dialogue
**Success:** Asks questions because prompt is vague (what event? what style? what info?)

---

## 🎯 Complete Test Suite (Recommended Order)

### Quick Smoke Test (5 minutes)
```
1. "Create a logo for my bakery"
   → Guided dialogue, verify checklist

2. "Skip dialogue: Generate abstract art with vibrant colors"
   → No dialogue, immediate generation

3. "List all my conversations"
   → See conversation history

4. Resume last conversation: "Make it brighter"
   → Refinement without new dialogue
```

### Comprehensive Test (30 minutes)

**Logo Workflow:**
```
"Create a logo for my coffee shop called 'Sunrise Roasters'"
→ Answer dialogue questions naturally
→ Check verification report for logo-specific items
→ Refine: "Make it more vintage"
```

**TRON Scene (Your Example):**
```
"Skip dialogue. Generate TRON movie style scene, figure on glowing digital grid, neon cyan and magenta lights, text 'DEATH TO THE SDLC', futuristic font, cinematic"
→ No dialogue
→ Verification mentions TRON elements, text, colors
→ Check if text is actually present in image
```

**Social Media Post:**
```
"Create an Instagram post about our new product"
→ Quick mode (1-2 questions)
→ Should auto-detect square size (1024x1024)
→ Verification mentions social media appeal
```

**Presentation Background:**
```
"Create a professional slide background for a tech conference"
→ Guided or Explorer mode
→ Should auto-detect landscape size (1536x1024)
→ Verification mentions presentation readability
```

**Iterative Refinement:**
```
1. "Create a modern office space"
2. "Add more natural light"
3. "Include minimalist furniture"
4. "Add some plants"
→ Only first prompt gets dialogue
→ Check all 4 images saved
```

**Storage & Resume:**
```
1. Start dialogue for "Create a portrait"
2. Answer 2 questions, then STOP
3. Restart Claude Desktop
4. "List conversations"
5. Resume with conversation_id
→ Should continue from where you left off
```

---

## 📊 Success Criteria

After testing, verify:

### Dialogue System
- [ ] Questions are relevant to image type
- [ ] Answers incorporated into final prompt
- [ ] Can choose different dialogue modes
- [ ] Skip mode works (no questions)

### Prompt Enhancement
- [ ] Quality scores make sense (minimal prompts ~20-40, detailed ~80-95)
- [ ] Type detection is accurate
- [ ] Enhanced prompts are better than originals
- [ ] Size suggestions match image type

### Image Verification
- [ ] Verification checklist is relevant to prompt
- [ ] Type-specific checks included (logo quality, presentation readability, etc.)
- [ ] Text requirements mentioned when applicable
- [ ] Confidence score provided

### Storage & Persistence
- [ ] Conversations save to ~/.openai-images-mcp/conversations/
- [ ] Can list all conversations
- [ ] Can resume after restart
- [ ] Conversation history preserved

### Refinement Workflow
- [ ] No new dialogue questions on refinements
- [ ] Context maintained across multiple edits
- [ ] All images saved with timestamps
- [ ] Can see conversation history

### Tool Selection
- [ ] Detailed prompts → Direct generation (no dialogue)
- [ ] Vague prompts → Conversational tool (dialogue)
- [ ] Works as expected from AI's perspective

---

## 🐛 Known Limitations (Phase 1)

1. **Verification doesn't "see" the image yet**
   - Creates checklists but can't automatically verify
   - Relies on user to check image matches requirements
   - Phase 2 will add vision-based verification

2. **Text generation is unreliable**
   - OpenAI's image model struggles with text
   - Verification reminds you to check, but can't guarantee text is present
   - This is a model limitation, not a system limitation

3. **Always passes verification**
   - Phase 1 provides guidance but never blocks delivery
   - Future phases can add confidence thresholds

---

## 📝 Feedback Template

After testing, please note:

1. **Which features worked well?**
2. **Which prompts failed or had issues?**
3. **Was dialogue helpful or annoying?**
4. **Did verification catch anything you would have missed?**
5. **Which dialogue mode did you prefer?**
6. **Any bugs or unexpected behavior?**

---

**Ready to test!** 🚀

Start with the Quick Smoke Test, then try scenarios that interest you.
