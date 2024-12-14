import cv2
import numpy as np
from pathlib import Path
import json
import random
from datetime import datetime
import tensorflow as tf
from typing import Tuple, List

class TrainingDataGenerator:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.image_size = (224, 224)
        self.augmentation_params = {
            'rotation_range': 20,
            'width_shift_range': 0.2,
            'height_shift_range': 0.2,
            'shear_range': 0.2,
            'zoom_range': 0.2,
            'horizontal_flip': True,
            'fill_mode': 'nearest'
        }

    def generate_synthetic_data(self, num_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data for print errors"""
        X = np.zeros((num_samples, *self.image_size, 3))
        y = np.zeros(num_samples)

        for i in range(num_samples):
            if i % 2 == 0:
                # Generate normal print image
                X[i] = self._generate_normal_print()
                y[i] = 0
            else:
                # Generate error print image
                X[i] = self._generate_error_print()
                y[i] = 1

        return X, y

    def _generate_normal_print(self) -> np.ndarray:
        """Generate synthetic image of normal print"""
        image = np.ones((*self.image_size, 3)) * 255

        # Add basic layer structure
        for layer in range(random.randint(5, 15)):
            height = int(self.image_size[1] * (layer / 15))
            cv2.line(image, (0, height), (self.image_size[0], height), 
                    (200, 200, 200), 2)

        # Add texture
        noise = np.random.normal(0, 10, image.shape).astype(np.uint8)
        image = cv2.add(image.astype(np.uint8), noise)

        return image

    def _generate_error_print(self) -> np.ndarray:
        """Generate synthetic image of print with errors"""
        image = self._generate_normal_print()

        # Add random error effects
        error_type = random.choice(['stringing', 'layer_shift', 'under_extrusion'])

        if error_type == 'stringing':
            self._add_stringing(image)
        elif error_type == 'layer_shift':
            self._add_layer_shift(image)
        else:
            self._add_under_extrusion(image)

        return image

    def _add_stringing(self, image: np.ndarray) -> None:
        """Add stringing artifacts to image"""
        for _ in range(random.randint(5, 15)):
            start_point = (random.randint(0, self.image_size[0]), 
                         random.randint(0, self.image_size[1]))
            end_point = (start_point[0] + random.randint(-20, 20),
                        start_point[1] + random.randint(-20, 20))
            cv2.line(image, start_point, end_point, (150, 150, 150), 1)

    def _add_layer_shift(self, image: np.ndarray) -> None:
        """Add layer shift effect to image"""
        shift_point = random.randint(0, self.image_size[1])
        shift_amount = random.randint(10, 30)
        
        top_part = image[0:shift_point, :, :]
        bottom_part = image[shift_point:, :, :]
        
        # Shift bottom part
        M = np.float32([[1, 0, shift_amount], [0, 1, 0]])
        bottom_part = cv2.warpAffine(bottom_part, M, 
                                   (self.image_size[0], self.image_size[1]-shift_point))
        
        image[shift_point:, :, :] = bottom_part

    def _add_under_extrusion(self, image: np.ndarray) -> None:
        """Add under-extrusion effect to image"""
        for _ in range(random.randint(3, 8)):
            x = random.randint(0, self.image_size[0]-50)
            y = random.randint(0, self.image_size[1]-50)
            w = random.randint(20, 50)
            h = random.randint(20, 50)
            
            roi = image[y:y+h, x:x+w]
            roi = cv2.multiply(roi.astype(np.uint8), 0.7).astype(np.uint8)
            image[y:y+h, x:x+w] = roi

    def augment_data(self, images: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Augment training data using various transformations"""
        datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            **self.augmentation_params
        )
        
        augmented_images = []
        augmented_labels = []
        
        for image, label in zip(images, labels):
            # Generate 3 augmented versions of each image
            for _ in range(3):
                aug_image = datagen.random_transform(image)
                augmented_images.append(aug_image)
                augmented_labels.append(label)
        
        return np.array(augmented_images), np.array(augmented_labels)

    def save_dataset(self, images: np.ndarray, labels: np.ndarray, 
                    output_dir: Path) -> None:
        """Save generated dataset to disk"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save images
        for i, (image, label) in enumerate(zip(images, labels)):
            image_path = output_dir / f"image_{i}_{int(label)}.jpg"
            cv2.imwrite(str(image_path), image)
        
        # Save labels
        labels_file = output_dir / "labels.json"
        with open(labels_file, 'w') as f:
            json.dump({
                'labels': labels.tolist(),
                'timestamp': datetime.now().isoformat(),
                'image_size': self.image_size
            }, f)

    def load_dataset(self, input_dir: Path) -> Tuple[np.ndarray, np.ndarray]:
        """Load dataset from disk"""
        # Load labels
        labels_file = input_dir / "labels.json"
        with open(labels_file, 'r') as f:
            labels_data = json.load(f)
        
        labels = np.array(labels_data['labels'])
        
        # Load images
        images = []
        for i in range(len(labels)):
            image_path = input_dir / f"image_{i}_{int(labels[i])}.jpg"
            image = cv2.imread(str(image_path))
            images.append(image)
        
        return np.array(images), labels
