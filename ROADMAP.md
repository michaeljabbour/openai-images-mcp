# OpenAI Images MCP - Product Roadmap

> **Vision:** The conversational image generation MCP server that helps users discover and refine their visual ideas through dialogue.
>
> **Last Updated:** January 24, 2025
> **Current Version:** 4.0.0 (Phase 1 Complete)

---

## 🎯 Core Value Proposition

**Transform image generation from prompt-and-pray into a guided creative conversation.**

Most image generation tools require users to know exactly what they want and how to describe it. This MCP server acts as a **creative consultant** that helps users:
- Explore their visual ideas through dialogue
- Articulate their vision with better prompts
- Refine iteratively through natural conversation
- Discover styles and approaches they hadn't considered

### What Makes This Different

Unlike other image MCP servers that are simple API wrappers, this server focuses on the **conversation before and during generation**:

| Other MCP Servers | This Server |
|-------------------|-------------|
| User provides prompt → Generate | Dialogue → Refined prompt → Generate |
| Single-shot generation | Iterative exploration |
| User must know what they want | Server helps discover what they want |
| Technical prompt engineering required | Natural conversation |
| No context between sessions | Conversation memory and learning |

---

## 🧭 Design Principles

1. **Dialogue-First** - Always engage before generating
2. **Context-Aware** - Remember conversation history and preferences
3. **Local-First** - Runs on user's machine with their API keys
4. **Simple & Focused** - Do one thing exceptionally well
5. **Claude-Native** - Designed for seamless Claude Desktop integration

---

## 🚀 Roadmap Phases

### ✅ Phase 1: Conversational Foundation (COMPLETE)

**Status:** Complete - Released January 2025
**Goal:** Transform from direct generation to dialogue-guided creation

#### 1.1 Pre-Generation Dialogue System
**Priority:** P0

Implement conversational discovery before image generation:

**Features:**
- Clarifying questions about subject, style, mood, composition
- Interactive style exploration (photorealistic, artistic, abstract, etc.)
- Color palette discussion and preferences
- Use case understanding (presentation, social media, art, reference)
- Detail level negotiation (minimalist vs. detailed)

**Implementation:**
```python
class DialogueMode(str, Enum):
    QUICK = "quick"           # 1-2 questions, fast generation
    GUIDED = "guided"         # 3-5 questions, balanced
    EXPLORER = "explorer"     # Deep exploration, 5+ questions

@mcp.tool("openai_conversational_image")
async def openai_conversational_image(params: ConversationalImageInput):
    """Enhanced with dialogue mode support"""
    # If dialogue_mode enabled, engage in pre-generation conversation
    # Use GPT-4 to ask clarifying questions
    # Build enhanced prompt from conversation
    # Generate with refined understanding
```

**Success Criteria:** ✅ **COMPLETE**
- ✅ Users can choose dialogue depth (quick/guided/explorer/skip)
- ✅ System asks relevant, contextual questions based on image type
- ✅ Generated prompts are measurably better than user's initial input (quality scoring 0-100)
- ✅ Conversation feels natural, not like a form

---

#### 1.2 Prompt Enhancement Engine
**Priority:** P0

Help users articulate their vision with better prompts:

**Features:**
- Automatic prompt enrichment from conversation
- Style keyword suggestions based on intent
- Technical parameter recommendations (size, composition)
- Prompt quality scoring and improvement suggestions
- Examples of similar successful prompts

**Implementation:**
```python
class PromptEnhancer:
    def analyze_prompt(self, user_prompt: str) -> PromptAnalysis:
        """Analyze prompt quality and suggest improvements"""
        
    def enrich_from_dialogue(self, conversation: List[Message]) -> str:
        """Build enhanced prompt from conversation context"""
        
    def suggest_variations(self, base_prompt: str) -> List[str]:
        """Generate prompt variations for exploration"""
```

**Success Criteria:** ✅ **COMPLETE**
- ✅ Enhanced prompts produce better results than raw user input
- ✅ Users understand why prompts were enhanced (quality scoring shown)
- ✅ Suggestions are contextually relevant (9 image types detected)
- ✅ Prompt quality scores correlate with completeness (0-100 scale)

