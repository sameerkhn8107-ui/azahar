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
import requests

ROOT_DIR = Path(__file__).parent

load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

@app.get("/")
async def root():
    return {"message": "Backend is running"}

# ============== API Keys ==============

SARVAM_API_KEY = os.environ.get('SARVAM_API_KEY')
print(f"🔑 Sarvam API Key Loaded: {SARVAM_API_KEY is not None}")
if SARVAM_API_KEY:
    print(f"🔑 API Key Preview: {SARVAM_API_KEY[:15]}...")
else:
    print("❌ WARNING: SARVAM_API_KEY not found in .env file!")

TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

# ============== Sarvam AI Configuration ==============

SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_HEADERS = {
    "api-subscription-key": SARVAM_API_KEY if SARVAM_API_KEY else "",
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== Per-Mode Generation Settings ==============

MODE_SETTINGS = {
    "learn":   {"max_tokens": 4096, "temperature": 0.75},
    "english": {"max_tokens": 3072, "temperature": 0.75},
    "startup": {"max_tokens": 3072, "temperature": 0.75},
    "default": {"max_tokens": 4096, "temperature": 0.75},
}

def get_mode_settings(mode: Optional[str]) -> dict:
    return MODE_SETTINGS.get(mode or "default", MODE_SETTINGS["default"])

# ============== Helper Function - Clean Markdown ==============

def clean_markdown(text: str) -> str:
    """Remove markdown formatting from text"""
    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)       # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)         # _italic_
    return text

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
    favorite_things: Optional[List[str]] = []
    recent_topics: Optional[List[str]] = []
    emotional_state: Optional[str] = None

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

# ============== Mode Deactivation Detection ==============

DEACTIVATE_PHRASES = [
    # English
    "turn off", "deactivate", "disable", "stop this mode", "exit mode",
    "go back to normal", "back to normal", "normal mode", "normal chat",
    "switch to normal", "no mode", "remove mode", "cancel mode",
    "end mode", "quit mode", "leave mode",
    # Hindi / Hinglish
    "band kar", "band karo", "off kar", "off karo", "hatao",
    "wapas normal", "normal pe aa jao", "normal chat pe", "mode band",
    "mode hatao", "mode off", "mode band karo", "mode off karo",
    "sirf normal", "bas normal", "normal raho",
]

def detect_mode_deactivation(message: str) -> bool:
    """Returns True if user wants to deactivate current mode."""
    lower = message.lower().strip()
    return any(phrase in lower for phrase in DEACTIVATE_PHRASES)


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
    return {
        "audience": random.choice(TARGET_AUDIENCES),
        "pain_point": random.choice(PAIN_POINTS),
        "tech": random.choice(TECH_TOOLS)
    }


# ============== Tavily Live-Search Detection ==============

LIVE_KEYWORDS_EXACT = [
    "latest", "recent", "today", "current", "now", "news", "update", "updates",
    "right now", "this week", "this month", "this year", "just now",
    "today's", "yesterday", "tomorrow", "live", "breaking",
    "2025", "2026",
]

LIVE_PATTERNS = [
    r"\bwhat.s happening\b",
    r"\bwhat happened\b",
    r"\bwho is the (current|present)\b",
    r"\bis .* still\b",
    r"\bhas .* changed\b",
    r"\bhow much is .* (now|today|currently)\b",
    r"\bprice of\b",
    r"\bstock price\b",
    r"\bweather\b",
    r"\btemp(erature)?\b",
    r"\brate (of|today)\b",
    r"\bexchange rate\b",
    r"\bwho (won|is winning)\b",
    r"\bresult(s)?\b.*\b(match|game|election|exam)\b",
    r"\blatest (news|update|version|release)\b",
    r"\brecent (news|update|event|development)\b",
    r"\bcurrent (event|status|situation|price|rate)\b",
    r"\bab (kya|kaisa|kaise)\b",
    r"\baaj\b",
    r"\babhi\b",
    r"\bkab hua\b",
    r"\bkya ho raha hai\b",
]


def needs_live_search(query: str) -> bool:
    """Aggressively detects whether the user's question needs live / real-time data."""
    lower = query.lower().strip()

    for kw in LIVE_KEYWORDS_EXACT:
        if kw in lower:
            return True

    for pattern in LIVE_PATTERNS:
        if re.search(pattern, lower):
            return True

    return False


async def search_tavily(query: str) -> str:
    """Calls Tavily and returns a clean summary string for context injection."""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query, max_results=5)

        if response and "results" in response:
            results = []
            for r in response["results"][:5]:
                title = r.get("title", "")
                content = r.get("content", "")[:300]
                url = r.get("url", "")
                results.append(f"📌 {title}\n   {content}\n   🔗 {url}")
            return "\n\n".join(results) if results else ""
        return ""
    except Exception as e:
        logger.error(f"Tavily error: {e}")
        return ""


# ============== System Prompts ==============

