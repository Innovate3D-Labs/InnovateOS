import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class FeedbackEntry:
    id: str
    user_id: str
    category: str  # 'bug', 'feature', 'improvement'
    title: str
    description: str
    timestamp: str
    status: str  # 'new', 'in_progress', 'resolved', 'closed'
    votes: int
    tags: List[str]
    anonymous: bool

class CommunityFeedbackPortal:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.feedback_file = data_dir / "community_feedback.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._load_feedback()

    def _load_feedback(self):
        """Load existing feedback from file"""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    self.feedback = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading feedback: {e}")
                self.feedback = {}
        else:
            self.feedback = {}

    def _save_feedback(self):
        """Save feedback to file"""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(self.feedback, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving feedback: {e}")

    def submit_feedback(self, entry: FeedbackEntry) -> bool:
        """Submit new feedback"""
        try:
            feedback_dict = {
                "id": entry.id,
                "user_id": entry.user_id if not entry.anonymous else "anonymous",
                "category": entry.category,
                "title": entry.title,
                "description": entry.description,
                "timestamp": entry.timestamp,
                "status": entry.status,
                "votes": entry.votes,
                "tags": entry.tags,
                "anonymous": entry.anonymous
            }
            
            self.feedback[entry.id] = feedback_dict
            self._save_feedback()
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting feedback: {e}")
            return False

    def vote_feedback(self, feedback_id: str, user_id: str, vote: int) -> bool:
        """Vote on feedback (1 for upvote, -1 for downvote)"""
        try:
            if feedback_id in self.feedback:
                vote_key = f"votes_{feedback_id}"
                if not hasattr(self, vote_key):
                    setattr(self, vote_key, set())
                
                voters = getattr(self, vote_key)
                if user_id not in voters:
                    self.feedback[feedback_id]["votes"] += vote
                    voters.add(user_id)
                    self._save_feedback()
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error processing vote: {e}")
            return False

    def get_trending_feedback(self, limit: int = 10) -> List[Dict]:
        """Get trending feedback based on votes and recency"""
        try:
            sorted_feedback = sorted(
                self.feedback.values(),
                key=lambda x: (x["votes"], x["timestamp"]),
                reverse=True
            )
            return sorted_feedback[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting trending feedback: {e}")
            return []

    def get_feedback_stats(self) -> Dict:
        """Get feedback statistics"""
        try:
            total = len(self.feedback)
            categories = {}
            statuses = {}
            tags = {}
            
            for entry in self.feedback.values():
                categories[entry["category"]] = categories.get(entry["category"], 0) + 1
                statuses[entry["status"]] = statuses.get(entry["status"], 0) + 1
                for tag in entry["tags"]:
                    tags[tag] = tags.get(tag, 0) + 1
                    
            return {
                "total_feedback": total,
                "by_category": categories,
                "by_status": statuses,
                "popular_tags": dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting feedback stats: {e}")
            return {}

    def update_feedback_status(self, feedback_id: str, new_status: str) -> bool:
        """Update the status of a feedback entry"""
        try:
            if feedback_id in self.feedback:
                self.feedback[feedback_id]["status"] = new_status
                self._save_feedback()
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating feedback status: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    portal = CommunityFeedbackPortal(Path("data/community"))
    
    # Create a new feedback entry
    feedback = FeedbackEntry(
        id=hashlib.md5("test_feedback".encode()).hexdigest(),
        user_id="user1",
        category="feature",
        title="Add support for TPU filament",
        description="Would love to see specific settings for TPU filament",
        timestamp=datetime.now().isoformat(),
        status="new",
        votes=0,
        tags=["material", "feature-request"],
        anonymous=False
    )
    
    portal.submit_feedback(feedback)
    stats = portal.get_feedback_stats()
    print("Feedback Stats:", stats)
