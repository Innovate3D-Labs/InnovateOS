import tensorflow as tf
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from typing import Tuple, Optional
from training_data_generator import TrainingDataGenerator
from print_monitor import PrintMonitor

class ModelTrainer:
    def __init__(self, data_dir: Path, model_dir: Path):
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.logger = logging.getLogger(__name__)
        self.image_size = (224, 224)
        
        # Initialize data generator
        self.data_generator = TrainingDataGenerator(data_dir)
        
        # Initialize print monitor for model access
        self.print_monitor = PrintMonitor()

    def prepare_dataset(self, validation_split: float = 0.2) -> Tuple[tf.data.Dataset, tf.data.Dataset]:
        """Prepare training and validation datasets"""
        try:
            # Load real data if available
            X_real, y_real = self._load_real_data()
            
            # Generate synthetic data
            X_syn, y_syn = self.data_generator.generate_synthetic_data(1000)
            
            # Combine real and synthetic data
            X = np.concatenate([X_real, X_syn]) if X_real is not None else X_syn
            y = np.concatenate([y_real, y_syn]) if y_real is not None else y_syn
            
            # Data augmentation
            X_aug, y_aug = self.data_generator.augment_data(X, y)
            
            # Combine with augmented data
            X = np.concatenate([X, X_aug])
            y = np.concatenate([y, y_aug])
            
            # Create TensorFlow datasets
            dataset = tf.data.Dataset.from_tensor_slices((X, y))
            dataset = dataset.shuffle(buffer_size=len(X))
            
            # Split into training and validation
            val_size = int(len(X) * validation_split)
            train_size = len(X) - val_size
            
            train_dataset = dataset.take(train_size)
            val_dataset = dataset.skip(train_size)
            
            # Batch and prefetch
            train_dataset = train_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
            val_dataset = val_dataset.batch(32).prefetch(tf.data.AUTOTUNE)
            
            return train_dataset, val_dataset
            
        except Exception as e:
            self.logger.error(f"Error preparing dataset: {e}")
            raise

    def _load_real_data(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Load real printer data if available"""
        real_data_path = self.data_dir / "real_data"
        if real_data_path.exists():
            return self.data_generator.load_dataset(real_data_path)
        return None, None

    def train_model(self, epochs: int = 50) -> None:
        """Train the error detection model"""
        try:
            # Prepare datasets
            train_dataset, val_dataset = self.prepare_dataset()
            
            # Get model from print monitor
            model = self.print_monitor.model
            
            # Add callbacks
            callbacks = [
                tf.keras.callbacks.ModelCheckpoint(
                    filepath=str(self.model_dir / "best_model.h5"),
                    save_best_only=True,
                    monitor='val_accuracy'
                ),
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.TensorBoard(
                    log_dir=str(self.model_dir / "logs" / datetime.now().strftime("%Y%m%d-%H%M%S")),
                    histogram_freq=1
                )
            ]
            
            # Train model
            history = model.fit(
                train_dataset,
                validation_data=val_dataset,
                epochs=epochs,
                callbacks=callbacks
            )
            
            # Save final model
            model.save(str(self.model_dir / "final_model.h5"))
            
            # Save training history
            self._save_training_history(history.history)
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            raise

    def _save_training_history(self, history: dict) -> None:
        """Save training history to file"""
        history_file = self.model_dir / "training_history.json"
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=4)

    def evaluate_model(self) -> dict:
        """Evaluate the trained model"""
        try:
            # Load test dataset
            test_data_path = self.data_dir / "test_data"
            if test_data_path.exists():
                X_test, y_test = self.data_generator.load_dataset(test_data_path)
                
                # Evaluate model
                results = self.print_monitor.model.evaluate(X_test, y_test)
                
                # Generate evaluation metrics
                metrics = {
                    'loss': float(results[0]),
                    'accuracy': float(results[1]),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Save metrics
                metrics_file = self.model_dir / "evaluation_metrics.json"
                with open(metrics_file, 'w') as f:
                    json.dump(metrics, f, indent=4)
                
                return metrics
            else:
                self.logger.warning("No test data available for evaluation")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error evaluating model: {e}")
            raise

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize paths
    data_dir = Path("data/training")
    model_dir = Path("models")
    
    # Create trainer and train model
    trainer = ModelTrainer(data_dir, model_dir)
    trainer.train_model()
    
    # Evaluate model
    metrics = trainer.evaluate_model()
    print("Evaluation metrics:", metrics)
