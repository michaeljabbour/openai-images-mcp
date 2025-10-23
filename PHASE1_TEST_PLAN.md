# Phase 1 Testing Plan - Conversational Dialogue System

## 🎯 Test Objectives

1. **Dialogue Quality** - Questions are helpful and lead to better images
2. **Prompt Enhancement** - Enhanced prompts produce better results than originals
3. **Image Verification** - System catches mismatches before delivery
4. **Persistence** - Conversations save and resume correctly
5. **User Experience** - Flow feels natural and improves outcomes

---

## 📋 Test Scenarios

### Scenario 1: Logo Design (Guided Mode - Default)

**Test Objective:** Verify guided dialogue improves logo generation

**Prompt:**
```
Create a logo for my coffee shop called "Sunrise Roasters"
```

**Expected Dialogue Flow:**
1. **Initial Question** - "Tell me about what this logo represents. What should it communicate?"
   - Example answer: "Local, artisanal, welcoming atmosphere, morning coffee culture"

2. **Style Question** - "What visual style appeals to you?"
   - Example answer: "Warm, minimalist, hand-crafted feel"

3. **Color Question** - "What color palette works best?"
   - Example answer: "Warm earth tones, sunrise oranges and yellows, coffee browns"

4. **Details Question** - "How detailed should it be?"
   - Example answer: "Simple and memorable, works at small sizes"

**Success Criteria:**
- ✅ System asks 3-5 questions
- ✅ Questions are relevant to logos (branding, scalability, colors)
- ✅ Enhanced prompt includes all your answers
- ✅ Image quality verification runs automatically
- ✅ Generated logo is cleaner/more professional than a direct generation
- ✅ Verification checklist mentions logo-specific requirements

---

### Scenario 2: TRON-Style Scene (Skip Mode)

**Test Objective:** Verify skip mode bypasses dialogue for experienced users

**Prompt:**
```
Skip dialogue mode. Generate a TRON movie style scene with a figure standing on a glowing digital grid, neon cyan and magenta lights, text overlay saying "DEATH TO THE SDLC" in futuristic font, cinematic lighting
```

**OR use this pattern:**
```
dialogue_mode=skip: [your detailed prompt]
```

**Expected Behavior:**
- ✅ No dialogue questions
- ✅ Direct generation with your detailed prompt
- ✅ Verification still runs (checks for TRON elements, text, colors)
- ✅ If verification detects text is missing, it should suggest refinement

**Success Criteria:**
- ✅ Image generated immediately without questions
- ✅ Verification report mentions what to check (TRON aesthetic, text presence, neon colors)
- ✅ If image doesn't match (like your previous failures), verification flags issues

---

### Scenario 3: Social Media Post (Quick Mode)

**Test Objective:** Verify quick mode asks minimal but effective questions

**Prompt:**
```
Create an Instagram post announcing our new product launch
```

**Expected Dialogue Flow:**
1. **Initial Question** - "What's the goal of this social media post?" or "Tell me about the product"
2. **Style/Visual Question** - One combined question about style and appeal

**Success Criteria:**
- ✅ Only 1-2 questions asked
- ✅ Questions are focused and efficient
- ✅ Auto-detects Instagram post type
- ✅ Auto-suggests square (1024x1024) size
- ✅ Verification checks for social media appeal (eye-catching, mobile-friendly)

---

### Scenario 4: Presentation Background (Explorer Mode)

**Test Objective:** Verify explorer mode provides deep exploration

**Prompt:**
```
Create a professional presentation background for a tech conference keynote
```

**Dialogue Mode:** Specify "explorer" mode

**Expected Dialogue Flow:**
1. Initial - "What's the presentation about? Who's the audience?"
2. Style - "What visual style appeals to you?"
3. Colors - "What color palette works best?"
4. Mood - "What mood or atmosphere should it convey?"
5. Details - "How detailed should it be?"
6. Composition - "Any composition preferences?"
7. Possibly more specific questions about elements

**Success Criteria:**
- ✅ Asks 6+ questions
- ✅ Covers presentation-specific concerns (readability, projector-friendly, text space)
- ✅ Auto-suggests landscape (1536x1024) size
- ✅ Enhanced prompt is comprehensive
- ✅ Verification checks presentation-specific requirements

---

### Scenario 5: Conversation Resumption

**Test Objective:** Verify conversations persist across sessions

**Steps:**
1. Start a dialogue: "Create a mountain landscape photograph"
2. Answer 2 questions, then STOP before completing
3. Note the conversation_id
4. Restart Claude Desktop (or wait and come back later)
5. Use the conversation_id to resume

**Success Criteria:**
- ✅ Conversation loads from `~/.openai-images-mcp/conversations/`
- ✅ System remembers your previous answers
- ✅ Continues from where you left off
- ✅ Can complete dialogue and generate image
- ✅ All conversation history is preserved

---

### Scenario 6: Iterative Refinement

**Test Objective:** Verify refinement workflow maintains context

**Initial Prompt:**
```
Create a cozy coffee shop interior
```

**Answer dialogue questions naturally**

**Refinement 1:**
```
Make it more modern with industrial elements
```

**Refinement 2:**
```
Add more plants and warmer lighting
```

**Success Criteria:**
- ✅ No new dialogue questions for refinements (context maintained)
- ✅ Each refinement builds on previous image
- ✅ Verification runs for each generation
- ✅ All images saved with timestamps
- ✅ Can list conversation history with `openai_list_conversations`

---

## 🔍 Verification Testing

### Test: Verification Catches Mismatches

**Objective:** Ensure verification system provides helpful feedback

**Test Case 1: Text in Image**
- Prompt: "Create an image with the text 'Hello World' in bold letters"
- **Verify:** Checklist mentions text requirement
- **Verify:** If text is missing, verification notes this

