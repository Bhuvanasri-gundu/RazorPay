"""Seed Supabase from generated synthetic data or inline generator."""

import json
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.seed import seed_database

if __name__ == "__main__":
    seed_database()
