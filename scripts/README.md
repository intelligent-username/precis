# Scripts

These are scripts that are run separetly from the app. They are used to collect data and fine-tune the model(s) being run for the actual app's functionality.

## Pull.py

Pull.py pulls (downloads) different datasets that are known to be exemplary fine-tuners for the task of summarization in the way we're trying to perform it. It'll place the data in the data directory.

## Cleaners

Cleaners are scripts that are used to clean up the data that is collected. They are used to remove any irrelevant information from the data. The data is then modified by hand to ensure even better performance.

## Train.py

Train.py simply fine-tunes the model with the cleaned data, and then places the model in the trained_models directory.