**Test Case 2: Specific Colors**
- Prompt with dialogue: Specify "Only use blue and white colors"
- **Verify:** Checklist mentions color requirement
- **Verify:** Report reminds you to check colors

**Test Case 3: Image Type Mismatch**
- Prompt: "Create a minimalist logo"
- **Verify:** Checklist includes "Logo Quality" item
- **Verify:** Mentions scalability and clean design requirements

---

## 🎨 Image Type Detection Testing

**Test each image type is detected correctly:**

### Logo
```
- "Create a logo for my startup"
- "Design a brand icon for our company"
- "Make an emblem for the tech club"
```
**Expected:** Type=logo, Size=1024x1024 (square), Logo-specific optimizations

### Presentation
```
- "Create a presentation slide background"
- "Professional PowerPoint backdrop"
- "Conference slide design"
```
**Expected:** Type=presentation, Size=1536x1024 (landscape), High-contrast optimizations

### Social Media
```
- "Instagram post about travel"
- "Facebook cover photo"
- "Twitter header image"
```
**Expected:** Type=social_media, Size=1024x1024 or contextual, Eye-catching optimizations

### Portrait
```
- "Portrait of a person with dramatic lighting"
- "Professional headshot"
- "Character portrait"
```
**Expected:** Type=portrait, Size=1024x1536 (vertical)

### Product
```
- "Product photography of a watch"
- "Commercial product shot of sneakers"
```
**Expected:** Type=product, Professional lighting optimization

---

## 💾 Storage & Persistence Testing

### Test: Conversation Storage

**Steps:**
1. Generate an image through dialogue
2. Check `~/.openai-images-mcp/conversations/` directory exists
3. Find the conversation JSON file
4. Verify it contains:
   - Your dialogue responses
   - Enhanced prompt
   - Generated image info
   - Timestamps

**Success Criteria:**
- ✅ JSON file is human-readable
- ✅ Contains all conversation history
- ✅ Includes verification results
- ✅ Proper timestamps

### Test: List Conversations

**Command:**
```
List all my image generation conversations
```

**Expected:**
- Shows all saved conversations
- Displays conversation IDs
- Shows first prompt from each
- Indicates dialogue mode used
- Shows image count

---

## 🐛 Edge Cases & Error Handling

### Test: Empty Dialogue Responses
- Start dialogue but provide minimal/empty answers
- **Verify:** Still generates reasonable image
- **Verify:** Doesn't crash or error

### Test: Very Long Prompt
- Provide a 3000+ character detailed prompt
- **Verify:** Handles gracefully
- **Verify:** Doesn't exceed API limits

### Test: Skip Dialogue Flag
- Use `skip_dialogue=true` parameter
- **Verify:** Bypasses dialogue even in guided mode

### Test: Invalid Image Size
- Try to specify an unsupported size
- **Verify:** Falls back to auto-detection
- **Verify:** Provides helpful error message

---

## 🎯 Quick Test Checklist

For a fast smoke test, try these in order:

**5-Minute Test:**
1. ✅ Logo with dialogue: "Create a logo for my bakery"
2. ✅ Skip mode: "skip dialogue: Generate abstract art with vibrant colors"
3. ✅ List conversations
4. ✅ Resume last conversation
5. ✅ Refine the image: "Make it brighter"

**Success = All 5 work without errors**

---

## 📊 Success Metrics

After testing, evaluate:

### Dialogue Quality (1-5 rating)
- [ ] Questions were helpful and relevant
- [ ] Dialogue felt natural, not robotic
- [ ] Answers were incorporated into final prompt
- [ ] Generated images were better than without dialogue

### Verification Accuracy
- [ ] Verification checklist was relevant
- [ ] Caught obvious mismatches (when they occurred)
- [ ] Didn't block good images
- [ ] Suggestions were actionable

### Persistence
- [ ] Conversations saved correctly
- [ ] Could resume after restart
- [ ] All data preserved properly
- [ ] Storage location accessible

### Overall Experience
- [ ] Faster to get good results (vs. trial-and-error)
- [ ] Would use this over simple generation
- [ ] Dialogue adds value, not friction

---

## 🔧 Debugging Commands

If something doesn't work:

```bash
# Check if storage directory exists
ls -la ~/.openai-images-mcp/conversations/

# View a conversation file
cat ~/.openai-images-mcp/conversations/conv_*.json | head -50

# Check recent images
ls -lt ~/Downloads/openai_image_* | head -5

# Run verification tests
pytest tests/test_image_verification.py -v

# Run all Phase 1 tests
./run_tests.sh
```

---

## 🚀 Advanced Test Scenarios

### Complex Multi-Stage Scene
```
Create an image of a futuristic cityscape at night, with flying vehicles, neon signs in multiple languages, rain-soaked streets reflecting lights, cyberpunk aesthetic, blade runner inspired, highly detailed
```

**Test:** Does skip mode handle complex prompts better than dialogue?

### Specific Text Requirements
```
Create a motivational poster with the text "NEVER GIVE UP" in bold letters, mountain background, inspiring atmosphere
```

**Test:** Verification should specifically mention checking for text presence

### Brand-Specific Requirements
```
Create a logo for "TechVision AI" - needs to work in black & white for legal docs, convey innovation and trust, avoid clichés like lightbulbs or gears
```

**Test:** Dialogue should capture all specific requirements and constraints

---

## 📝 Feedback Template

After testing, please provide feedback on:

1. **What worked well?**
2. **What didn't work as expected?**
3. **Which dialogue mode did you prefer?**
4. **Were verification reports helpful?**
5. **Did enhanced prompts produce better images?**
6. **Any suggested improvements?**

---

**Ready to test!** 🎨✨

Start with the 5-minute quick test, then dive into specific scenarios that interest you.
