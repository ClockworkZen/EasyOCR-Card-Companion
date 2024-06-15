# EasyOCR Card Companion

EasyOCR Card Companion is a companion tool to [EasyOCR-Card-Scanner](https://github.com/ClockworkZen/EasyOCR-Card-Scanner). This script processes images of trading cards, identifies the card and TCG (Trading Card Game) name, and organizes them accordingly. It also supports cleaning up empty `Errors` directories after processing.

## Features

- Processes images of trading cards in `Errors` directories.
- Identifies card and TCG name using OpenAI's GPT-4o model.
- Moves processed images to the parent directory.
- Removes empty `Errors` directories if `CleanUpMode` is enabled.

## Requirements

- An OpenAI API key with valid paid compute time and permissions to ChatGPT-4o.
- Python 3.x.
- Required Python packages:
  - `requests`
  - `unidecode`

## Installation

1. Download the script to the directory directly above your Magic the Gathering or other TCG directories.

2. Install the required Python packages:
    ```
    pip install requests unidecode
    ```

3. Create a `tcg.cfg` file in the same directory as the script with the following content:
    ```
    openai_api_key=your_openai_api_key
    logging_level=WARNING
    CleanUpMode=true
    ```

## Usage

1. This is a companion tool to [EasyOCR-Card-Scanner](https://github.com/ClockworkZen/EasyOCR-Card-Scanner). It is intended to be run after using EasyOCR Card Scanner to automatically identify difficult cards using OpenAI's API.

2. Run the script:
    ```
    python easyocr_card_companion.py
    ```
3. The script will process the images, identify the cards, and move the processed images to the parent directory. If `CleanUpMode` is enabled, it will also remove empty `Errors` directories.

## Configuration

The `tcg.cfg` file supports the following settings:

- `openai_api_key`: Your OpenAI API key with permissions to ChatGPT-4o.
- `logging_level`: The logging level (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `CleanUpMode`: Boolean flag to enable or disable the removal of empty `Errors` directories after processing (default is `true`).


## Contributing

Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)

## Acknowledgments

- This tool is a companion to [EasyOCR-Card-Scanner](https://github.com/your-repo/EasyOCR-Card-Scanner).
- Powered by [OpenAI's GPT-4o](https://www.openai.com/).
