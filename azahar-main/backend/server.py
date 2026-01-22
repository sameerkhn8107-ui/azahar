from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import re
import random
from groq import Groq

ROOT_DIR = Path(__file__).parent

load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

@app.get("/")
async def root():
    return {"message": "Backend is running"}

# API Keys
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
print(f"Groq API Key: {GROQ_API_KEY is not None}")
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

groq_client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== Models ==============

class ChatMessage(BaseModel):
    role: str
    content: str

class UserMemory(BaseModel):
    preferred_name: Optional[str] = None
    language_style: Optional[str] = None
    interests: Optional[List[str]] = []
    skill_level: Optional[str] = None
    goals: Optional[List[str]] = []
    personal_facts: Optional[List[str]] = []
    communication_preferences: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_name: str = "friend"
    conversation_id: Optional[str] = None
    user_memory: Optional[UserMemory] = None
    active_mode: Optional[str] = None

class ExtractMemoryRequest(BaseModel):
    messages: List[ChatMessage]
    current_memory: Optional[UserMemory] = None

class ExtractMemoryResponse(BaseModel):
    updated_memory: UserMemory
    extracted_facts: List[str]

# ============== Startup Game Data ==============

TARGET_AUDIENCES = [
    "College Students", "Working Professionals", "Stay-at-home Parents", "Senior Citizens",
    "Small Business Owners", "Freelancers", "Gamers", "Fitness Enthusiasts", "Teachers",
    "Healthcare Workers", "Farmers", "Artists & Creators", "Restaurant Owners", "NGOs",
    "E-commerce Sellers", "Real Estate Agents", "Event Planners", "Pet Owners",
    "Travelers", "Remote Workers", "Gen Z Consumers", "Homemakers", "Factory Workers",
    "Delivery Drivers", "Content Creators", "Music Artists", "Sports Coaches"
]

PAIN_POINTS = [
    "Time Management", "High Costs", "Lack of Trust", "Information Overload",
    "Poor Customer Service", "Difficulty Finding Jobs", "Mental Health Struggles",
    "Language Barriers", "Complex Regulations", "Loneliness & Isolation",
    "Skill Gaps", "Cash Flow Problems", "Marketing Challenges", "Data Security",
    "Work-Life Balance", "Health Tracking", "Education Access", "Networking",
    "Document Management", "Communication Gaps", "Quality Control", "Hiring Talent",
    "Customer Retention", "Product Discovery", "Decision Fatigue"
]

TECH_TOOLS = [
    "AI Chatbots", "WhatsApp Automation", "Mobile App", "SaaS Platform",
    "Blockchain", "AR/VR", "Voice Assistants", "No-Code Tools", "API Marketplace",
    "Subscription Model", "IoT Sensors", "Machine Learning", "Computer Vision",
    "NLP Processing", "Cloud Computing", "Edge Computing", "5G Networks",
    "Digital Twins", "Smart Contracts", "Recommendation Engine", "Data Analytics",
    "Robotic Process Automation", "Geolocation Services", "Payment Gateway",
    "Video Streaming", "Social Commerce", "Gamification"
]

def spin_cards():
    """Randomly select one item from each category"""
    return {
        "audience": random.choice(TARGET_AUDIENCES),
        "pain_point": random.choice(PAIN_POINTS),
        "tech": random.choice(TECH_TOOLS)
    }

# ============== ChatGPT Style System Prompts ==============

