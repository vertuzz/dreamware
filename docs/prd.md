# Product Requirements Document (PRD): VibeHub

**Version:** 1.0  
**Status:** Draft  
**Date:** October 26, 2025  
**Document Owner:** Project Lead

---

## 1. Executive Summary

- **Product Name:** VibeHub (Working Title)
- **Concept:** A visual-first aggregation platform for AI-generated software concepts ("Vibe Coding").
- **Core Value Prop:** Vibe coding disconnects the idea from the implementation. VibeHub connects them back together. It allows creators to share "Dreamware" (Concept Art + System Prompts) and invites the community to turn those dreams into deployed apps using AI tools (Replit, Cursor, v0, Bolt).

**Mission:** To become the "Dribbble for AI Apps" — the primary destination where AI-native ideas are discovered, forked, and built.

---

## 2. Problem Statement

1. **The Fragmented Workflow:** "Vibe coders" generate amazing app ideas and visuals (Google Nano Banana, GPT image) but often lack the persistence to deploy them.
2. **No Central Gallery:** Twitter/X is ephemeral. Reddit is text-heavy. Product Hunt is for polished, finished businesses. There is no home for "cool experiments" or "half-finished vibes."
3. **Collaboration Gap:** Developers often have the skills/tools (Cursor, Replit, Claude code) but lack ideas. Vibe coders have ideas but get stuck on implementation.

---

## 3. Target Audience (Personas)

### A. The "Vibe Coder" (The Dreamer)
- **Profile:** Uses Google Nano Banana/GPT image for visuals and Claude/ChatGPT for text. May not know React/Python deeply.
- **Goal:** Wants to show off a cool app concept and prompt, hoping someone says "this is cool" or helps build it.
- **Pain Point:** *"I made this amazing UI mockup in v0, but I don't know how to connect the database."*

### B. The "Remixer" (The Builder)
- **Profile:** Comfortable with Cursor, Replit, or Bolt.new. Loves experimenting with new tech stacks.
- **Goal:** Needs inspiration. Wants to take a good prompt, tweak it, and deploy a working version to get clout.
- **Pain Point:** Staring at a blank IDE with no inspiration.

---

## 4. Competitive Analysis

| Competitor | Focus | Gap |
| :--- | :--- | :--- |
| **Product Hunt** | Finished Businesses | Too high-stakes. Rejects "toy" apps or raw concepts. |
| **Dribbble/Behance** | Static Design | No code/prompt sharing. Just visuals. |
| **Reddit (r/SideProject)** | Feedback | Text-heavy. Ugly UI. Hard to find "prompts." |
| **v0.dev / Bolt.new** | Creation Tools | These are editors, not galleries for discovery. |

---

## 5. Core Features (MVP)

### 5.1. The "Vibe" Submission (Create Post)
- **Concept Images (Required):** Support for one or more high-res uploads (or AI generation via API if budget allows). The "Vibe" is visual.
- **The "System Prompt" (The Source Code):** A structured text field for the actual prompt used to generate the app (e.g., "Create a retro-style Kanban board...").
- **Status:** "Concept Only" vs. "Live Demo."
- **Tags:** AI Tools Used (e.g., `#Cursor`, `#ReplitAgent`, `#GoogleNanoBanana`, `#GPTimage`, `#Claude3.5`).

### 5.2. The Feed (Discovery)
- **Pinterest-Style Grid:** Masonry layout. Minimal text. Hover to see title and "Vibe Check" score.
- **Filters:**
  - **By Tool:** "Show me apps built with Replit."
  - **By Tag:** Discover by aesthetics or use case (e.g., `#Cyberpunk`, `#SaaS`).
  - **By Status:** "Show me ideas that need a builder."
  - **Sort by Popularity:** Views, Likes, or "Vibe Check" score.

### 5.3. Interaction & Collaboration
- **"Vibe Check" (Rating):** High-fidelity quantitative feedback (0-100%).
- **Likes & Social Proof:** Quick "Like" (Heart) for feed ranking.
- **Followers:** Follow creators to build a personal "Dreamware" feed.
- **Collections:** Users can organize Vibes into public/private folders (e.g., "AI Side Projects").
- **Comments & Remix Linking:** Users can post comments on a Vibe. Comments can include text and links to their own implementations.
- **"Fork This Vibe" (Copy Prompt):** One-click button to copy the System Prompt. This creates a "Lineage" link in the database.
- **"Claim Project":** A user can click "I'm building this." This links their profile to the post as a "Collaborator."

### 5.4. Engagement
- **Notifications:** Real-time (or near real-time) alerts when someone Likes, Comments, or Forks your Vibe.

---

## 6. Functional Specifications

### 6.1. User Flow - The "Idea" Lifecycle
1. **User A** generates a UI mockup in Google Nano Banana.
2. **User A** posts it on VibeHub with the title "Neon To-Do List" and pastes the Claude prompt they tried to use.
3. **User A** tags it `#Concept` `#NeedsBuilder`.
4. **User B (Dev)** sees it, clicks "Copy Prompt," pastes it into Cursor, and fixes the bugs.
5. **User B** deploys to Vercel.
6. **User B** returns to VibeHub, comments the Vercel link.
7. **User A** marks the Vercel link as the "Official Implementation."

### 6.2. Data Model (Schema)
- **Users:** `id`, `username`, `email`, `avatar`, `reputation_score`, `auth_fields`
- **Tools:** `id`, `name`
- **Tags:** `id`, `name` (Aesthetic or category tags)
- **VibeImages:** `id`, `vibe_id`, `image_url`
- **Vibes (Posts):**
  - `id`, `creator_id`
  - `parent_vibe_id` (Link to the original "forked" Vibe)
  - `prompt_text`, `prd_text`, `extra_specs`
  - `status` (Concept, WIP, Live)
  - `tools` (Many-to-Many), `tags` (Many-to-Many)
- **Reviews (Vibe Checks):** `id`, `vibe_id`, `user_id`, `score`, `comment`
- **Comments:** `id`, `vibe_id`, `user_id`, `content`
- **Likes:** `id`, `vibe_id`, `user_id`
- **Collections:** `id`, `owner_id`, `name`, `vibes` (Many-to-Many)
- **Followers:** `follower_id`, `followed_id`
- **Notifications:** `id`, `user_id`, `type`, `content`, `link`, `is_read`

---

## 7. Technical Stack Recommendations

- **Frontend:** React, shadcn/ui (using a template).
- **Styling:** Tailwind CSS.
- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, managed with `uv`.
- **Database:** PostgreSQL.
- **Storage:**  S3 (or similar).
- **Auth:** email + password. + google + github.

---

## 8. Success Metrics (KPIs)

- **Fork Rate:** % of posts where the "Copy Prompt" button is clicked. (This proves utility).
- **Build Rate:** % of "Concept" posts that eventually get a "Live Link" added.
- **Time-to-Vibe:** How fast a user goes from landing page to viewing a prompt.

---

## 9. Future Roadmap (Post-MVP)

- **Direct Integration:** "Open in StackBlitz" or "Open in Replit" buttons that pre-fill the prompt.
- **Bounties:** Users can attach $50 (crypto/Stripe) to a "Concept" for whoever builds it first.
- **Weekly Vibe Batches:** Newsletter featuring the "Top 5 Forked Prompts" of the week.