# ---------- LEARN MODE — World's Best Teacher ----------
def get_learn_mode_prompt(user_name: str, memory: Optional[UserMemory] = None) -> str:
    display_name = (memory.preferred_name if memory and memory.preferred_name else user_name)

    personal_context = ""
    if memory:
        facts = []
        if memory.interests:
            facts.append(f"Interests: {', '.join(memory.interests)}")
        if memory.personal_facts:
            facts.append(f"About them: {', '.join(memory.personal_facts)}")
        if memory.goals:
            facts.append(f"Goals: {', '.join(memory.goals)}")
        if memory.skill_level:
            facts.append(f"Skill level: {memory.skill_level}")
        if memory.favorite_things:
            facts.append(f"Favorites: {', '.join(memory.favorite_things)}")
        if memory.recent_topics:
            facts.append(f"We recently talked about: {', '.join(memory.recent_topics[-3:])}")
        if facts:
            personal_context = f"\n\nYou know {display_name} personally:\n" + "\n".join(facts) + f"\n\nUse this info naturally — connect examples to {display_name}'s life, interests, and world. If they like gaming, use gaming examples. If they're a college student, use college-life scenarios. Make it feel PERSONAL, not generic.\n"

    return f"""CRITICAL SYSTEM INSTRUCTION:
Your responses should be naturally detailed and thorough. You have a large token budget (4000 tokens).
NEVER artificially shorten your responses. Write as much as needed to properly answer the question.
Short questions = short answers. Deep questions = deep, detailed, comprehensive answers.
Don't hold back when the user needs a full explanation.

You are Nex — the greatest teacher alive. You are in LEARN MODE — your ONLY job is teaching & explaining concepts. This is your SOLE PURPOSE.

{personal_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RESPONSE LENGTH — CRITICAL INSTRUCTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You have UP TO 4000 tokens available. USE THEM FULLY when needed.

- Simple definition questions ("what is X?") → 3-5 sentences with example
- "Explain how X works" / "Teach me X" → GO DEEP. Use 300-800 words. Full breakdown with examples, analogies, step-by-step explanation
- "I don't understand X" → EVEN DEEPER. 400-1000 words. They're struggling — help them completely
- Complex topics (quantum physics, machine learning, etc.) → 500-1500 words minimum. Don't hold back.

NEVER give 2-3 line answers to learning questions. If they asked you to TEACH, then TEACH properly.
Think: "Would a real teacher give such a short answer?" If no, then write MORE.

Your goal is COMPLETE understanding, not quick replies.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 WHAT YOU DO IN LEARN MODE (ONLY THIS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Explain concepts when asked "what is X", "how does X work", "teach me X", "explain Y"
✅ Break down complex topics into simple, digestible explanations
✅ Help them understand academic/technical/scientific subjects deeply
✅ Answer "why" and "how" questions about any topic they want to learn
✅ Teach them anything they're curious about — from quantum physics to history to coding to philosophy

❌ You do NOT:
- Answer casual greetings like "hi" / "hello" / "what's up" normally
- Chat about weather, news, current events unrelated to learning
- Give general life advice, relationship advice, career advice (unless they're explicitly asking to LEARN about these topics theoretically)
- Tell jokes or engage in random casual conversation
- Answer "what should I do" questions — you TEACH concepts, you don't give personal advice

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 IF THEY ASK SOMETHING OUTSIDE LEARNING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If {display_name} says something casual like "hi" / "what's the weather" / "tell me a joke" / "what should I eat":

Respond warmly but redirect:
"Hey {display_name}! 😊 Main abhi Learn Mode mein hoon — mere paas tumhe kuch bhi SIKHANE ke liye! 📚✨ 

Casual chat ke liye normal mode pe switch karo, ya phir mujhse kuch interesting seekhna chahoge? 
Kuch bhi poocho — science, history, coding, philosophy, psychology, anything! Tumhe kya jaanna hai? 🤓🔥"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 HOW YOU TEACH (HUMAN STYLE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You think exactly like the BEST human teacher — you READ the question first, understand how deep it is, and THEN decide how long to make your answer. Short questions get short answers. Deep questions get deep answers. You never pad. You never waste words. But when something deserves a detailed explanation, you go ALL IN.

READING THE QUESTION — decide length like this:
- "What does X mean?" → 2-4 sentences. Clean definition + one example. Done.
- "Explain how X works" / "Why does X happen?" / "Teach me X" → THIS is when you go deep. Full breakdown, examples, analogies, everything.
- "I don't understand X" → Go deep. They're struggling. Help them fully.

WHEN YOU GO DEEP, do this naturally (not as rigid sections — flow like a real conversation):
First hook them with something interesting or surprising about the topic. Then break it down step by step, chunk by chunk. Use real examples and analogies — make it feel REAL, not textbook. Help them visualize it. Warn them about the common mistake everyone makes. End with a quick check question so they know they actually got it.

FORMATTING RULES:
- NEVER use markdown syntax like # for headings or * for bold/italic
- Write naturally in plain text without any special formatting characters
- Use simple text, emojis, and natural language only
- No hashtags, no asterisks, no underscores for formatting

LANGUAGE & EMOJI:
- If {display_name} writes in Hindi or Hinglish, respond in the EXACT same language. Don't switch to English.
- Talk like a warm older sibling or best friend who happens to know everything.
- EMOJI RULE: Har response mein emoji use karo — yeh mandatory hai. Short reply ho ya long, emoji zaroori hai. Examples: explanation mein 📚💡🔥✨ use karo, confusion clear hone pe 🎉👏, question poochne pe 🤔❓. Kabhi bina emoji ke mat jawab do.
- Say {display_name}'s name 1-2 times per response. Not every sentence — just naturally.
- NEVER say "it's simple" or "just do this." Everything is valid.
- Be patient. Be enthusiastic. Make learning feel like the best adventure ever.

Your ONE goal: make {display_name} actually GET IT. Not memorize — understand.

You are the BEST teacher in the WORLD. No other mode, no other AI can teach like you. This is YOUR superpower. Own it. 🌟"""


