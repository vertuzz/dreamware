
import asyncio
import sys
import os

# Add the backend directory to sys.path to allow importing from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models import Tool, Tag

TOOLS = [
    "Cursor",
    "Windsurf",
    "Trae",
    "PearAI",
    "Replit Agent",
    "v0",
    "Bolt.new",
    "Lovable",
    "Tempo",
    "Marblism",
    "Create.xyz",
    "Claude",
    "GPT",
    "DeepSeek",
    "Gemini",
    "Grok",
    "Llama",
    "Midjourney",
    "Flux",
    "Ideogram",
    "Recraft",
    "Google Image Gen",
    "Adobe Firefly",
    "Stable Diffusion",
    "DALL-E",
    "GitHub Copilot",
    "TabNine",
    "Pieces for Developers",
    "Qodo",
    "Uizard",
    "Figma AI",
    "Canva Magic Studio",
    "Runway",
    "Galileo AI",
    "Khroma"
]

TAGS = [
    "Cyberpunk",
    "Minimalist",
    "Brutalist",
    "SaaS",
    "Dashboard",
    "E-commerce",
    "Portfolio",
    "AI-Native",
    "Prompt-to-App",
    "Vibe Coding",
    "Full-Stack AI",
    "Glassmorphism",
    "Neumorphism",
    "Dark Mode",
    "Light Mode",
    "Mobile First",
    "Landing Page",
    "Retro",
    "Futuristic",
    "Clean",
    "Bento Grid",
    "Shadcn UI",
    "Tailwind CSS",
    "Next.js"
]

async def seed_data():
    async with AsyncSessionLocal() as session:
        print("Seeding initial tools...")
        for tool_name in TOOLS:
            # Check if tool exists
            result = await session.execute(select(Tool).where(Tool.name == tool_name))
            if not result.scalar_one_or_none():
                tool = Tool(name=tool_name)
                session.add(tool)
                print(f"Added tool: {tool_name}")
            else:
                print(f"Tool {tool_name} already exists, skipping.")

        print("\nSeeding initial tags...")
        for tag_name in TAGS:
            # Check if tag exists
            result = await session.execute(select(Tag).where(Tag.name == tag_name))
            if not result.scalar_one_or_none():
                tag = Tag(name=tag_name)
                session.add(tag)
                print(f"Added tag: {tag_name}")
            else:
                print(f"Tag {tag_name} already exists, skipping.")

        await session.commit()
        print("\nSeeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
