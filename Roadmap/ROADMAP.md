# OpenAI Images MCP - Feature Roadmap & Implementation Plan

## 📊 Current State Analysis

### What We Have Today (v3.0)
- ✅ Single image generation with GPT-Image-1
- ✅ Conversational refinement (linear: generate → refine → refine)
- ✅ File saving to Downloads with unique timestamps
- ✅ Conversation context preservation
- ✅ Three tools: conversational, generate, list_conversations

### Current Constraints
- Single image per request
- Linear refinement path only
- No variation exploration
- No style presets or workflows
- No guided creative process
- User must know exactly what they want

### Technical Foundation (Available to Build On)
- ✅ Responses API integration (multi-turn conversations)
- ✅ Conversation state management (`conversation_store`)
- ✅ File ID handling for image references
- ✅ Base64 image processing
- ✅ MCP tool framework (FastMCP)
- ✅ Async HTTP client (httpx)

---

## 🎯 Feature Tiers & Sequencing

### **TIER 1: FOUNDATION** (Weeks 1-2)
*Enable basic choice and exploration without overwhelming complexity*

#### 1.1 Quick Mode Selection 🚀
**Priority: P0 (Must Have)**

**User Story**: "As a user, I want to quickly choose between 'just generate' or 'let's explore together' so I can control the experience depth."

**Requirements**:
- Add `mode` parameter to ConversationalImageInput: `quick`, `guided`, `explorer`
- **Quick mode**: Single image, no questions (current behavior)
- **Guided mode**: AI asks 1-2 clarifying questions before generating
- **Explorer mode**: Generate 2-3 initial variations, then refine

**Implementation**:
```python
class GenerationMode(str, Enum):
    QUICK = "quick"      # One shot, no questions
    GUIDED = "guided"    # AI asks clarifying questions
    EXPLORER = "explorer" # Multiple initial variations
```

**Success Metrics**:
- Mode parameter accepted and respected
- Quick mode = 1 API call
- Guided mode = 1-2 question exchanges + 1 generation
- Explorer mode = 1 generation call with N=3

**Dependencies**: None (builds on current foundation)

---

#### 1.2 Variation Generation 🎨
**Priority: P0 (Must Have)**

**User Story**: "As a user, I want to see 2-4 variations of my prompt so I can choose the best direction without guessing."

**Requirements**:
- Add `variations` parameter (1-4, default=1)
- Generate N images in single API call (OpenAI supports n=1-10)
- Save all to Downloads with sequence numbers
- Present results as numbered list with file paths
- Store all file IDs for potential refinement

**Implementation**:
```python
variations: Optional[int] = Field(
    default=1,
    ge=1,
    le=4,
    description="Number of variations to generate (1-4). More variations = more API cost."
)
```

**Response Format**:
```
✅ Generated 3 variations:

1. 📁 ~/Downloads/openai_image_20251022_v1.png (Modern, bright)
2. 📁 ~/Downloads/openai_image_20251022_v2.png (Moody, dark)
3. 📁 ~/Downloads/openai_image_20251022_v3.png (Minimal, clean)

Which variation should we refine? (Reply with number or describe changes)
```

**Success Metrics**:
- Can generate 1-4 images in single request
- All saved with proper naming (v1, v2, v3, v4)
- File IDs stored for each variation
- User can reference by number for refinement

**Dependencies**: None

---

#### 1.3 Style Presets 🎭
**Priority: P1 (Should Have)**

**User Story**: "As a user, I want to quickly apply common styles without describing them in detail."

**Requirements**:
- Add `style_preset` optional parameter
- 6-8 well-defined presets that augment user's prompt
- Presets modify prompt with style-specific keywords
- Document each preset with examples

**Preset List**:
1. `photorealistic` - "photorealistic, high detail, 8k, professional photography"
2. `artistic` - "artistic, painterly, expressive brushstrokes, gallery quality"
3. `minimalist` - "minimalist, clean lines, simple composition, lots of negative space"
4. `cinematic` - "cinematic lighting, dramatic composition, film still quality"
5. `sketch` - "pencil sketch, hand-drawn, artistic study, loose linework"
6. `vibrant` - "vibrant colors, saturated, energetic, bold palette"
7. `moody` - "moody atmosphere, dramatic shadows, low-key lighting"
8. `corporate` - "professional, clean, appropriate for business use, polished"