---

#### 1.3 Conversation Context Management
**Priority:** P0

Maintain coherent conversation state across sessions:

**Features:**
- Persistent conversation storage (encrypted)
- Session resumption with full context
- Preference learning from past conversations
- Conversation search and retrieval
- Export conversation history

**Implementation:**
```python
class ConversationStore:
    def save_conversation(self, conv_id: str, messages: List[Message]):
        """Persist conversation with encryption"""
        
    def load_conversation(self, conv_id: str) -> Conversation:
        """Resume previous conversation with full context"""
        
    def extract_preferences(self, user_id: str) -> UserPreferences:
        """Learn style preferences from conversation history"""
```

**Success Criteria:** ✅ **COMPLETE**
- ✅ Conversations persist across Claude Desktop restarts (local JSON storage)
- ✅ Users can resume previous sessions seamlessly
- ✅ Conversation search and listing implemented
- ⚠️ Encryption and preference learning deferred to Phase 3

---

## 🎯 Recommended Next Steps

Based on Phase 1 completion, here are the recommended priorities:

### Option A: User Feedback & Refinement (Recommended)
**Duration:** 2-4 weeks
**Rationale:** Gather real user feedback before building more features

**Activities:**
1. Deploy to early users and collect feedback
2. Monitor usage patterns and pain points
3. Identify which Phase 2 features users actually need
4. Fix bugs and polish existing features based on feedback
5. Document common workflows and use cases

**Success Metrics:**
- 10+ active users providing feedback
- Clear understanding of most-wanted features
- Bug backlog prioritized
- Usage analytics showing adoption patterns

### Option B: Enhanced Refinement Experience
**Duration:** 1-2 weeks
**Rationale:** Improve the most-used workflow immediately

**Features:**
1. Better "make it more/less X" commands
2. Undo/redo for refinements
3. Refinement strength controls
4. Visual refinement history

**Value:** Direct improvement to core user workflow

### Option C: Batch Variations
**Duration:** 2-3 weeks
**Rationale:** Generate multiple options to choose from

**Features:**
1. Generate 2-4 variations from one prompt
2. Side-by-side comparison
3. Select and refine preferred variation

**Value:** Helps users explore options without multiple conversations

---

### Phase 2: Advanced Generation Capabilities

**Status:** Not Started
**Goal:** Enable sophisticated generation workflows through conversation

#### 2.1 Batch Generation with Variations
**Priority:** P1

Generate multiple variations from a single conversation:

**Features:**
- Generate 2-4 variations from one prompt
- Automatic variation strategies (color, composition, style)
- Conversational selection of preferred direction
- Refinement of selected variation
- Side-by-side comparison support

**Implementation:**
```python
@mcp.tool("openai_generate_variations")
async def generate_variations(
    prompt: str,
    variation_strategy: str,  # "color", "composition", "style", "mixed"
    num_variations: int = 3
) -> List[ImageResult]:
    """Generate multiple variations with different approaches"""
```

**Success Criteria:**
- ✅ Variations are meaningfully different
- ✅ Users can articulate preferences between variations
- ✅ Refinement continues from selected variation
- ✅ Batch generation is faster than sequential

---

#### 2.2 Style Transfer & Reference Images
**Priority:** P1

Use reference images to guide generation through conversation:

**Features:**
- Upload reference image for style extraction
- Conversational discussion of what to adopt from reference
- Selective style transfer (color only, composition only, full style)
- Multiple reference blending
- "Make it like this, but..." workflows

**Implementation:**
```python
@mcp.tool("openai_extract_style")
async def extract_style(
    reference_image_path: str,
    aspects: List[str]  # ["color", "composition", "mood", "technique"]
) -> StyleProfile:
    """Extract style attributes from reference image"""

@mcp.tool("openai_apply_style")
async def apply_style(
    subject_prompt: str,
    style_profile: StyleProfile,
    strength: float = 0.7
) -> ImageResult:
    """Apply extracted style to new subject"""
```

