# Training Data for Color Classifier

Pre-collected sticker images for training the KNN color classifier. Use this so you don't have to collect data yourself.

## Structure

```
training_data/
├── R/   # Red stickers
├── G/   # Green stickers
├── B/   # Blue stickers
├── Y/   # Yellow stickers
├── O/   # Orange stickers
└── W/   # White stickers
```

Each folder contains PNG images of individual sticker crops (extracted from cube faces).

## Usage

Train the KNN model from this pre-collected data (no need to collect your own):

```bash
python -c "
from color_classifier import ColorClassifier
c = ColorClassifier()
c.train_model('training_data')
c.save_model()
"
```

This creates `color_model.pkl`, which the solver uses for color classification. Then run:

```bash
python main.py --webcam
# or
python api.py   # for the Hexgate web frontend
```

To collect more data yourself, use `python collect_training_data.py`.
