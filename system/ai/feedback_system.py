import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional
import tensorflow as tf
from .print_monitor import PrintMonitor
from .train_model import ModelTrainer

class FeedbackSystem:
    def __init__(self, feedback_dir: Path):
        self.feedback_dir = feedback_dir
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.print_monitor = PrintMonitor()
        
    def submit_feedback(self, prediction_id: str, actual_result: bool, image_path: str, notes: Optional[str] = None) -> bool:
        """Submit feedback for a prediction"""
        try:
            feedback_data = {
                "prediction_id": prediction_id,
                "timestamp": datetime.now().isoformat(),
                "actual_result": actual_result,
                "image_path": str(image_path),
                "notes": notes
            }
            
            feedback_file = self.feedback_dir / f"feedback_{prediction_id}.json"
            with open(feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=4)
                
            self.logger.info(f"Feedback submitted for prediction {prediction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting feedback: {e}")
            return False
            
    def collect_training_data(self) -> List[Dict]:
        """Collect all feedback data for model retraining"""
        feedback_data = []
        for feedback_file in self.feedback_dir.glob("feedback_*.json"):
            try:
                with open(feedback_file, 'r') as f:
                    data = json.load(f)
                feedback_data.append(data)
            except Exception as e:
                self.logger.error(f"Error reading feedback file {feedback_file}: {e}")
                
        return feedback_data
        
    def retrain_with_feedback(self, model_dir: Path):
        """Retrain model using collected feedback data"""
        feedback_data = self.collect_training_data()
        if not feedback_data:
            self.logger.info("No feedback data available for retraining")
            return
            
        try:
            trainer = ModelTrainer(self.feedback_dir, model_dir)
            trainer.train_model(epochs=10)  # Shorter training for feedback updates
            self.logger.info("Model retrained with feedback data")
            
        except Exception as e:
            self.logger.error(f"Error retraining model: {e}")
            
    def analyze_feedback_trends(self) -> Dict:
        """Analyze feedback trends for model performance insights"""
        feedback_data = self.collect_training_data()
        total = len(feedback_data)
        if not total:
            return {"total": 0}
            
        correct_predictions = sum(1 for f in feedback_data if f["actual_result"])
        accuracy = correct_predictions / total if total > 0 else 0
        
        return {
            "total_feedback": total,
            "correct_predictions": correct_predictions,
            "accuracy": accuracy,
            "last_feedback": feedback_data[-1]["timestamp"] if feedback_data else None
        }

if __name__ == "__main__":
    feedback_system = FeedbackSystem(Path("data/feedback"))
    trends = feedback_system.analyze_feedback_trends()
    print("Feedback Trends:", trends)
