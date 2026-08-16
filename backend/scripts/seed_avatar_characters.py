#!/usr/bin/env python3
"""
Hermes LinguaMind — avatar character seeder.

Inserts a couple of default AvatarCharacterORM rows so the avatar system
has something to point at out of the box. Reference/config data like this
is fine to write directly via the ORM (unlike user accounts) — there's no
password hashing or business-rule validation to route through an API for.

The `opentalking_avatar_id` values here point at the sample avatars that
ship in OpenTalking's own `examples/avatars` directory (see
docker-compose.yml OPENTALKING_AVATARS_DIR) — swap in your own once you've
added custom avatars via the OpenTalking WebUI.

Usage (run inside the hermes_backend container, or anywhere with
DATABASE_URL pointed at the same Postgres):
    python3 scripts/seed_avatar_characters.py

Safe to re-run — skips any slug that already exists.
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "phase3"))

from sqlalchemy import select  # noqa: E402

from shared.database import get_db_session, init_db  # noqa: E402
from shared.models.common import AvatarCharacterORM  # noqa: E402

DEFAULT_CHARACTERS = [
    {
        "slug": "hermes-default",
        "display_name": "Hermes",
        "personality_prompt": (
            "You are Hermes, a warm and patient multilingual tutor. Keep "
            "replies short and conversational, correct mistakes gently, "
            "and adapt your language level to the learner."
        ),
        "teaching_style": "conversational",
        "opentalking_avatar_id": "default",
        "opentalking_model": "mock",  # swap to quicktalk/wav2lip once you have GPU + weights
        "voice_id": "edge:en-US-AriaNeural",
        "emotion_profile": {"default": "friendly", "on_correction": "encouraging"},
    },
    {
        "slug": "maria-spanish-tutor",
        "display_name": "Maria",
        "personality_prompt": (
            "You are Maria, an enthusiastic native Spanish speaker helping "
            "learners practice conversational Spanish. Mix in cultural "
            "context naturally and switch to English briefly only when the "
            "learner seems lost."
        ),
        "teaching_style": "immersive",
        "opentalking_avatar_id": "default",
        "opentalking_model": "mock",
        "voice_id": "edge:es-ES-ElviraNeural",
        "emotion_profile": {"default": "warm", "on_correction": "playful"},
    },
]


async def main() -> int:
    await init_db()
    created = 0
    async with get_db_session() as db:
        for char in DEFAULT_CHARACTERS:
            existing = await db.execute(
                select(AvatarCharacterORM).where(AvatarCharacterORM.slug == char["slug"])
            )
            if existing.scalar_one_or_none() is not None:
                print(f"skip (exists): {char['slug']}")
                continue
            db.add(AvatarCharacterORM(**char))
            created += 1
            print(f"created: {char['slug']}")
    print(f"Done. {created} character(s) created.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