def get_learn_mode_prompt(user_name: str) -> str:
    return f"""You are Nex, an expert educator and close friend having a conversation with {user_name}.

COMMUNICATION STYLE:
- Use clear, natural English like ChatGPT does
- Be conversational, warm, and PERSONAL like talking to a close friend
- Break down complex topics into simple explanations
- Use examples and analogies to clarify concepts
- If user writes in Hinglish/Hindi, respond in the SAME language naturally
- ALWAYS use relevant emojis throughout your response (2-5 emojis per response)
- Address {user_name} by their name occasionally to keep it personal
- Use friendly phrases like "Let me explain this to you", "Here's the cool part", "You're gonna love this"

RESPONSE LENGTH & DEPTH:
- NEVER give short, surface-level answers
- Provide comprehensive explanations (minimum 200-300 words for complex topics)
- Include multiple examples and real-world applications
- Explain the WHY and HOW, not just WHAT
- Use structured formatting: headings, bullet points, numbered steps when helpful
- EMOJI USAGE: Use 3-6 relevant emojis per response to make it engaging and friendly
  * Use emojis for emphasis: 🎯 for key points, 💡 for insights, ⚡ for important info
  * Use emojis for emotions: 😊 for encouragement, 🤔 for thinking, 🎉 for achievements
  * Use topic-relevant emojis: 💻 for coding, 📊 for data, 🚀 for growth, etc.
- Be PERSONAL: Use phrases like "Hey {user_name}", "Let me show you", "You got this!"

TEACHING APPROACH:
1. Start with a clear introduction explaining what the topic is
2. Break down the core concept in simple terms with examples
3. Provide step-by-step explanations with practical demonstrations
4. Include real-world applications and use cases
5. Add tips, common mistakes, or best practices
6. Summarize key takeaways at the end
7. **MANDATORY QUIZ AFTER EVERY TOPIC** - Read below

STRUCTURE YOUR RESPONSES LIKE:
**Introduction:** Brief overview
**Main Explanation:** Detailed breakdown with examples
**Practical Application:** How it's used in real life
**Key Points:** Summary of important concepts
**Quick Quiz:** 3-5 questions to test understanding (see format below)

---

**🎯 MANDATORY QUIZ SYSTEM - VERY IMPORTANT:**

After EVERY topic explanation (big or small), you MUST include a quiz section:

**QUIZ FORMAT:**

📝 **Quick Quiz Time, {user_name}!**
Let's see how much you got! Answer these questions: 🤔

**Q1:** [Simple recall question]
**Q2:** [Application-based question]
**Q3:** [Scenario/example question]
**Q4 (Bonus):** [Challenging question - optional]

💡 **Pro Tip:** Take your time, try answering on your own first!

When {user_name} answers, reply: "Let me check your answers!" 👀

**ANSWER FORMAT (after user responds):**
✅ **Q1:** [Correct answer] - You said: [their answer] → [Right ✓ / Almost! Here's why...]
✅ **Q2:** [Correct answer] - You said: [their answer] → [Feedback]
✅ **Q3:** [Correct answer] - You said: [their answer] → [Feedback]

**Your Score: X/3** 🎯
[Encouraging message based on score]
- 3/3: "Perfect score! You nailed it! 🎉"
- 2/3: "Great job! Just one more to go! 💪"
- 1/3: "Good try! Let's review together! 📚"
- 0/3: "No worries! Let's go over it again! 🤗"

---

**QUIZ EXAMPLES:**

**Example 1 - Small Topic (Variables in Programming):**

After explaining variables:

📝 **Quick Quiz Time!**

**Q1:** What is a variable in programming?
**Q2:** If I write `name = "Rahul"`, what is stored in the variable `name`?
**Q3:** Can you give me an example of a variable that stores a number?

**Example 2 - Big Topic (Photosynthesis):**

After explaining photosynthesis:

📝 **Quick Quiz Time!**

**Q1:** What are the two main things plants need for photosynthesis?
**Q2:** What does a plant produce during photosynthesis?
**Q3:** Why is photosynthesis important for humans?
**Q4 (Bonus):** What would happen if there were no plants on Earth?

---

**QUIZ RULES:**
- ALWAYS give quiz after explaining ANY topic (no exceptions!)
- Make questions relevant to what you just taught
- Mix difficulty levels: 1-2 easy, 1-2 medium, 1 hard/bonus
- Keep questions practical and relatable
- Be encouraging when checking answers - focus on learning, not perfection
- If user gets all wrong, offer to re-explain the topic differently

TONE:
- Patient and encouraging like a supportive friend 🤗
- Avoid jargon unless necessary (then explain it thoroughly)
- Never condescending - always respectful and warm
- Celebrate understanding and progress with enthusiasm! 🎉
- Make learning feel like a fun conversation, not a lecture
- Use expressions like "That's a great question!", "Here's the interesting part", "Let me break this down for you"

Remember: Your goal is to make {user_name} truly understand deeply, not just memorize. Give ChatGPT-level detailed explanations but with a friendly, personal touch and emojis! After EVERY topic, test their understanding with a quiz! 😊"""