**Success Criteria:**
- ✅ Style extraction captures meaningful attributes
- ✅ Users can selectively apply style aspects
- ✅ Results reflect reference influence appropriately
- ✅ Conversation guides style application decisions

---

#### 2.3 Prompt Template Library
**Priority:** P1

Contextual prompt templates that accelerate creation:

**Features:**
- 20+ curated templates for common use cases
- Contextual template suggestions based on conversation
- Customizable template parameters
- User-created template saving
- Template effectiveness tracking

**Categories:**
- **Presentation**: Title slides, section headers, diagrams
- **Marketing**: Product shots, social media, ads
- **Art**: Portraits, landscapes, abstract, concept art
- **Technical**: Diagrams, infographics, technical illustrations
- **Reference**: Character design, environment concepts, object studies

**Implementation:**
```yaml
# templates/presentation/title_slide.yaml
name: "Presentation Title Slide"
category: "presentation"
description: "Professional title slide with brand-appropriate styling"
template: |
  {title_text} text logo, {style} lettering,
  {color_scheme} gradient, {accent_elements},
  {background_color} background, modern typography,
  professional presentation design
parameters:
  - name: title_text
    type: string
    prompt: "What's the title text?"
  - name: style
    type: choice
    options: ["bold artistic brush", "clean sans-serif", "elegant serif"]
    prompt: "What lettering style?"
  - name: color_scheme
    type: string
    prompt: "What colors? (e.g., 'cyan through cream to magenta')"
```

**Success Criteria:**
- ✅ Templates reduce time to good results
- ✅ Suggestions are contextually relevant
- ✅ Users can customize templates through conversation
- ✅ Template library grows through user contributions

---

#### 2.4 Iterative Refinement Workflows
**Priority:** P0

Make refinement feel like natural conversation:

**Features:**
- "Make it more/less [attribute]" commands
- Incremental adjustments with visual feedback
- Undo/redo for refinement steps
- Refinement history visualization
- Automatic prompt diff showing what changed

**Implementation:**
```python
class RefinementEngine:
    def apply_adjustment(
        self,
        current_image: str,
        adjustment: str,  # "darker", "more detailed", "warmer colors"
        strength: float = 0.5
    ) -> ImageResult:
        """Apply conversational refinement"""
        
    def show_refinement_path(self, conversation_id: str) -> RefinementHistory:
        """Visualize the refinement journey"""
```

**Success Criteria:**
- ✅ Refinements feel intuitive and natural
- ✅ Users can articulate changes in plain language
- ✅ System interprets intent correctly >80% of time
- ✅ Refinement history helps users understand evolution

---

### Phase 3: Intelligence & Learning

**Status:** Not Started
**Goal:** Make the server smarter through usage and feedback

#### 3.1 Semantic Prompt Caching
**Priority:** P1

Intelligent caching based on semantic similarity:

**Features:**
- Embedding-based prompt similarity detection
- Cache hits for semantically similar prompts
- Conversation context included in cache key
- Configurable similarity threshold
- Cache analytics and hit rate tracking

**Implementation:**
```python
class SemanticCache:
    def get_similar_result(
        self,
        prompt: str,
        conversation_context: List[Message],
        similarity_threshold: float = 0.85
    ) -> Optional[CachedResult]:
        """Find cached results for similar prompts"""
        
    def cache_result(
        self,
        prompt: str,
        context: List[Message],
        result: ImageResult
    ):
        """Cache with semantic embeddings"""
```

**Performance Targets:**
- Cache hit rate: >20% within 1 week of usage
- Similarity threshold: 0.85 (configurable)
- Lookup latency: <100ms
- Storage: Embeddings + metadata only (not images)

**Success Criteria:**
- ✅ Cache reduces API costs by >15%
- ✅ Cached results are contextually appropriate
- ✅ No false positives (wrong images served)
- ✅ Performance impact is negligible

---

#### 3.2 Visual DNA Extraction
**Priority:** P2

