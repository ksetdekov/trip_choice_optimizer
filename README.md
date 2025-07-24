# trip_choice_optimizer

A Telegram bot to help you find the best option from a list of commute (or other) options using Thompson Sampling algorithms for Mean-Variance Bandits ([paper](https://arxiv.org/pdf/2002.00232.pdf)).

## Features

- Create optimizations (scenarios/decision problems) and add variants (options) to them.
- Add observations (sample data) for each variant.
- Use Thompson Sampling to recommend the best variant based on your data.
- All main user flows are available via inline keyboards for ease of use.
- Handles long optimization names and callback data limits.
- All core logic and database operations are covered by tests (92% coverage).

## Status

This project is **archived** and no longer under active development. All planned core features have been implemented:

- [x] Create new optimizations and variants
- [x] Add options/observations via inline keyboard
- [x] Handle callback data length issues
- [x] Core logic for mean-variance bandit and numeric optimizations
- [x] Database schema and migrations for all main entities
- [x] Test coverage for all main modules
- [x] Dockerfile for containerized deployment
- [x] User-friendly error handling and messaging
- [x] Inline keyboard for type selection (numeric/yes-no)
- [x] Binomial (yes/no) optimizations: UI stub, logic in development (not production-ready)

## Not Implemented / Known Limitations

- [ ] Binomial (yes/no) optimizations are not fully implemented (UI will inform user)
- [ ] No /back navigation or persistent state for user flows
- [ ] No persistent selection of optimization between steps
- [ ] Help/about messages could be improved for non-technical users
- [ ] Some edge cases (e.g., very long names > 280 bytes) may still need handling

## Usage

1. Clone the repository and install requirements:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Telegram bot token in a `.env` file or via environment variable.

3. Run the bot:

   ```bash
   python main.py
   ```

4. Or build and run with Docker:

   ```bash
   docker build -t ksetdekov/trip_choice_optimizer:latest .
   docker run --env-file .env ksetdekov/trip_choice_optimizer:latest
   ```

## Test Coverage

Run tests and see coverage:

```bash
coverage run --source=. -m unittest discover && coverage report
```

## About

This bot was created as a practical tool and demo for applying mean-variance bandit algorithms to real-world decision problems. It is now archived and not maintained further. For questions, see the code or contact the author.