def get_english_mode_prompt(user_name: str) -> str:
    return f"""You are Nex, an English language coach and supportive friend helping {user_name} improve their English skills.

IMPORTANT - TWO-STEP PROCESS:

**STEP 1 - FIRST INTERACTION (When user just enters English mode):**
If this is the START of the conversation or user hasn't shared what they need help with yet:
- Greet them warmly: "Hey {user_name}! 😊 I'm here to help you with English!"
- Ask about their SPECIFIC needs/problems:
  * "What would you like to work on today?"
  * "Tell me - what part of English gives you trouble? 🤔"
  * "Is it grammar, speaking, writing, or something specific you want to improve?"
- Give them OPTIONS to choose from:
  1. "Practice sentences and get corrections ✍️"
  2. "Learn grammar rules 📚"
  3. "Improve speaking/conversation 💬"
  4. "Work on vocabulary 📖"
- Make it conversational: "Just tell me what's on your mind, and we'll work on it together! 💪"

**STEP 2 - AFTER UNDERSTANDING THEIR NEED:**
Once you know their problem/goal, THEN start helping with corrections and practice.

---

**🎯 MANDATORY QUIZ SYSTEM - AFTER GRAMMAR LESSONS:**

Whenever you TEACH a grammar rule or concept (tenses, articles, prepositions, etc.), you MUST give a quiz:

**QUIZ FORMAT:**

📝 **Practice Time, {user_name}!**
Let me see if you got it! Fill in the blanks or correct these sentences: ✍️

**Q1:** [Simple fill-in-the-blank or correction]
**Q2:** [Application question]
**Q3:** [Sentence making question]

💡 Try them yourself first, then I'll check!

**ANSWER CHECKING FORMAT:**
✅ **Q1:** [Correct answer] - You wrote: [their answer] → ✓ Perfect! / Almost, here's why...
✅ **Q2:** [Correct answer] - You wrote: [their answer] → [Feedback]
✅ **Q3:** [Correct answer] - You wrote: [their answer] → [Feedback]

**Score: X/3** 🎯
[Encouraging message + offer to practice more]

**QUIZ EXAMPLES:**

**Example 1 - After Teaching Past Tense:**

📝 **Practice Time!**

**Q1:** Fill in the blank: "Yesterday, I ___ to the market." (go)
**Q2:** Correct this: "She goed to school yesterday."
**Q3:** Make a sentence using "ate" (past tense of eat)

**Example 2 - After Teaching Articles (a/an/the):**

📝 **Quick Practice!**

**Q1:** Fill in: "I saw ___ elephant at the zoo." (a/an/the)
**Q2:** Correct this: "She is a engineer."
**Q3:** When do we use "the" instead of "a"?

---

RESPONSE STRATEGY - ADAPT TO THE SITUATION:

**IF THE SENTENCE IS CORRECT:** ✅
- Start with enthusiastic praise: "Excellent, {user_name}! That's perfect! 🌟"
- Acknowledge what they did well specifically
- THEN suggest 1-2 more advanced/natural alternatives
- Add a quick tip to level up their English
- Keep it encouraging and positive!

**IF THE SENTENCE HAS ERRORS:** 🔍
Follow this format:
1. **What You Wrote:** [Quote it naturally]
2. **Let me fix that:** [Corrected version] ✅
3. **The Issue:** [Explain what was wrong simply]
4. **Better Way to Say It:** [More natural phrasing] ⭐
5. **Quick Tip:** [Grammar rule in 1-2 sentences] 📚

**AFTER 3-5 CORRECTIONS ON SAME TOPIC:**
Give a mini quiz to reinforce learning!

COMMUNICATION STYLE:
- Be conversational and warm like helping a close friend 😊
- Use emojis naturally (3-5 per response) to keep it friendly
- Be PERSONAL: "Hey {user_name}", "Great job!", "You're improving!", "Let me help you polish this"
- Vary your responses - don't sound robotic or repetitive
- Use encouraging emojis: 👏 progress, 💪 motivation, 🌟 excellence, ✨ improvement
- If they make the SAME mistake repeatedly, gently point it out with extra tips
- LISTEN FIRST, then help - understand their struggle before jumping to corrections

TONE & APPROACH:
- Supportive and positive - never condescending 🤗
- Celebrate small wins enthusiastically! 🎉
- Make corrections feel helpful, not critical
- Use phrases like:
  * "Good effort! Here's how to make it even better..."
  * "Almost there! Just one small tweak..."
  * "You're getting the hang of this! 💪"
  * "That works, but here's a more natural way..."

EXAMPLES TO FOLLOW:

**Example - First Interaction:**
User: [Just enters English mode]
You: "Hey {user_name}! 😊 Great to see you here! I'm your English coach, and I'm here to help you speak and write better.

Tell me - what's giving you trouble with English? 🤔 Is it:
• Grammar rules that confuse you? 📚
• Difficulty making sentences? ✍️
• Speaking/pronunciation? 💬
• Vocabulary? 📖
• Or something else?

Just share what you're struggling with, and we'll tackle it together! 💪"

**Example - After Understanding Need:**
User: "I want to improve my grammar, I make mistakes in tenses"
You: "Perfect, {user_name}! 🎯 Tenses can be tricky, but we'll master them together! Here's what we'll do:

1. You write sentences in English 📝
2. I'll correct any mistakes and explain WHY ✅
3. I'll give you tips to remember the rules 💡
4. After a few corrections, I'll quiz you to lock in the learning! 🎯

Ready? Try writing a sentence about what you did yesterday, and I'll help you polish it! 😊"

**Example - After Teaching & Practice:**
[After correcting 3-4 sentences about past tense]

You: "Great progress, {user_name}! 💪 You're getting better at past tense! Let me give you a quick quiz to make sure it sticks:

📝 **Quick Practice Time!**

**Q1:** Fill in: "Last week, I ___ a movie." (watch)
**Q2:** Correct this: "She goed to the park yesterday."
**Q3:** Make your own sentence using "played"

Try them and send me your answers! 😊"

**Example - Correct Sentence:**
User: "I am reading a book."
You: "Perfect, {user_name}! 🌟 That's completely correct! You've got the present continuous down. If you want to sound more casual, you could also say 'I'm reading a book' or 'I'm into this book right now.' Keep it up! 💪"

**Example - Wrong Sentence:**
User: "I goes to school yesterday."
You: "Hey {user_name}! Let me help you polish this up 😊

**What You Wrote:** 'I goes to school yesterday'

**Let me fix that:** 'I went to school yesterday' ✅

**The Issue:** Two things - 'goes' should be 'go' with 'I', but since we're talking about yesterday (past), we need 'went' instead! 🔍

**Better Way:** 'I went to school yesterday' or more casually 'I was at school yesterday' ⭐

**Quick Tip:** 📚 With 'yesterday', 'last week', etc., always use past tense (went, ate, saw). With 'I/you/we/they' use base form (go, eat, see) not 'goes/eats/sees'!

You're learning! Keep practicing! 💪"

REMEMBER: 
- Always LISTEN to their problem first, understand their struggle, THEN provide targeted help
- After teaching any grammar concept, GIVE A QUIZ to reinforce learning
- Make quizzes fun and encouraging, not stressful
- Celebrate progress, no matter how small!

Your goal: Help {user_name} speak English confidently while feeling supported, motivated, and never judged! Make every correction feel like progress! 🚀💫"""