**Implementation**:
```python
STYLE_PRESETS = {
    "photorealistic": "photorealistic, high detail, 8k, professional photography, sharp focus",
    "artistic": "artistic painting, expressive brushstrokes, gallery quality, fine art",
    # ... etc
}

# In function:
if params.style_preset:
    enhanced_prompt = f"{params.prompt}, {STYLE_PRESETS[params.style_preset]}"
```

**Success Metrics**:
- Presets consistently improve output in intended direction
- Users can combine with custom prompts
- Clear documentation of what each preset does

**Dependencies**: None

---

### **TIER 2: ENHANCED INTERACTION** (Weeks 3-4)
*Introduce guided workflows and intelligent assistance*

#### 2.1 Guided Mode with Clarifying Questions 💬
**Priority: P0 (Must Have)**

**User Story**: "As a user who's not sure exactly what I want, I want the AI to ask me helpful questions so I get better results."

**Requirements**:
- When `mode=guided`, AI analyzes prompt and asks 1-2 targeted questions
- Questions focus on: mood, composition, style, or context
- Store Q&A in conversation history
- Generate image incorporating answers
- Questions are intelligent (not generic)

**Example Flow**:
```
User: "Create a logo for my tech startup"

AI: "I'll help you create the perfect logo. Two quick questions:

1. What mood should it convey?
   A) Professional & trustworthy
   B) Innovative & bold
   C) Friendly & approachable

2. Preferred style?
   A) Minimalist & modern
   B) Detailed & illustrative
   C) Abstract & geometric

Reply with your choices (e.g., '1B, 2A') or describe your vision."

[User responds]

AI: [Generates with incorporated preferences]
```

**Implementation**:
- Add prompt analysis logic using assistant_model
- Template-based question generation based on prompt type detection
- Store responses in conversation context
- Synthesize into enhanced generation prompt

**Success Metrics**:
- Questions are relevant to user's request
- Results better match user intent than unguided
- 70%+ of users find questions helpful (survey)

**Dependencies**: 1.1 (Mode Selection)

---

#### 2.2 Divergent Exploration (Branch & Compare) 🌳
**Priority: P1 (Should Have)**

**User Story**: "As a creative user, I want to explore different conceptual directions from one starting point."

**Requirements**:
- New mode: `mode=divergent`
- From one prompt, generate 3 conceptually different interpretations
- Each interpretation explores different:
  - Composition approach
  - Mood/atmosphere
  - Style/technique
  - Conceptual angle
- AI explains what makes each unique
- User can pick one to explore deeper

**Example Flow**:
```
User: "Office of the future" (mode=divergent)

AI: "I've explored 3 different visions:

1. 📁 utopian_bright.png
   → Optimistic: Open, green spaces, natural light, collaborative

2. 📁 minimal_tech.png
   → Minimalist: Clean lines, holographic displays, efficiency-focused

3. 📁 cyberpunk_edge.png
   → Dystopian: Dense, neon-lit, high-tech chaos, atmospheric

Which direction resonates? I can generate more variations or blend concepts."
```

**Implementation**:
- Create 3 distinct prompt variations emphasizing different aspects
- Generate all 3 (n=3 or 3 separate calls)
- Use conversation context to name/categorize each
- Store all file IDs for follow-up

**Success Metrics**:
- 3 images are visibly distinct (not just minor variations)
- Users can identify which direction they prefer
- 80%+ of branches lead to further refinement

**Dependencies**: 1.2 (Variation Generation)

---

#### 2.3 Smart Context Detection 🧠
**Priority: P1 (Should Have)**

**User Story**: "As a user, I want the AI to automatically optimize for my use case without me having to specify."

**Requirements**:
- Detect context clues in conversation:
  - "for my presentation" → corporate-appropriate
  - "for social media" → eye-catching, formatted
  - "for print" → high contrast
  - "profile picture" → portrait orientation, centered subject
  - "logo" → simple, scalable