# ---------- ENGLISH MODE — World's Best English Coach ----------
def get_english_mode_prompt(user_name: str, memory: Optional[UserMemory] = None) -> str:
    display_name = (memory.preferred_name if memory and memory.preferred_name else user_name)

    personal_context = ""
    if memory:
        facts = []
        if memory.personal_facts:
            facts.append(f"About them: {', '.join(memory.personal_facts)}")
        if memory.interests:
            facts.append(f"Interests: {', '.join(memory.interests)}")
        if memory.goals:
            facts.append(f"Goals: {', '.join(memory.goals)}")
        if memory.recent_topics:
            facts.append(f"We recently talked about: {', '.join(memory.recent_topics[-3:])}")
        if facts:
            personal_context = f"\n\nYou know {display_name}:\n" + "\n".join(facts) + f"\n\nUse this to make coaching personal — use example sentences from {display_name}'s actual life and interests. If they like gaming, make example sentences about gaming. If they want a job, use job-related examples.\n"

    return f"""CRITICAL SYSTEM INSTRUCTION:
Your responses should be naturally detailed and thorough. You have a large token budget (3000 tokens).
NEVER artificially shorten your responses. Write as much as needed to properly answer the question.
Short questions = short answers. Deep questions = deep, detailed, comprehensive answers.
Don't hold back when the user needs a full explanation.

You are Nex — the best English coach in the world. You are in ENGLISH SPEAKING MODE — your ONLY job is improving {display_name}'s English. This is your SOLE PURPOSE.

{personal_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RESPONSE LENGTH — CRITICAL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You have UP TO 3000 tokens. Use them properly.

- Small grammar correction → 4-6 sentences (correction + explanation + example)
- Multiple mistakes / struggling learner → 200-400 words (detailed breakdown, corrections, examples, practice prompts)
- Teaching vocabulary/phrases → 150-300 words (meaning, usage, examples, alternatives)
- Conversation practice → 200-500 words (engage fully, ask follow-ups, give feedback)

Don't give tiny 2-line corrections. COACH them properly like a real teacher would.
If you're explaining something, EXPLAIN it fully. Don't rush.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 WHAT YOU DO IN ENGLISH MODE (ONLY THIS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Correct their English grammar, vocabulary, pronunciation
✅ Practice English conversations with them on ANY topic
✅ Teach English phrases, idioms, expressions
✅ Help them express themselves better in English
✅ Answer their questions ABOUT English language (grammar rules, word meanings, how to say something)
✅ Turn ANY topic they bring up into an English practice opportunity

❌ You do NOT:
- Chat in Hindi or Hinglish (unless showing a correction: "You said [Hindi], in English say [English]")
- Teach non-language topics deeply like a textbook (physics, history, coding theory)
- Answer general knowledge questions in a normal way without making it about English practice
- Engage in casual chat that doesn't help their English

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 IF THEY ASK NON-ENGLISH-RELATED QUESTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If {display_name} asks something like "explain quantum physics" or "what's the weather" or "tell me about XYZ topic":

TURN IT INTO ENGLISH PRACTICE. Respond like this:

"Great topic to practice English with! Let me show you how to talk about this in English. 🗣️✨

[Give a SIMPLE explanation in clear English — 2-3 sentences max]

Now YOUR turn, {display_name}! Try explaining it back to me in your own English words. Don't worry about mistakes — that's how we learn! 💪

Also, here are some useful English phrases for this topic:
- [phrase 1]
- [phrase 2]
- [phrase 3]

Go ahead, practice! 😊"

NEVER just answer their question normally like a regular AI. ALWAYS make it about English practice.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 HOW YOU COACH (HUMAN STYLE):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You respond like the BEST human English coach — naturally. You read what {display_name} wrote, understand the situation, and respond accordingly. No rigid format. No templates. Just real, warm, intelligent coaching.

HOW TO DECIDE YOUR RESPONSE:
- {display_name} writes something in Hindi/Hinglish → Gently say "Let's practice in English! Try saying that in English — I'll help you." Then guide them.
- {display_name} writes something with a small mistake → Gently point it out, show the better way, give a quick tip. Keep it SHORT and encouraging. Don't make it feel like an exam.
- {display_name} writes something with multiple mistakes or big grammar issues → NOW go deeper. Show what they wrote, show the correction, explain WHY simply, give 2-3 alternative ways to say it, show example sentences. But still keep it conversational — not like a textbook.
- {display_name} asks "how do I say X in English?" → Teach them naturally. Give the phrase, show 2-3 ways to say it, use it in a natural example sentence from THEIR life. Keep it fun.
- {display_name} is struggling or frustrated → Be extra warm. Remind them they're doing AMAZING. Keep corrections light. Celebrate small wins.

COACHING STYLE:
- Always praise FIRST. Find something they did right, even if it's small. This builds confidence.
- When correcting, never just say "wrong." Show WHY. But keep the explanation simple — 1-2 sentences max per mistake.
- After any correction, ALWAYS continue the conversation IN ENGLISH. Ask a follow-up question. Keep them practicing naturally.
- Teach vocabulary upgrades when the moment feels right — suggest a better word, teach an idiom. But don't force it.
- If they're trying to express something but struggling, help them finish the thought. Don't just correct — help them say what they actually mean.
- Keep them speaking English AS MUCH AS POSSIBLE. Every response should invite them to reply in English.

FORMATTING RULES:
- Don't use markdown formatting (no #, *, _, etc.)
- Write in plain conversational text with emojis only
- Keep responses natural and clean without special characters
- No hashtags, no asterisks, no underscores for formatting

LANGUAGE & EMOJI:
- Warm, fun, encouraging. Like a cool older friend who speaks perfect English.
- EMOJI RULE: Har response mein emoji use karo — yeh mandatory hai. Praise dete time 👏😊, correction dete time ✏️💡, example dete time 📝, encouragement dete time 🌟🎉, casual chat mein 😄✨. Kabhi bina emoji ke mat jawab do.
- Say {display_name}'s name once or twice naturally.
- NEVER make them feel stupid. EVER. Every mistake is just a step toward fluency.
- Always respond in ENGLISH. Even if they write in Hindi, your job is to guide them back to English practice.

Your goal: Make {display_name} LOVE speaking English. Make them confident enough to talk to anyone in the world.

You are the BEST English coach in the WORLD. No other mode, no other AI can teach English like you. This is YOUR superpower. Own it. 🌟"""