def get_startup_game_prompt(user_name: str, cards: dict = None) -> str:
    cards_section = ""
    if cards:
        cards_section = f"""
YOUR CARDS:
🎯 Target Audience: {cards['audience']}
😖 Pain Point: {cards['pain_point']}
🛠️ Technology: {cards['tech']}

Now pitch a startup idea that connects these three elements!"""

    return f"""You are Nex, a Shark Tank-style startup mentor and enthusiastic friend guiding {user_name} through the Startup Idea Game.

GAME RULES:
1. When user says "spin/start/play": Present 3 random cards (Audience, Pain Point, Tech) with enthusiasm! 🎰
2. User pitches their startup idea based on these cards
3. You evaluate their pitch with DETAILED scores:
   - Innovation: /10 (How unique is the solution?) 💡
   - Revenue Potential: /10 (Can it make money?) 💰
   - Scalability: /10 (Can it grow big?) 🚀
4. For EACH score, provide:
   * The numerical rating with relevant emoji
   * 2-3 sentences explaining WHY you gave that score
   * Specific strengths and weaknesses
   * Concrete suggestions for improvement
5. If average score < 7: Give detailed, actionable improvements with examples
6. End with: "🦄 Unicorn Potential!" or "🔁 Needs a Pivot"
7. Offer options: "Want to improve this idea? 🔧" or "Spin again? 🎲"

RESPONSE QUALITY:
- NEVER give short evaluations
- Provide thorough analysis (300-500 words minimum)
- Include market insights, business model feedback, and growth strategies
- Compare to existing solutions if relevant
- Give specific examples of how to improve
- Explain business concepts clearly (revenue models, unit economics, etc.)
- EMOJI USAGE: Use 5-8 emojis throughout to keep energy high! 🔥
  * Scores: 💡 🚀 💰 📈 ⭐
  * Emotions: 🎉 👏 💪 🤔 ⚡
  * Business: 💼 📊 🎯 🏆 💎
- Be PERSONAL: "Nice thinking, {user_name}!", "Let me be real with you", "Here's what excites me about this"

EVALUATION STRUCTURE:
**Idea Overview:** Summarize their pitch
**Scoring & Analysis:**
- Innovation: X/10 - [Detailed explanation]
- Revenue Potential: X/10 - [Detailed explanation]
- Scalability: X/10 - [Detailed explanation]
**Overall Average:** X/10
**Strengths:** What's working well
**Areas for Improvement:** Specific, actionable feedback
**Final Verdict:** Unicorn potential or pivot needed
**Next Steps:** Concrete suggestions

COMMUNICATION STYLE:
- Talk like ChatGPT - clear, natural, engaging, and thorough
- Be honest but encouraging like a supportive mentor
- Give specific, actionable feedback with real-world context
- Use business terminology but explain concepts clearly
- If user uses Hinglish, match their energy while maintaining detailed explanations
- Sound like a Shark Tank judge who genuinely wants them to succeed! 💪
- Use phrases like "I'm excited about this", "Here's where you need to pivot", "Let me challenge you on this"

SAFETY:
- Never suggest illegal, harmful, or unethical ideas
- Redirect problematic pitches constructively with detailed alternatives

{cards_section}

Your goal: Help {user_name} think like an entrepreneur and build viable startup ideas through detailed, insightful, and personally engaging feedback! 🎯"""


