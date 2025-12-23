# Contributing to LiveIndex

Thank you for your interest in contributing to LiveIndex! We welcome contributions from the community.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/liveindex.git
   cd liveindex
   ```
3. **Set up the development environment:**
   ```bash
   # Start Qdrant
   docker-compose up -d

   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

   # Frontend
   cd ../frontend
   npm install
   ```

## Making Changes

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and test them locally

3. **Commit your changes** with a clear message:
   ```bash
   git commit -m "Add: brief description of your change"
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** against the `main` branch

## Contribution Ideas

### Good First Issues

- **Add a connector** - Implement Google Drive, S3, Notion, Slack, or Confluence connector (see `backend/connectors/README.md`)
- **File type support** - Add PDF, DOCX, or PPTX parsing
- **UI improvements** - Better mobile responsiveness, dark mode, accessibility
- **Documentation** - Improve setup guides, add examples, fix typos
- **Tests** - Add unit tests or integration tests

### Larger Contributions

- Hybrid search (vector + keyword)
- Authentication & multi-tenancy
- Kubernetes Helm chart
- Analytics dashboard

## Code Style

- **Python**: Use type hints, follow PEP 8, use async/await for I/O
- **JavaScript/React**: Functional components, hooks, Tailwind CSS
- **Commits**: Use clear, descriptive commit messages

## Questions?

Open an issue or start a discussion on GitHub. We're happy to help!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