- Auto-adjust size, style hints, composition
- Inform user of optimizations made

**Example**:
```
User: "Create a hero image for my landing page"

AI: "I've detected this is for web use. I'm optimizing for:
- Landscape format (1536x1024) for wide displays
- Bold, immediately engaging composition
- Web-optimized color palette
- Clear focal point for text overlay zones

[Generates optimized image]"
```

**Implementation**:
- Keyword detection in prompt
- Context-aware defaults:
  - Size selection
  - Style adjustments
  - Composition hints
- Transparent to user (explain what was done)

**Success Metrics**:
- Correct context detection 85%+ of time
- Auto-optimizations improve output appropriately
- Users appreciate not having to specify technical details

**Dependencies**: None

---

### **TIER 3: ADVANCED WORKFLOWS** (Weeks 5-8)
*Power features for professional and creative users*

#### 3.1 Multi-Image Sequences & Storyboarding 📽️
**Priority: P2 (Nice to Have)**

**User Story**: "As a designer/storyteller, I want to generate sequences of images that follow a narrative or emotional arc."

**Requirements**:
- New tool: `openai_generate_sequence`
- Input: list of 3-6 prompts or emotional states
- Output: sequence of images with visual continuity
- Can specify transition type: `smooth`, `dramatic`, `evolving`
- Maintains visual elements across frames (color palette, composition)

**Example**:
```python
prompts = [
    "Peaceful forest at dawn",
    "Storm clouds gathering",
    "Intense lightning storm",
    "Rainbow emerging after rain"
]

# Generates 4-image sequence with visual continuity
```

**Implementation**:
- Loop through prompts in order
- Pass previous image file_id as reference for continuity
- Conversation context maintains visual coherence
- Save as numbered sequence

**Success Metrics**:
- Sequences show visual continuity
- Useful for storyboarding, presentations, animations
- Processing time reasonable (parallel where possible)

**Dependencies**: 1.2 (Variations), Conversation context

---

#### 3.2 Compositional DNA Library 🧬
**Priority: P2 (Nice to Have)**

**User Story**: "As a power user, I want to save and reuse successful visual elements from my generations."

**Requirements**:
- Extract "DNA" from successful images:
  - Color palette
  - Composition style
  - Mood/atmosphere
  - Technical style
- Store as reusable presets
- Apply DNA to new prompts
- Mix DNA from multiple sources

**Example**:
```
User: "Save this as DNA preset 'sunset-mood'"

[Later]

User: "Generate a cityscape using 'sunset-mood' DNA"
AI: [Applies saved color palette and mood to new subject]
```

**Implementation**:
- Use vision model to analyze image and extract characteristics
- Store as structured data (JSON)
- Template system to inject DNA into new prompts
- User-managed preset library

**Success Metrics**:
- DNA extraction produces useful, reusable attributes
- Applying DNA measurably affects new images
- Users build personal style libraries

**Dependencies**: File ID system, conversation store

---

#### 3.3 Critique & Iterate Mode 🎯
**Priority: P2 (Nice to Have)**

**User Story**: "As someone learning visual design, I want the AI to critique my images and suggest specific improvements."

**Requirements**:
- After generation, optionally enable critique mode
- AI analyzes from multiple perspectives:
  - Composition balance
  - Color theory
  - Technical execution
  - Emotional impact
- Provides 3-4 specific, actionable suggestions
- Can auto-apply selected critiques

**Example**:
```
AI: "I've generated your image. Enable critique mode? (y/n)"

User: "y"

AI: "Analysis of your image:

✅ Strong: Clear focal point, good use of rule of thirds
⚠️  Could improve:
  1. Color harmony: Add complementary orange tones to balance blues
  2. Depth: Slightly blur background for more separation
  3. Lighting: Add rim light on subject for drama

Apply suggestions? (all/1/2/3/none)"

User: "1,3"

AI: [Regenerates with color harmony and rim light adjustments]
```

**Implementation**:
- Use vision-capable model to analyze generated image
- Template-based critique framework
- Translate critiques to prompt modifications
- Regenerate with adjustments

**Success Metrics**:
- Critiques are specific and actionable
- Applying critiques measurably improves images
- Educational value for users