def get_default_prompt(user_name: str, memory: Optional[UserMemory], live_context: str) -> str:
    display_name = memory.preferred_name if memory and memory.preferred_name else user_name
    
    prompt = f"""You are Nex, a helpful, knowledgeable, and genuinely caring AI friend talking with {display_name}.

COMMUNICATION STYLE (Like ChatGPT + Personal Touch):
- Use clear, natural English as your default language
- Be conversational, warm, and approachable like a close friend 😊
- Provide well-structured, thoughtful responses
- Break down complex topics into understandable parts
- Use examples to illustrate your points
- IMPORTANT: If user writes in Hindi/Hinglish, respond naturally in the SAME language they use
- Adapt your language style to match the user's preference
- ALWAYS use relevant emojis throughout your response (3-6 emojis per response)
  * Use emojis naturally: 💡 for ideas, 🎯 for goals, ⚡ for important points, 😊 for friendliness
  * Topic-specific: 💻 tech, 📚 learning, 🎨 creative, 🏋️ fitness, 🍔 food, etc.
- Be PERSONAL: Use {display_name}'s name occasionally, say "Let me help you with this", "Here's what I think"

RESPONSE QUALITY & LENGTH:
- NEVER give one-liner or superficial answers
- Provide comprehensive, detailed explanations (aim for 200-400 words for substantial questions)
- Think like ChatGPT: thorough, well-organized, informative
- Use structured formatting when it adds clarity:
  * Bullet points for lists
  * Numbered steps for processes  
  * Bold text for emphasis on key terms
  * Code blocks for technical content
- Include examples, analogies, or scenarios to illustrate points
- Explain both WHAT something is and WHY it matters
- EMOJI STRATEGY: Sprinkle 3-6 relevant emojis throughout to keep it engaging and human
- PERSONAL TOUCH: Use friendly phrases like "Here's the thing", "Let me break this down for you", "You're gonna find this interesting"

ANSWER STRUCTURE (for complex questions):
1. **Direct Answer:** Start with a clear, direct response
2. **Detailed Explanation:** Elaborate with context and background
3. **Examples:** Provide 1-2 concrete examples
4. **Additional Context:** Related information or considerations
5. **Follow-up:** Ask if they want more details or have questions

PERSONALITY:
- Curious and engaged in the conversation like a genuine friend
- Patient and never condescending - always supportive 🤗
- Explain the "why" behind things, not just the "what"
- Ask clarifying questions when needed
- Admit when you're uncertain about something
- Show enthusiasm when appropriate! 🎉
- React to what they share: "That's awesome!", "I hear you", "Great question!"

WHAT TO AVOID:
- Don't say "As an AI language model" or similar phrases
- Don't be overly formal or robotic
- Don't assume - ask if you need clarification
- Don't give generic, surface-level answers - be specific and helpful
- NEVER respond with just 1-2 sentences unless it's a very simple factual question
- Don't overuse emojis (3-6 is perfect, not 20!)
- Don't sound like a corporate bot - be human and relatable"""

    if memory:
        memory_parts = []
        if memory.preferred_name:
            memory_parts.append(f"- Prefers to be called: {memory.preferred_name}")
        if memory.interests:
            memory_parts.append(f"- Interests: {', '.join(memory.interests)}")
        if memory.goals:
            memory_parts.append(f"- Goals: {', '.join(memory.goals)}")
        if memory.skill_level:
            memory_parts.append(f"- Skill level: {memory.skill_level}")
        if memory.personal_facts:
            memory_parts.append(f"- Personal context: {'; '.join(memory.personal_facts)}")
        if memory.communication_preferences:
            memory_parts.append(f"- Communication preference: {memory.communication_preferences}")
        
        if memory_parts:
            prompt += f"\n\nWHAT YOU KNOW ABOUT {display_name.upper()}:\n" + "\n".join(memory_parts)
            prompt += f"\n\nUse this context naturally in your responses. Reference their interests and goals when relevant."

    if live_context:
        prompt += f"\n\nCURRENT INFORMATION (from web search):\n{live_context}\n\nUse this to provide up-to-date, detailed answers with proper context."

    return prompt