Learn and reuse visual styles from successful generations:

**Features:**
- Extract style "DNA" from generated images
- Save as reusable style presets
- Apply DNA to new subjects
- Personal style library
- DNA mixing (combine multiple styles)

**Implementation:**
```python
@mcp.tool("openai_extract_dna")
async def extract_visual_dna(
    image_file_id: str,
    name: str,
    aspects: List[str] = ["color", "composition", "mood", "technique"]
) -> VisualDNA:
    """Extract reusable style attributes from successful image"""

class VisualDNA(BaseModel):
    id: str
    name: str
    color_palette: List[str]  # Hex codes
    composition_style: str
    mood_descriptors: List[str]
    technical_attributes: Dict[str, Any]
    
@mcp.tool("openai_apply_dna")
async def apply_visual_dna(
    subject_prompt: str,
    dna_id: str,
    strength: float = 0.7
) -> ImageResult:
    """Apply saved DNA to new generation"""
```

**Success Criteria:**
- ✅ DNA extraction produces reusable attributes
- ✅ Applying DNA measurably affects new images
- ✅ Users build personal style libraries
- ✅ DNA mixing creates coherent hybrid styles

---

#### 3.3 Quality Feedback Loop
**Priority:** P2

Learn from user feedback to improve suggestions:

**Features:**
- Simple thumbs up/down on results
- Detailed feedback on what worked/didn't
- Preference learning over time
- Automatic prompt adjustment based on feedback
- Feedback analytics and insights

**Implementation:**
```python
@mcp.tool("openai_rate_image")
async def rate_image(
    image_file_id: str,
    rating: int,  # 1-5
    feedback: Optional[str] = None
) -> None:
    """Provide feedback on generated image"""

class FeedbackEngine:
    def learn_preferences(self, user_feedback: List[Feedback]) -> UserPreferences:
        """Extract preferences from feedback history"""
        
    def adjust_prompts(self, prompt: str, preferences: UserPreferences) -> str:
        """Adjust prompts based on learned preferences"""
```

**Success Criteria:**
- ✅ Feedback collection is frictionless
- ✅ Preferences improve prompt quality over time
- ✅ Users see their feedback reflected in suggestions
- ✅ System adapts to individual creative styles

---

#### 3.4 Conversation History Search
**Priority:** P2

Find and reuse past conversations and results:

**Features:**
- Full-text search across conversations
- Semantic search for similar discussions
- Filter by date, style, use case
- Quick access to successful prompts
- Conversation bookmarking

**Implementation:**
```python
@mcp.tool("openai_search_conversations")
async def search_conversations(
    query: str,
    search_type: str = "semantic",  # "text" or "semantic"
    filters: Optional[Dict] = None
) -> List[ConversationResult]:
    """Search conversation history"""
```

**Success Criteria:**
- ✅ Search returns relevant results
- ✅ Semantic search finds conceptually similar conversations
- ✅ Users can quickly find past successful prompts
- ✅ Search performance is <500ms

---

### Phase 4: Polish & Optimization

**Status:** Not Started
**Goal:** Production-ready quality and performance

#### 4.1 Performance Optimization
**Priority:** P0

**Targets:**
- P95 latency: <15s for single image generation
- Cache hit rate: >20% after 1 week
- Memory usage: <500MB for conversation store
- Conversation load time: <200ms

**Optimizations:**
- Parallel API calls for batch generation
- Lazy loading of conversation history
- Efficient embedding storage
- Connection pooling and reuse

---

#### 4.2 Error Handling & Resilience
**Priority:** P0

**Features:**
- Graceful degradation when APIs are unavailable
- Retry logic with exponential backoff
- Clear error messages with recovery suggestions
- Automatic fallback to simpler modes
- Circuit breaker for API failures

---

#### 4.3 Documentation & Examples
**Priority:** P0

**Deliverables:**
- Comprehensive user guide with examples
- Video walkthrough of key workflows
- Prompt engineering best practices
- Troubleshooting guide
- API reference documentation

---