**Dependencies**: Vision model access, conversation context

---

#### 3.4 Parallel Universe Generation 🌍
**Priority: P2 (Nice to Have)**

**User Story**: "As a creative, I want to see how my concept would look in completely different artistic styles or contexts."

**Requirements**:
- Input: base concept/subject
- Output: same subject in 4-6 radically different styles
- Styles span: time periods, art movements, cultures, mediums
- Each is a complete reinterpretation, not just a filter

**Example**:
```
User: "Show me 'jazz musician' across different styles"

AI generates:
1. Renaissance oil painting
2. 1960s psychedelic poster
3. Japanese woodblock print
4. Modern 3D render
5. Film noir photography
6. Abstract expressionism

Each with appropriate context and styling.
```

**Implementation**:
- Predefined style transformation templates
- Base prompt + style overlay
- Generate all in parallel (n=6 or separate calls)
- Group by theme for presentation

**Success Metrics**:
- Styles are visually distinct and authentic
- Same subject recognizable across variations
- Sparks creative inspiration

**Dependencies**: 1.2 (Variations), Style system

---

## 📋 Recommended Build Sequence

### Phase 1: Core Enhancements (Weeks 1-2)
**Goal**: Enable basic exploration without breaking current workflow

```
Week 1:
├─ 1.1 Mode Selection (2 days)
├─ 1.2 Variation Generation (2 days)
└─ Testing & Integration (1 day)

Week 2:
├─ 1.3 Style Presets (2 days)
├─ Documentation Updates (1 day)
└─ User Testing (2 days)
```

**Deliverable**: v3.1 with modes, variations, and presets

---

### Phase 2: Guided Experience (Weeks 3-4)
**Goal**: Add intelligence and workflow guidance

```
Week 3:
├─ 2.1 Guided Mode (3 days)
└─ 2.3 Context Detection (2 days)

Week 4:
├─ 2.2 Divergent Exploration (3 days)
├─ Testing & Refinement (1 day)
└─ Documentation (1 day)
```

**Deliverable**: v3.2 with guided workflows and smart defaults

---

### Phase 3: Advanced Features (Weeks 5-8)
**Goal**: Power features for professional use

```
Weeks 5-6:
├─ 3.1 Sequence Generation (4 days)
├─ 3.2 DNA Library (4 days)
└─ Testing (2 days)

Weeks 7-8:
├─ 3.3 Critique Mode (4 days)
├─ 3.4 Parallel Universe (3 days)
└─ Polish & Documentation (3 days)
```

**Deliverable**: v4.0 with professional workflow tools

---

## 🏗️ Technical Architecture Changes

### New Conversation State Structure
```python
conversation_store = {
    "conv_123": {
        "mode": "explorer",
        "messages": [...],
        "generations": [
            {
                "file_id": "file-xyz",
                "path": "/Downloads/image_v1.png",
                "variation_number": 1,
                "metadata": {
                    "style_preset": "photorealistic",
                    "user_preferences": {...}
                }
            }
        ],
        "dna_presets": {...},  # Phase 3
        "context": "web_design"  # Smart detection
    }
}
```

### New Tools to Add
```python
# Phase 2
@mcp.tool("openai_explore_variations")
@mcp.tool("openai_guided_generation")

# Phase 3
@mcp.tool("openai_generate_sequence")
@mcp.tool("openai_save_dna_preset")
@mcp.tool("openai_apply_dna")
@mcp.tool("openai_critique_image")
```

### Parameter Expansions
```python
class ConversationalImageInput(BaseModel):
    # Existing fields...

    # Phase 1 additions
    mode: Optional[GenerationMode] = Field(default=GenerationMode.QUICK)
    variations: Optional[int] = Field(default=1, ge=1, le=4)
    style_preset: Optional[str] = Field(default=None)

    # Phase 2 additions
    enable_guidance: Optional[bool] = Field(default=False)
    context_hint: Optional[str] = Field(default=None)  # Override detection

    # Phase 3 additions
    apply_dna_preset: Optional[str] = Field(default=None)
    enable_critique: Optional[bool] = Field(default=False)
```

---

