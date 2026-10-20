import os
AUTO_ACCEPT_BELOW = 1000      # > 0 and < 1000  -> auto accept
HUMAN_REVIEW_MAX = 10000      # 1000..10000     -> human review; above -> auto approval path
REVIEWER_API_KEY = os.getenv("REVIEWER_API_KEY", "reviewer-demo-key")
DB_PATH = os.getenv("DB_PATH", "loans.db")