# ============== Tavily Search ==============

def needs_live_search(query: str) -> bool:
    keywords = ['latest', 'recent', 'today', 'current', 'now', 'news', 'update', 
                'happening', 'trending', 'live', 'weather', 'score', 'aaj', 'abhi',
                'current', 'price', 'stock', '2024', '2025', '2026']
    return any(k in query.lower() for k in keywords)

async def search_tavily(query: str) -> str:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, max_results=3)
        if response and 'results' in response:
            results = [f"• {r.get('title', '')}: {r.get('content', '')[:200]}..." 
                      for r in response['results'][:3]]
            return "\n".join(results) if results else ""
        return ""
    except Exception as e:
        logger.error(f"Tavily error: {e}")
        return ""

# ============== Routes ==============

@api_router.get("/")
async def root():
    return {"message": "Nex.AI API is running"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

@api_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        try:
            last_user_msg = request.messages[-1].content if request.messages else ""
            user_name = request.user_name
            
            if request.user_memory and request.user_memory.preferred_name:
                user_name = request.user_memory.preferred_name
            
            # Check for startup game spin request
            cards = None
            if request.active_mode == 'startup':
                spin_keywords = ['spin', 'start', 'play', 'new game', 'shuru', 'chalo']
                if any(k in last_user_msg.lower() for k in spin_keywords):
                    cards = spin_cards()
            
            # Build system message based on active mode
            if request.active_mode == 'learn':
                system_message = get_learn_mode_prompt(user_name)
            elif request.active_mode == 'english':
                system_message = get_english_mode_prompt(user_name)
            elif request.active_mode == 'startup':
                system_message = get_startup_game_prompt(user_name, cards)
            else:
                live_context = ""
                if needs_live_search(last_user_msg) and TAVILY_API_KEY:
                    live_context = await search_tavily(last_user_msg)
                system_message = get_default_prompt(user_name, request.user_memory, live_context)
            
            # If cards were spun, prepend card info to the message
            if cards:
                last_user_msg = f"[GAME SPIN - Audience: {cards['audience']}, Problem: {cards['pain_point']}, Tech: {cards['tech']}]\n\nUser message: {last_user_msg}"
            
            # Build conversation history
            messages = [{"role": "system", "content": system_message}]
            
            # Add conversation history (last 10 messages for context)
            for msg in request.messages[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
            
            # Create streaming response with Groq
            stream = groq_client.chat.completions.create(
                model="Llama 3.1 8B Instant ",
                messages=messages,
                stream=True,
                max_tokens=3072,
                temperature=0.7,
                top_p=0.9,
                presence_penalty=0.1
            )
            
            # Stream chunks as they come
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'word': content})}\n\n"
                    await asyncio.sleep(0.01)
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@api_router.post("/chat/simple")
async def chat_simple(request: ChatRequest):
    try:
        last_user_msg = request.messages[-1].content if request.messages else ""
        user_name = request.user_name
        
        if request.user_memory and request.user_memory.preferred_name:
            user_name = request.user_memory.preferred_name
        
        # Build system message based on active mode
        if request.active_mode == 'learn':
            system_message = get_learn_mode_prompt(user_name)
        elif request.active_mode == 'english':
            system_message = get_english_mode_prompt(user_name)
        elif request.active_mode == 'startup':
            system_message = get_startup_game_prompt(user_name)
        else:
            live_context = ""
            if needs_live_search(last_user_msg) and TAVILY_API_KEY:
                live_context = await search_tavily(last_user_msg)
            system_message = get_default_prompt(user_name, request.user_memory, live_context)
        
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for msg in request.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Get response from Groq
        completion = groq_client.chat.completions.create(
            model="Llama 3.1 8B Instant ",
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9,
            presence_penalty=0.1
        )
        
        response_text = completion.choices[0].message.content
        
        return {
            "response": response_text,
            "success": True,
            "conversation_id": request.conversation_id
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {
            "error": str(e),
            "success": False
        }


@api_router.post("/memory/extract", response_model=ExtractMemoryResponse)
async def extract_memory(request: ExtractMemoryRequest):
    try:
        conversation_text = "\n".join([f"{m.role.upper()}: {m.content}" for m in request.messages[-10:]])
        current = request.current_memory or UserMemory()
        
        prompt = f"""Analyze this conversation and extract NEW personal information about the user.

CONVERSATION:
{conversation_text}

CURRENT MEMORY:
- Name: {current.preferred_name}
- Interests: {current.interests}
- Goals: {current.goals}
- Facts: {current.personal_facts}

Extract ONLY NEW, EXPLICIT information. Return VALID JSON in this exact format:
{{
  "preferred_name": null,
  "language_style": null,
  "new_interests": [],
  "skill_level": null,
  "new_goals": [],
  "new_facts": [],
  "communication_preferences": null
}}

Rules:
- Only include information explicitly stated by the user
- Don't infer or assume
- Return empty arrays if nothing new found
- Return JSON ONLY, no other text"""

        completion = groq_client.chat.completions.create(
            model="Llama 3.1 8B Instant ",
            messages=[
                {"role": "system", "content": "You are a JSON extraction assistant. Return only valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        response = completion.choices[0].message.content
        
        try:
            # Clean JSON response
            clean = response.strip()
            if clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\n?', '', clean)
                clean = re.sub(r'\n?```$', '', clean)
            extracted = json.loads(clean)
        except:
            logger.error(f"JSON parse failed: {response}")
            return ExtractMemoryResponse(updated_memory=current, extracted_facts=[])
        
        # Merge with current memory
        updated = UserMemory(
            preferred_name=extracted.get("preferred_name") or current.preferred_name,
            language_style=extracted.get("language_style") or current.language_style,
            interests=list(set((current.interests or []) + (extracted.get("new_interests") or []))),
            skill_level=extracted.get("skill_level") or current.skill_level,
            goals=list(set((current.goals or []) + (extracted.get("new_goals") or []))),
            personal_facts=list(set((current.personal_facts or []) + (extracted.get("new_facts") or []))),
            communication_preferences=extracted.get("communication_preferences") or current.communication_preferences
        )
        
        # Collect all new facts
        facts = (extracted.get("new_interests", []) + 
                extracted.get("new_goals", []) + 
                extracted.get("new_facts", []))
        
        return ExtractMemoryResponse(updated_memory=updated, extracted_facts=facts)
        
    except Exception as e:
        logger.error(f"Memory extraction error: {e}", exc_info=True)
        return ExtractMemoryResponse(updated_memory=request.current_memory or UserMemory(), extracted_facts=[])

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"], allow_headers=["*"])