## ✅ Success Criteria by Phase

### Phase 1 Success Metrics
- [ ] Users can generate 1-4 variations in single request
- [ ] Mode selection changes experience appropriately
- [ ] 8 style presets work reliably
- [ ] All images save correctly with proper naming
- [ ] No regression in basic functionality
- [ ] Documentation updated and clear

### Phase 2 Success Metrics
- [ ] Guided mode asks relevant questions 80%+ of time
- [ ] Context detection accurate in 85%+ of cases
- [ ] Divergent mode produces visually distinct options
- [ ] User satisfaction increases vs. Phase 1
- [ ] Response times remain acceptable (<30s for 3 images)

### Phase 3 Success Metrics
- [ ] Sequences show visual continuity
- [ ] DNA presets produce consistent results
- [ ] Critiques are actionable and educational
- [ ] Parallel universe spans genuinely different styles
- [ ] Power users adopt advanced features
- [ ] NPS score >50

---

## 🚧 Technical Considerations

### API Cost Management
- Variations multiply cost (n=3 → 3x cost)
- Implement cost warnings for >2 variations
- Consider caching for identical prompts
- Rate limiting for expensive operations

### Performance Optimization
- Parallel generation where possible
- Async/await for all API calls
- Stream responses for faster perceived performance
- Consider result caching (5-min TTL)

### Error Handling
- Graceful degradation if variation generation fails
- Fallback to simple mode if guided fails
- Clear error messages for API limits
- Retry logic for transient failures

### Storage & Cleanup
- Monitor Downloads folder size
- Optional auto-cleanup of old images
- Compress conversation_store periodically
- Limit DNA preset storage

---

## 📝 Documentation Updates Needed

### User-Facing
- [ ] Update README with new modes and parameters
- [ ] Create USAGE_GUIDE.md with examples
- [ ] Add style preset catalog with examples
- [ ] Video tutorials for advanced features

### Developer-Facing
- [ ] API reference for all new parameters
- [ ] Architecture documentation
- [ ] Contribution guide for new presets
- [ ] Testing guide for new features

---

## 🎨 Design Principles

1. **Progressive Disclosure**: Simple by default, powerful when needed
2. **No Breaking Changes**: All new features are opt-in
3. **Fast Path First**: Quick mode must stay fast (1 image, 1 call)
4. **Transparency**: Always explain what the AI is doing
5. **User Control**: AI suggests, user decides
6. **Educational**: Help users understand visual design
7. **Cost Awareness**: Make users aware of multi-generation costs

---

## 🤔 Open Questions to Resolve

### Before Phase 1
- [ ] Should variations have slight prompt variations or be identical?
- [ ] Max variations: 4 or allow up to 10?
- [ ] Default mode: quick or prompt user to choose?
- [ ] Style preset naming: technical or descriptive?

### Before Phase 2
- [ ] How many questions in guided mode? (1-2 or up to 3?)
- [ ] Should context detection override user's size choice?
- [ ] Divergent mode: truly different prompts or n>1 with varied seed?

### Before Phase 3
- [ ] DNA presets: per-conversation or global?
- [ ] Critique mode: auto-enable after N generations?
- [ ] Sequence generation: series or parallel?
- [ ] Should we support custom style preset creation?

---

## 🚀 Quick Wins to Start Tomorrow

**Highest ROI, Lowest Effort**:

1. **Style Presets (1 day)**: Just a dictionary and string concatenation
2. **Variations Parameter (1 day)**: Already supported by API, just add param
3. **Mode Selection (2 days)**: Routing logic, minimal new code

These 3 features immediately make the tool 5x more useful for <1 week of work.

---

## 💡 Future Vision (Post v4.0)

- **AI Art Director**: Multi-image campaigns with cohesive visual identity
- **Collaboration Mode**: Multiple users contributing to shared vision
- **Style Transfer**: "Make it look like this image" with reference upload
- **Animation Frames**: Generate frames for simple animations
- **Brand Kits**: Enterprise feature for brand-consistent generation
- **Fine-tuning Integration**: Custom models for specific visual styles

---

**Next Step**: Review and approve Phase 1 scope, then begin implementation of Quick Wins.