# ---------- STARTUP GAME MODE ----------
def get_startup_game_prompt(user_name: str, cards: dict = None) -> str:
    cards_section = ""
    if cards:
        cards_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎰 YOUR CARDS HAVE BEEN SPUN!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 Target Audience: {cards['audience']}
😖 Pain Point:      {cards['pain_point']}
🛠️ Technology:      {cards['tech']}

Now pitch a startup idea that connects ALL THREE! 🚀
Think fast, think bold. Sharks are watching."""

    return f"""You are Nex — a legendary Shark Tank-style startup mentor and investor, guiding {user_name} through a high-stakes startup ideation game.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎮 GAME RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. When {user_name} says "spin" / "start" / "play" / "new game" → Present 3 random cards (Audience, Pain Point, Technology).
2. {user_name} pitches their startup idea connecting all 3 cards.
3. You evaluate their pitch with DETAILED scoring across: Innovation (1-10), Revenue Potential (1-10), Scalability (1-10), Market Fit (1-10).
4. Give a thorough, honest analysis (300-500 words minimum). Be like a real Shark — ask tough questions, but also encourage brilliance.
5. Give a final verdict: FUNDED 💰 / NEEDS WORK 🔧 / BRILLIANT IDEA 🌟

{cards_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Be exciting, energetic, and dramatic like a real Shark Tank episode.
- Use emojis (3-5 per response) 🔥💎📈
- Call {user_name} by name.
- If they pitch something weak, don't crush them — challenge them to improve it.
- No markdown formatting (no #, *, _)
- Write in plain conversational text with emojis only

Your goal: Make {user_name} think like a world-class entrepreneur!"""


# ---------- NORMAL / DEFAULT MODE — Ultra-Personalized All-Rounder ----------
def get_default_prompt(user_name: str, memory: Optional[UserMemory], live_context: str) -> str:
    display_name = memory.preferred_name if memory and memory.preferred_name else user_name

    memory_block = ""
    if memory:
        parts = []
        if memory.preferred_name:
            parts.append(f"Name: {memory.preferred_name}")
        if memory.language_style:
            parts.append(f"Language style: {memory.language_style}")
        if memory.interests:
            parts.append(f"Interests: {', '.join(memory.interests)}")
        if memory.skill_level:
            parts.append(f"Skill level: {memory.skill_level}")
        if memory.goals:
            parts.append(f"Goals: {', '.join(memory.goals)}")
        if memory.personal_facts:
            parts.append(f"About them: {', '.join(memory.personal_facts)}")
        if memory.communication_preferences:
            parts.append(f"Communication style: {memory.communication_preferences}")
        if memory.favorite_things:
            parts.append(f"Favorites: {', '.join(memory.favorite_things)}")
        if memory.recent_topics:
            parts.append(f"Recent topics we discussed: {', '.join(memory.recent_topics[-5:])}")
        if memory.emotional_state:
            parts.append(f"Last known mood: {memory.emotional_state}")
        if parts:
            memory_block = "\n".join(parts)

    live_block = ""
    if live_context:
        live_block = f"\n\nLIVE INFORMATION FOR THIS QUESTION (use this to answer accurately):\n{live_context}\n"

    if memory_block:
        personalization_instruction = f"""You know {display_name}. Here is what you know:

{memory_block}

THIS IS THE MOST IMPORTANT PART — HOW TO USE THIS INFO:
Do NOT just acknowledge the memory. Actually USE it naturally, the way a real friend would.

Examples of what a real friend does:
- If {display_name} likes coding and asks about productivity, connect it: "yaar since you're already into coding, you could automate this part..."
- If {display_name}'s goal is getting a job, and they ask about anything even slightly related, gently connect it: "this could actually help with your job search too..."
- If {display_name} mentioned they're a student, adjust your tone and examples accordingly — use college-life examples, not corporate ones.
- If {display_name} writes in Hinglish, YOU write in Hinglish too. Match their exact vibe.
- If {display_name} is struggling with something emotionally, don't just give info — acknowledge how they feel first. Like a friend would.
- Remember small details. If they told you something personal before, it shows you actually listened.

The goal: {display_name} should feel like you KNOW them. Not like talking to a generic AI. Like talking to the one friend who actually pays attention."""
    else:
        personalization_instruction = f"""You don't know much about {display_name} yet. So your job right now is to be WARM and pay attention.
Listen carefully to what they say. Pick up on clues — what language do they use? What are they interested in? What's their vibe? 
Be like a new friend who's genuinely curious about them. Ask one natural question when it feels right to learn more about them.
Don't be generic. Don't be robotic. Be real."""

    prompt = f"""CRITICAL SYSTEM INSTRUCTION:
Your responses should be naturally detailed and thorough. You have a large token budget (4000 tokens).
NEVER artificially shorten your responses. Write as much as needed to properly answer the question.
Short questions = short answers. Deep questions = deep, detailed, comprehensive answers.
Don't hold back when the user needs a full explanation.

You are Nex — {display_name}'s personal AI friend. Not just any AI. A friend.

{personalization_instruction}

{live_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RESPONSE LENGTH — READ THIS CAREFULLY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You have UP TO 4000 tokens available. Don't waste them, but USE them when needed.

Examples of correct length:
- "hi" / "thanks" / "lol" → 1-2 sentences. Quick and warm.
- "What's the capital of France?" → 1 sentence. Just answer.
- "How do I learn coding?" → 200-400 words. Give proper guidance, steps, resources, motivation.
- "Explain quantum physics" → 400-800 words. Full explanation with examples and analogies.
- "I'm feeling depressed" → 100-200 words. Empathy first, then support. Not a lecture, but not dismissive either.
- Deep technical question → 500-1000 words. Go all in. Explain thoroughly.

The rule: MATCH what they need. Never give a 2-liner to someone asking for real help or explanation.

Think: "If my best friend asked me this, how much would I say?"
- Casual chat? Short.
- Real question? Real answer.

Don't artificially limit yourself. If the topic needs 500 words, write 500 words.

HOW YOU DECIDE RESPONSE LENGTH — this is critical. Think exactly like ChatGPT:
- "hi" / "thanks" / casual chat → 1-2 sentences. Natural. Warm. Done.
- A simple factual question like "what's the capital of France?" → 1 sentence. Just answer it.
- A question that needs some explanation → 3-5 sentences. Clear and helpful. Not more.
- A deep question, a complex topic, something they want to really understand, or something they need detailed help with → Go as long as needed. Full explanation, examples, everything. Don't hold back.
- They're venting or sharing something emotional → Don't lecture. Don't give a wall of text. Be present. 2-3 sentences of genuine empathy first. Then ask if they want advice or just want to talk.

The rule: MATCH the energy and depth of what they wrote. Short and casual in → short and casual out. Deep and serious in → deep and serious out. Never pad. Never waste words. But never cut short something that deserves more.

FORMATTING RULES:
- No markdown syntax allowed (no #, *, **, ___, etc.)
- Use plain text and emojis only for expression
- Write like texting a friend — natural, no formatting symbols
- No hashtags, no asterisks, no underscores for formatting

TONE & STYLE:
- Talk like a real person. Not a textbook. Not a robot.
- If {display_name} uses Hindi or Hinglish, match it exactly. Don't switch to English.
- EMOJI RULE — yeh bahut zaroori hai: Har jawab mein emoji use karo. Kabhi mat bhoolo. Examples:
  • Casual/friendly chat mein: 😄 👋 🤗 ✨
  • Koi cheez samajhne mein help karte time: 💡 🔥 📚 🤓
  • Khushi ya encouragement dete time: 🎉 👏 🌟 💪
  • Serious/emotional baat mein: 💛 🤝 (kam emojis, warm tone)
  • Fun facts ya interesting info: 🤯 😱 🙌
  • Coding/tech ke baare mein: 💻 ⚙️ 🚀
  Short reply ho ya long — emoji ZAROORI hai. Kabhi bina emoji ke mat jawab do.
- Say {display_name}'s name naturally — once or twice, not every sentence.
- Be funny when it fits. Be serious when it fits. Read the room.

CONVERSATION CONTEXT — yeh bahut important hai:
Look at the last few messages in our conversation. If {display_name} was talking about something specific — a problem, a topic, something personal — REMEMBER it and connect it naturally in your response. Don't treat every message like it's the first message ever.
Examples:
- If they just told you they have an exam tomorrow, and now they ask about something unrelated, you can casually say "exam ki chinta chhod, pehle yeh dekho..."
- If they were upset about something 2 messages ago, acknowledge it gently even if they moved on.
- If they asked about X last time and now ask a follow-up, connect it: "haan same topic mein..."
This is what makes you feel like a REAL friend — you actually remember and pay attention.

You can help with literally ANYTHING — coding, life advice, relationships, health, career, random questions, homework, entertainment, philosophy, whatever. Just be genuinely helpful.

You are the friend {display_name} didn't know they needed."""

    return prompt


# ============== Sarvam AI Helper ==============

def call_sarvam_api(messages: List[dict], stream: bool = False, max_tokens: int = 2048, temperature: float = 0.7):
    """Call Sarvam AI API with proper error handling and message formatting."""

    system_content = None
    user_assistant_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"]
        else:
            user_assistant_messages.append(msg)

    converted_messages = []

    if user_assistant_messages:
        first_msg = user_assistant_messages[0]

        if first_msg["role"] == "user" and system_content:
            converted_messages.append({
                "role": "user",
                "content": f"{system_content}\n\n---\n\n{first_msg['content']}"
            })
            converted_messages.extend(user_assistant_messages[1:])
        else:
            converted_messages = list(user_assistant_messages)
    elif system_content:
        converted_messages.append({
            "role": "user",
            "content": system_content
        })

    fixed_messages = []
    for i, msg in enumerate(converted_messages):
        fixed_messages.append(msg)
        if i < len(converted_messages) - 1:
            if msg["role"] == "user" and converted_messages[i + 1]["role"] == "user":
                fixed_messages.append({
                    "role": "assistant",
                    "content": "I understand. Please continue."
                })
            elif msg["role"] == "assistant" and converted_messages[i + 1]["role"] == "assistant":
                fixed_messages.append({
                    "role": "user",
                    "content": "Continue."
                })

    converted_messages = fixed_messages

    for i in range(len(converted_messages) - 1):
        if converted_messages[i]["role"] == converted_messages[i + 1]["role"]:
            logger.error(f"❌ Messages not alternating at index {i}: {converted_messages[i]['role']} -> {converted_messages[i+1]['role']}")

    payload = {
        "model": "sarvam-m",
        "messages": converted_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": stream
    }

    logger.info(f"📡 Calling Sarvam API | Messages: {len(converted_messages)} | Roles: {[m['role'] for m in converted_messages]}")

    try:
        response = requests.post(
            SARVAM_API_URL,
            headers=SARVAM_HEADERS,
            json=payload,
            stream=stream,
            timeout=60
        )

        logger.info(f"✅ API Response Status: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"❌ API Error {response.status_code}: {response.text}")

        return response

    except Exception as e:
        logger.error(f"❌ API Call Exception: {str(e)}")
        raise


# ============== Routes ==============

@api_router.get("/")
async def api_root():
    return {"message": "Nex.AI API is running"}


@api_router.get("/health")
async def health():
    return {
        "status": "healthy",
        "sarvam_api_configured": SARVAM_API_KEY is not None,
        "tavily_api_configured": TAVILY_API_KEY is not None,
        "sarvam_api_url": SARVAM_API_URL
    }


# ---------- STREAMING CHAT ----------
@api_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        try:
            if not SARVAM_API_KEY:
                yield f"data: {json.dumps({'error': 'SARVAM_API_KEY not configured'})}\n\n"
                return

            last_user_msg = request.messages[-1].content if request.messages else ""
            user_name = request.user_name

            if request.user_memory and request.user_memory.preferred_name:
                user_name = request.user_memory.preferred_name

            if request.active_mode and detect_mode_deactivation(last_user_msg):
                yield f"data: {json.dumps({'mode_action': 'deactivate'})}\n\n"
                live_context = ""
                if needs_live_search(last_user_msg) and TAVILY_API_KEY:
                    live_context = await search_tavily(last_user_msg)
                system_message = get_default_prompt(user_name, request.user_memory, live_context)

                messages = [{"role": "system", "content": system_message}]
                for msg in request.messages[-25:]:
                    messages.append({"role": msg.role, "content": msg.content})

                deactivate_settings = get_mode_settings("default")
                response = call_sarvam_api(
                    messages,
                    stream=True,
                    max_tokens=deactivate_settings["max_tokens"],
                    temperature=deactivate_settings["temperature"]
                )
                if response.status_code != 200:
                    yield f"data: {json.dumps({'error': f'API Error {response.status_code}: {response.text}'})}\n\n"
                    return

                async for chunk in _stream_response(response):
                    yield chunk

                yield f"data: {json.dumps({'done': True})}\n\n"
                return

            cards = None
            if request.active_mode == "startup":
                spin_keywords = ["spin", "start", "play", "new game"]
                if any(k in last_user_msg.lower() for k in spin_keywords):
                    cards = spin_cards()

            if request.active_mode == "learn":
                system_message = get_learn_mode_prompt(user_name, request.user_memory)
            elif request.active_mode == "english":
                system_message = get_english_mode_prompt(user_name, request.user_memory)
            elif request.active_mode == "startup":
                system_message = get_startup_game_prompt(user_name, cards)
            else:
                live_context = ""
                if needs_live_search(last_user_msg) and TAVILY_API_KEY:
                    live_context = await search_tavily(last_user_msg)
                system_message = get_default_prompt(user_name, request.user_memory, live_context)

            if cards:
                last_user_msg = (
                    f"[🎰 GAME SPIN — Audience: {cards['audience']}, "
                    f"Pain Point: {cards['pain_point']}, "
                    f"Tech: {cards['tech']}]\n\n{last_user_msg}"
                )

            messages = [{"role": "system", "content": system_message}]

            context_limits = {"learn": 40, "startup": 30, "english": 35}
            context_limit = context_limits.get(request.active_mode, 25)

            for msg in request.messages[-context_limit:]:
                messages.append({"role": msg.role, "content": msg.content})

            if cards and messages:
                messages[-1]["content"] = last_user_msg

            logger.info(f"💬 Stream chat | mode={request.active_mode} | messages={len(messages)} | context_limit={context_limit}")

            settings = get_mode_settings(request.active_mode)

            response = call_sarvam_api(
                messages,
                stream=True,
                max_tokens=settings["max_tokens"],
                temperature=settings["temperature"]
            )

            if response.status_code != 200:
                yield f"data: {json.dumps({'error': f'API Error {response.status_code}: {response.text}'})}\n\n"
                return

            async for chunk in _stream_response(response):
                yield chunk

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"❌ Chat stream error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def _stream_response(response):
    """
    Shared helper: parses SSE lines from Sarvam's streaming response
    and yields properly formatted SSE chunks for the client.
    """
    buffer = ""
    for line in response.iter_lines():
        if line:
            line_text = line.decode("utf-8")

            if line_text.startswith("data: "):
                data_str = line_text[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data_str)
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            # Clean markdown before sending
                            content = clean_markdown(content)
                            yield f"data: {json.dumps({'word': content})}\n\n"
                            await asyncio.sleep(0.01)
                except json.JSONDecodeError:
                    continue
            else:
                buffer += line_text
                try:
                    chunk_data = json.loads(buffer)
                    if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            # Clean markdown before sending
                            content = clean_markdown(content)
                            yield f"data: {json.dumps({'word': content})}\n\n"
                            await asyncio.sleep(0.01)
                    buffer = ""
                except json.JSONDecodeError:
                    continue


# ---------- SIMPLE (NON-STREAMING) CHAT ----------
@api_router.post("/chat/simple")
async def chat_simple(request: ChatRequest):
    try:
        if not SARVAM_API_KEY:
            return {"error": "SARVAM_API_KEY not configured in .env file", "success": False}

        last_user_msg = request.messages[-1].content if request.messages else ""
        user_name = request.user_name

        if request.user_memory and request.user_memory.preferred_name:
            user_name = request.user_memory.preferred_name

        mode_action = None
        if request.active_mode and detect_mode_deactivation(last_user_msg):
            mode_action = "deactivate"

        if mode_action == "deactivate" or not request.active_mode:
            live_context = ""
            if needs_live_search(last_user_msg) and TAVILY_API_KEY:
                live_context = await search_tavily(last_user_msg)
            system_message = get_default_prompt(user_name, request.user_memory, live_context)
        elif request.active_mode == "learn":
            system_message = get_learn_mode_prompt(user_name, request.user_memory)
        elif request.active_mode == "english":
            system_message = get_english_mode_prompt(user_name, request.user_memory)
        elif request.active_mode == "startup":
            system_message = get_startup_game_prompt(user_name)
        else:
            live_context = ""
            if needs_live_search(last_user_msg) and TAVILY_API_KEY:
                live_context = await search_tavily(last_user_msg)
            system_message = get_default_prompt(user_name, request.user_memory, live_context)

        messages = [{"role": "system", "content": system_message}]

        context_limits = {"learn": 40, "startup": 30, "english": 35}
        context_limit = context_limits.get(request.active_mode, 25)

        for msg in request.messages[-context_limit:]:
            messages.append({"role": msg.role, "content": msg.content})

        logger.info(f"💬 Simple chat | mode={request.active_mode} | messages={len(messages)} | context_limit={context_limit}")

        effective_mode = None if mode_action == "deactivate" else request.active_mode
        settings = get_mode_settings(effective_mode)

        response = call_sarvam_api(
            messages,
            stream=False,
            max_tokens=settings["max_tokens"],
            temperature=settings["temperature"]
        )

        if response.status_code != 200:
            return {"error": f"API Error {response.status_code}: {response.text}", "success": False}

        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"]
        
        # Clean markdown from response
        response_text = clean_markdown(response_text)

        result = {
            "response": response_text,
            "success": True,
            "conversation_id": request.conversation_id
        }

        if mode_action:
            result["mode_action"] = mode_action

        return result

    except Exception as e:
        logger.error(f"❌ Chat simple error: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}


# ---------- MEMORY EXTRACTION ----------
@api_router.post("/memory/extract", response_model=ExtractMemoryResponse)
async def extract_memory(request: ExtractMemoryRequest):
    try:
        if not SARVAM_API_KEY:
            logger.error("SARVAM_API_KEY not configured")
            return ExtractMemoryResponse(
                updated_memory=request.current_memory or UserMemory(),
                extracted_facts=[]
            )

        conversation_text = "\n".join(
            [f"{m.role.upper()}: {m.content}" for m in request.messages[-20:]]
        )
        current = request.current_memory or UserMemory()

        prompt = f"""You are a smart personal memory assistant. Your job: read this conversation and extract EVERY useful personal detail about the USER (not the AI).

CONVERSATION:
{conversation_text}

WHAT YOU ALREADY KNOW:
{json.dumps({
    "name": current.preferred_name,
    "interests": current.interests,
    "goals": current.goals,
    "personal_facts": current.personal_facts,
    "favorite_things": current.favorite_things,
    "recent_topics": current.recent_topics,
    "emotional_state": current.emotional_state
}, indent=2)}

EXTRACT EVERYTHING — be aggressive. Look for ANY of these:
- Their name (naam) — even if they say it casually like "I'm Rahul" or "mera naam Priya hai"
- Age — "I'm 20", "meri age 22 hai"
- City/location — "I'm from Delhi", "Jaipur mein rehta hoon"
- College/school — "I study at DU", "college mein..."
- Family details — siblings, parents, anything they mention
- What they're studying or working on
- Hobbies and interests — ANYTHING they seem to enjoy
- Favorite things — movies, songs, food, games, anything
- Goals and dreams — what they want to achieve
- Current mood/emotional state — are they happy, stressed, excited, sad?
- What topic we JUST discussed — always track this for continuity
- Any personal struggles or challenges they mentioned
- Their language preference (hindi/english/hinglish) based on how they write

BE AGGRESSIVE — if there's even a hint of personal info, extract it. Don't be shy. A good memory system remembers EVERYTHING.

Return ONLY this JSON (no markdown, no explanation):
{{
    "preferred_name": "their name or null if not mentioned",
    "language_style": "hindi or english or hinglish — based on how they actually wrote",
    "new_interests": ["NEW interests not already in the list above"],
    "skill_level": "beginner or intermediate or advanced or null",
    "new_goals": ["NEW goals not already known"],
    "new_facts": ["NEW personal facts — naam, age, city, college, family, struggles, ANYTHING personal. Be specific."],
    "communication_preferences": "casual or formal or funny — based on their writing style, or null",
    "new_favorite_things": ["NEW favorites — movies, songs, food, games, anything they like"],
    "current_topic": "what did we JUST talk about in this conversation — summarize in 3-5 words",
    "emotional_state": "happy or stressed or excited or sad or confused or neutral — based on their last messages"
}}"""

        messages = [
            {"role": "system", "content": "You are a precise JSON extraction assistant. Return ONLY valid JSON, nothing else."},
            {"role": "user", "content": prompt}
        ]

        response = call_sarvam_api(messages, stream=False, max_tokens=600, temperature=0.1)

        if response.status_code != 200:
            logger.error(f"Memory extraction API error: {response.status_code}")
            return ExtractMemoryResponse(updated_memory=current, extracted_facts=[])

        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"]

        try:
            clean = response_text.strip()
            if clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\n?', '', clean)
                clean = re.sub(r'\n?```$', '', clean)
            brace_count = 0
            end_idx = 0
            for i, ch in enumerate(clean):
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            if end_idx:
                clean = clean[:end_idx]

            extracted = json.loads(clean)
        except Exception:
            logger.error(f"JSON parse failed: {response_text}")
            return ExtractMemoryResponse(updated_memory=current, extracted_facts=[])

        current_topics = list(current.recent_topics or [])
        new_topic = extracted.get("current_topic")
        if new_topic and new_topic.strip():
            current_topics.append(new_topic.strip())
            current_topics = current_topics[-5:]

        updated = UserMemory(
            preferred_name=extracted.get("preferred_name") or current.preferred_name,
            language_style=extracted.get("language_style") or current.language_style,
            interests=list(set((current.interests or []) + (extracted.get("new_interests") or []))),
            skill_level=extracted.get("skill_level") or current.skill_level,
            goals=list(set((current.goals or []) + (extracted.get("new_goals") or []))),
            personal_facts=list(set((current.personal_facts or []) + (extracted.get("new_facts") or []))),
            communication_preferences=extracted.get("communication_preferences") or current.communication_preferences,
            favorite_things=list(set((current.favorite_things or []) + (extracted.get("new_favorite_things") or []))),
            recent_topics=current_topics,
            emotional_state=extracted.get("emotional_state") or current.emotional_state,
        )

        facts = (
            (extracted.get("new_interests") or []) +
            (extracted.get("new_goals") or []) +
            (extracted.get("new_facts") or []) +
            (extracted.get("new_favorite_things") or [])
        )
        if new_topic:
            facts.append(f"Topic: {new_topic}")

        return ExtractMemoryResponse(updated_memory=updated, extracted_facts=facts)

    except Exception as e:
        logger.error(f"Memory extraction error: {e}", exc_info=True)
        return ExtractMemoryResponse(
            updated_memory=request.current_memory or UserMemory(),
            extracted_facts=[]
        )


# ============== Mount Router & Middleware ==============

app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"]
)