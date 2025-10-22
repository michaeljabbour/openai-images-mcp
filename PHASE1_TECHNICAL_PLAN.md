# Phase 1: Conversational Dialogue System - Technical Plan

> **Branch**: `feature/phase1-conversational-dialogue`
> **Focus**: User-facing conversational features following MCP best practices

---

## MCP Security & Best Practices Compliance

### Official Guidelines Applied

Based on [MCP Security Best Practices](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices) and [Claude Code Security](https://docs.claude.com/en/docs/claude-code/security):

✅ **What We're Doing Right:**
- Using **stdio transport** (limits access to Claude Desktop only)
- **Environment variables** for API keys (no hardcoding)
- **No authentication system** (single-user, local-first)
- **Minimal permissions** (only what's needed for image generation)

✅ **Storage Best Practices:**
- **Local JSON files** for conversation persistence (common MCP pattern)
- Stored in user's home directory: `~/.openai-images-mcp/conversations/`
- Optional encryption for sensitive conversation data
- No centralized databases or cloud storage

✅ **Privacy by Design:**
- All data stays on user's machine
- User controls their own data through filesystem
- No data collection or telemetry
- Conversations can be deleted by user at any time

---

## Phase 1 Features (User-Facing)

### 1.1 Pre-Generation Dialogue System

**User Value:** Get better images through guided conversation before generation

#### Dialogue Modes

```python
class DialogueMode(str, Enum):
    QUICK = "quick"        # 1-2 questions, fast path
    GUIDED = "guided"      # 3-5 questions, balanced (default)
    EXPLORER = "explorer"  # Deep exploration, 5+ questions
    SKIP = "skip"          # Direct generation, no dialogue
```

**User Experience:**

```
User: "Create a logo for my tech startup"

[QUICK MODE]
Assistant: "Two quick questions:
  1. What vibe? (Professional, Innovative, Friendly)
  2. Colors in mind?"
→ 2 questions, then generate

[GUIDED MODE]
Assistant: "I'll help create your logo! A few questions:
  1. What does your startup do?
  2. Target audience?
  3. Preferred style? (Minimalist, Detailed, Abstract)
  4. Color palette?"
→ 4-5 questions, then generate

[EXPLORER MODE]
Assistant: "Let's explore thoroughly! Tell me about:
  1. Your startup's mission and values
  2. Who are your customers?
  3. Competitors you admire/avoid?
  4. Visual style preferences
  5. Typography direction
  6. Color psychology considerations"
→ Deep dive, then generate
```

#### Implementation

```python
# Add to ConversationalImageInput
class ConversationalImageInput(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

    # NEW: Dialogue system
    dialogue_mode: DialogueMode = DialogueMode.GUIDED
    dialogue_stage: Optional[str] = None
    user_responses: Optional[Dict[str, Any]] = None
```

**Dialogue Flow State Machine:**

```python
class DialogueStage(str, Enum):
    INITIAL = "initial"           # Ask first questions
    STYLE_EXPLORATION = "style"   # Explore visual style
    COLOR_MOOD = "color_mood"     # Discuss colors and mood
    DETAILS = "details"           # Finalize composition details
    READY = "ready"               # Generate with enhanced prompt

async def conduct_dialogue(
    prompt: str,
    mode: DialogueMode,
    stage: DialogueStage,
    responses: Dict[str, Any]
) -> Union[DialogueQuestion, EnhancedPrompt]:
    """
    Orchestrate multi-turn dialogue flow.
    Returns questions for user OR final enhanced prompt.
    """
```

---

### 1.2 Prompt Enhancement Engine

**User Value:** Automatically improve prompts based on dialogue and best practices

#### Features

1. **Quality Analysis**
   - Score prompts on completeness (0-100)
   - Identify missing elements (style, mood, colors, composition)
   - Provide actionable suggestions

2. **Dialogue-Based Enrichment**
   - Extract information from conversation
   - Build comprehensive prompts from user answers
   - Add technical quality keywords

3. **Contextual Enhancement**
   - Detect use case (logo, presentation, social media)
   - Optimize size and orientation automatically
   - Apply best practices for image type

**Example Enhancement:**

```
User input: "Create a coffee shop"
Dialogue responses:
  - Style: Modern industrial
  - Mood: Cozy and inviting
  - Colors: Warm browns, exposed brick
  - Details: Add plants, large windows

Enhanced prompt:
"Modern industrial coffee shop interior with cozy inviting atmosphere,
warm color palette featuring rich browns and natural wood tones,
exposed brick walls, abundant greenery with hanging plants,
large windows with natural lighting, comfortable seating areas,
contemporary design aesthetic, welcoming ambiance, professional
interior photography style"
```

#### Implementation

```python
class PromptEnhancer:
    def analyze_prompt(self, prompt: str) -> PromptAnalysis:
        """Analyze quality and identify gaps"""
        return PromptAnalysis(
            score=85,  # 0-100
            missing_elements=["color_palette", "mood"],
            suggestions=[
                "Consider adding color preferences",
                "Specify the mood or atmosphere"
            ]
        )

    def enrich_from_dialogue(
        self,
        original_prompt: str,
        conversation: List[Message]
    ) -> str:
        """Build enhanced prompt from dialogue context"""
        # Extract style, colors, mood, details from conversation
        # Combine into coherent, detailed prompt
        return enhanced_prompt
```

---

### 1.3 Conversation Context Management

**User Value:** Resume previous conversations, maintain context across sessions

#### Local Storage Pattern

Following **MCP best practice** for local persistence:

```python
# Storage location
~/.openai-images-mcp/
├── conversations/
│   ├── conv_abc123.json
│   ├── conv_def456.json
│   └── ...
├── preferences.json
└── cache/
    └── semantic_cache.db
```

**JSON Structure:**

```json
{
  "conversation_id": "conv_abc123",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:45:00Z",
  "messages": [
    {
      "role": "user",
      "content": "Create a logo for my tech startup",
      "timestamp": "2025-10-22T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "I'll help create your logo! A few questions...",
      "timestamp": "2025-10-22T10:30:15Z"
    }
  ],
  "metadata": {
    "dialogue_mode": "guided",
    "enhanced_prompt": "...",
    "generated_images": [
      {
        "file_id": "file-xyz",
        "path": "/Users/user/Downloads/openai_image_20251022_103045.png",
        "timestamp": "2025-10-22T10:30:45Z"
      }
    ]
  }
}
```

#### Optional Encryption

**User Control:** Encryption is optional for users with sensitive prompts

```python
class ConversationStore:
    def __init__(self, storage_dir: str = "~/.openai-images-mcp/conversations"):
        self.storage_dir = Path(storage_dir).expanduser()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.encryption_enabled = self._check_encryption_preference()

    def save_conversation(self, conv_id: str, data: dict):
        """Save conversation to local JSON file"""
        file_path = self.storage_dir / f"{conv_id}.json"

        if self.encryption_enabled:
            # Simple encryption using cryptography library
            encrypted = self._encrypt(json.dumps(data))
            file_path.write_bytes(encrypted)
        else:
            file_path.write_text(json.dumps(data, indent=2))

    def load_conversation(self, conv_id: str) -> dict:
        """Load conversation from local storage"""
        file_path = self.storage_dir / f"{conv_id}.json"

        if not file_path.exists():
            return None

        if self.encryption_enabled:
            encrypted = file_path.read_bytes()
            return json.loads(self._decrypt(encrypted))
        else:
            return json.loads(file_path.read_text())
```

**Encryption Decision:**
- **Default: No encryption** (most users don't need it)
- **Opt-in via config** for users with sensitive prompts
- Uses `cryptography` library (industry standard)
- Key derived from user's system (keychain/keyring)

---

## Implementation Steps

### Step 1: Add Dialogue Mode Parameter (Day 1)

```python
# Update openai_images_mcp.py

class DialogueMode(str, Enum):
    QUICK = "quick"
    GUIDED = "guided"
    EXPLORER = "explorer"
    SKIP = "skip"

class ConversationalImageInput(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

    # NEW
    dialogue_mode: DialogueMode = DialogueMode.GUIDED
    skip_dialogue: bool = False  # Quick override
```

### Step 2: Implement Dialogue State Machine (Day 1-2)

```python
# New file: dialogue_system.py

class DialogueManager:
    def __init__(self, mode: DialogueMode):
        self.mode = mode
        self.stage = DialogueStage.INITIAL

    async def get_next_question(
        self,
        prompt: str,
        responses: Dict[str, Any]
    ) -> Optional[DialogueQuestion]:
        """
        Returns next question to ask, or None if dialogue complete.
        """
        if self.mode == DialogueMode.SKIP:
            return None

        # Different question sequences based on mode
        questions = self._get_questions_for_mode()

        # Return next unanswered question
        return next_question_or_none

    def build_enhanced_prompt(
        self,
        original_prompt: str,
        responses: Dict[str, Any]
    ) -> str:
        """
        Combine original prompt with dialogue responses.
        """
        return enhanced_prompt
```

### Step 3: Implement Prompt Enhancement (Day 2-3)

```python
# New file: prompt_enhancement.py

class PromptEnhancer:
    def analyze_quality(self, prompt: str) -> PromptAnalysis:
        """Use GPT-4 to analyze prompt quality"""
        # Call GPT-4 with analysis prompt
        # Return structured analysis

    def suggest_improvements(self, analysis: PromptAnalysis) -> List[str]:
        """Generate specific improvement suggestions"""

    def enrich_prompt(
        self,
        original: str,
        dialogue_context: Dict[str, Any]
    ) -> str:
        """Build enhanced prompt from dialogue"""
        # Extract style, colors, mood from dialogue
        # Combine into coherent enhanced prompt
```

### Step 4: Implement Local Storage (Day 3-4)

```python
# New file: storage.py

class ConversationStore:
    def save(self, conv_id: str, data: dict):
        """Save to ~/.openai-images-mcp/conversations/{conv_id}.json"""

    def load(self, conv_id: str) -> Optional[dict]:
        """Load from local JSON file"""

    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""

    def delete(self, conv_id: str):
        """Delete conversation (user's right to be forgotten)"""
```

### Step 5: Integrate Into Main Tool (Day 4-5)

```python
# Modify openai_conversational_image()

@mcp.tool(name="openai_conversational_image")
async def openai_conversational_image(params: ConversationalImageInput):
    # Load conversation if continuing
    conversation = storage.load(params.conversation_id)

    # Check if dialogue needed
    if params.dialogue_mode != DialogueMode.SKIP and not params.skip_dialogue:
        # Conduct dialogue
        dialogue_manager = DialogueManager(params.dialogue_mode)
        question = await dialogue_manager.get_next_question(
            params.prompt,
            params.user_responses or {}
        )

        if question:
            # Return question to user
            return format_dialogue_question(question)

    # Build enhanced prompt
    enhanced_prompt = prompt_enhancer.enrich_prompt(
        params.prompt,
        params.user_responses or {}
    )

    # Generate with enhanced prompt
    result = await call_responses_api(enhanced_prompt, conversation_id)

    # Save conversation
    storage.save(conversation_id, conversation_data)

    return result
```

---

## Testing Plan

### Unit Tests

```python
# tests/test_dialogue_system.py
def test_quick_mode_asks_minimal_questions()
def test_guided_mode_progression()
def test_explorer_mode_depth()
def test_dialogue_stage_transitions()

# tests/test_prompt_enhancement.py
def test_quality_analysis()
def test_enhancement_from_dialogue()
def test_contextual_optimization()

# tests/test_storage.py
def test_save_and_load_conversation()
def test_conversation_listing()
def test_encryption_optional()
```

### Integration Tests

```python
# tests/test_integration.py
async def test_full_conversational_flow():
    """
    User: "Create a logo"
    → Dialogue questions
    → User responses
    → Enhanced prompt
    → Image generation
    → Conversation saved
    """

async def test_conversation_resumption():
    """
    Generate image in conv_123
    → Resume conv_123 later
    → Context preserved
    → Refinement works
    """
```

### Manual Testing Scenarios

1. **Quick Mode Flow**
   - Start conversation with quick mode
   - Answer 1-2 questions
   - Verify fast generation

2. **Guided Mode Flow**
   - Start with vague prompt
   - Answer 4-5 questions
   - Compare enhanced vs. original prompt quality

3. **Explorer Mode Flow**
   - Deep dive with 6+ questions
   - Verify comprehensive prompt building

4. **Conversation Resumption**
   - Generate image
   - Restart Claude Desktop
   - Resume conversation
   - Verify context preserved

---

## File Structure Changes

```
openai-images-mcp/
├── openai_images_mcp.py           # Main tool (updated)
├── dialogue_system.py             # NEW: Dialogue orchestration
├── prompt_enhancement.py          # NEW: Prompt quality analysis
├── storage.py                     # NEW: Local persistence
├── tests/
│   ├── test_dialogue_system.py   # NEW
│   ├── test_prompt_enhancement.py # NEW
│   └── test_storage.py           # NEW
└── README.md                      # Update with Phase 1 features
```

---

## Security Checklist

✅ **MCP Compliance:**
- [x] Using stdio transport (local-only access)
- [x] API keys from environment variables
- [x] No authentication system (single-user)
- [x] Minimal permissions (image generation only)
- [x] Local file storage (~/.openai-images-mcp/)

✅ **Privacy:**
- [x] All data stays on user's machine
- [x] Optional encryption for sensitive conversations
- [x] User controls data deletion
- [x] No telemetry or data collection

✅ **Dependencies:**
- [x] No new external dependencies (use stdlib where possible)
- [x] Optional: `cryptography` for encryption (if user enables)

---

## Success Criteria

### User-Facing Metrics

- [ ] Users can choose dialogue depth (quick/guided/explorer)
- [ ] Dialogue feels natural and helpful (not robotic)
- [ ] Enhanced prompts produce measurably better images
- [ ] First-time success rate improves 2x (vs. direct generation)
- [ ] Users can resume conversations seamlessly

### Technical Metrics

- [ ] All tests pass (unit + integration)
- [ ] No performance regression (dialogue adds <2s overhead)
- [ ] Conversation storage <100KB per conversation
- [ ] Zero security vulnerabilities

---

## Timeline

**Week 1 (Days 1-5):**
- Day 1: Dialogue mode parameter + state machine skeleton
- Day 2: Basic dialogue flow (guided mode)
- Day 3: Prompt enhancement engine
- Day 4: Local storage implementation
- Day 5: Integration + basic testing

**Week 2 (Days 6-10):**
- Day 6: Quick mode + explorer mode
- Day 7: Comprehensive testing
- Day 8: Documentation updates
- Day 9: Manual testing + bug fixes
- Day 10: PR review + merge

---

## Next Steps (After Phase 1)

- **Phase 2:** Batch generation with variations
- **Phase 3:** Semantic caching and visual DNA extraction

But first: **Let's nail the conversational dialogue experience!** 🚀
