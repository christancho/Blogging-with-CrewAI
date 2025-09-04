#!/usr/bin/env python3
"""
Constants for the CrewAI Blog Generation System
"""

# Content Analysis Constants
CONTENT_PREVIEW_LENGTH = 2000
MIN_WORD_COUNT_SUBSTANTIAL = 1000
MIN_WORD_COUNT_MODERATE = 500
MIN_WORD_COUNT_SHORT = 500

# Rate Limiting Constants
RATE_LIMIT_WAIT_TIME = 60  # seconds
MAX_TPM_LIMIT = 200000

# Progress Tracking Constants
TOTAL_WORKFLOW_STEPS = 5
PROGRESS_DELAY = 1  # seconds between steps

# File Constants
OUTPUT_FILE_EXTENSION = '.md'
MAX_RETRIES = 3

# Display Constants
SEPARATOR_LENGTH = 60
MAX_FILES_TO_DISPLAY = 10

# Content Quality Thresholds
QUALITY_EXCELLENT_WORDS = 1000
QUALITY_GOOD_WORDS = 500
