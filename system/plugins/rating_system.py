import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PluginRating:
    plugin_id: str
    user_id: str
    rating: int  # 1-5 stars
    comment: Optional[str]
    timestamp: str
    version: str

class PluginRatingSystem:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.ratings_file = data_dir / "plugin_ratings.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._load_ratings()

    def _load_ratings(self):
        """Load existing ratings from file"""
        if self.ratings_file.exists():
            try:
                with open(self.ratings_file, 'r') as f:
                    self.ratings = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading ratings: {e}")
                self.ratings = {}
        else:
            self.ratings = {}

    def _save_ratings(self):
        """Save ratings to file"""
        try:
            with open(self.ratings_file, 'w') as f:
                json.dump(self.ratings, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving ratings: {e}")

    def add_rating(self, rating: PluginRating) -> bool:
        """Add a new rating for a plugin"""
        try:
            if rating.plugin_id not in self.ratings:
                self.ratings[rating.plugin_id] = []
            
            # Convert dataclass to dict for storage
            rating_dict = {
                "user_id": rating.user_id,
                "rating": rating.rating,
                "comment": rating.comment,
                "timestamp": rating.timestamp,
                "version": rating.version
            }
            
            self.ratings[rating.plugin_id].append(rating_dict)
            self._save_ratings()
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding rating: {e}")
            return False

    def get_plugin_rating(self, plugin_id: str) -> Dict:
        """Get average rating and stats for a plugin"""
        if plugin_id not in self.ratings:
            return {"average": 0, "total": 0}
            
        ratings = self.ratings[plugin_id]
        if not ratings:
            return {"average": 0, "total": 0}
            
        total = len(ratings)
        avg_rating = sum(r["rating"] for r in ratings) / total
        
        # Calculate rating distribution
        distribution = {i: sum(1 for r in ratings if r["rating"] == i) for i in range(1, 6)}
        
        return {
            "average": round(avg_rating, 2),
            "total": total,
            "distribution": distribution,
            "recent_comments": sorted(
                [r for r in ratings if r["comment"]], 
                key=lambda x: x["timestamp"],
                reverse=True
            )[:5]
        }

    def get_top_plugins(self, limit: int = 10) -> List[Dict]:
        """Get top rated plugins"""
        plugin_averages = []
        for plugin_id in self.ratings:
            stats = self.get_plugin_rating(plugin_id)
            if stats["total"] > 0:  # Only include plugins with ratings
                plugin_averages.append({
                    "plugin_id": plugin_id,
                    "average": stats["average"],
                    "total_ratings": stats["total"]
                })
        
        return sorted(
            plugin_averages,
            key=lambda x: (x["average"], x["total_ratings"]),
            reverse=True
        )[:limit]

if __name__ == "__main__":
    rating_system = PluginRatingSystem(Path("data/plugin_ratings"))
    
    # Example usage
    test_rating = PluginRating(
        plugin_id="test-plugin",
        user_id="user1",
        rating=5,
        comment="Great plugin!",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )
    
    rating_system.add_rating(test_rating)
    stats = rating_system.get_plugin_rating("test-plugin")
    print("Plugin Stats:", stats)