#### 4.4 Testing & Quality Assurance
**Priority:** P0

**Test Coverage:**
- Unit tests for core functions (>80% coverage)
- Integration tests for API interactions
- End-to-end workflow tests
- Performance benchmarks
- User acceptance testing

---

## 📊 Success Metrics

### User Engagement
- **Conversation Depth**: Average 4+ messages before generation
- **Refinement Rate**: 60% of users refine at least once
- **Session Length**: Average 15+ minutes per session
- **Return Rate**: 70% of users return within 7 days

### Quality Metrics
- **Prompt Enhancement**: 80% of enhanced prompts rated better than original
- **First-Time Success**: 40% of first generations meet user needs
- **Refinement Success**: 80% satisfaction after 2-3 refinements
- **Cache Hit Rate**: >20% within 1 week of usage

### Performance Metrics
- **Generation Latency**: P95 <15s
- **Conversation Load**: P95 <200ms
- **Cache Lookup**: P95 <100ms
- **Memory Usage**: <500MB steady state

---

## 🎁 Phase 1 Bonus Features

These features were added during Phase 1 implementation based on real needs:

### Image Quality Verification System
**Added:** January 2025
**Rationale:** User reported images not matching prompts (e.g., TRON scene generating street signs)

**Features:**
- Automatic verification checklist before delivery
- Type-specific requirements (logo quality, text presence, colors, etc.)
- Confidence scoring (0-100%)
- Helpful reminders to review key requirements
- Verification results saved to conversation storage

**Impact:** Helps catch mismatches before delivery, though Phase 1 doesn't block on failures

### Organized Downloads Folder
**Added:** January 2025
**Features:**
- Images save to `Downloads/images/` subfolder (not main Downloads)
- Cross-platform support (macOS/Linux/Windows)
- Keeps Downloads folder organized
- Auto-creates directory on first use

### Enhanced Tool Descriptions
**Added:** January 2025
**Rationale:** Needed clarity on when to use each tool

**Improvements:**
- Clear "USE THIS TOOL when..." guidelines
- Direct vs conversational generation criteria
- Better examples in docstrings

---

## 🎯 Out of Scope (Explicitly NOT Building)

To maintain focus, the following are **explicitly excluded** from this roadmap:

### ❌ Enterprise Features
- Multi-user authentication
- Team workspaces
- Role-based access control
- Approval workflows
- Audit logs and compliance reporting
- SSO integration

### ❌ Monetization
- Stripe integration
- Subscription management
- Usage quotas and billing
- Payment processing
- Pricing tiers

### ❌ Social Features
- Public gallery
- Community sharing
- User profiles
- Likes/comments
- Leaderboards

### ❌ Platform Integrations
- Figma plugin
- Notion integration
- Slack bot
- DAM integrations
- Third-party exports

### ❌ Why These Are Out of Scope

**MCP servers are local tools** that run on individual users' machines to extend Claude Desktop. They are not:
- Web applications with users and databases
- SaaS platforms with subscriptions
- Social networks with communities
- Enterprise software with compliance features

Building these features would transform this from a **focused MCP server** into a **complex platform** that competes with Midjourney, Canva, and Adobe—which is not the goal.

---

## 🔄 Version History

### Version 4.0 (Planned)
- Conversational dialogue system
- Prompt enhancement engine
- Advanced refinement workflows
- Semantic caching and learning

### Version 3.0 (Current)
- Full-quality PNG output
- Conversational image generation
- GPT-Image-1 exclusive support
- Simplified codebase

### Version 2.0
- GPT-Image-1 support via Responses API
- Multi-turn editing capabilities
- File ID support

### Version 1.0
- Initial release with DALL-E 2/3
- Direct API image generation

---

## 📝 Contributing

This roadmap is a living document. Feedback and suggestions are welcome through:
- GitHub Issues for feature requests
- Pull requests for roadmap improvements
- Discussions for strategic direction

**Guiding Question:** Does this feature make the **conversational image generation experience** better? If not, it probably doesn't belong in this MCP server.

