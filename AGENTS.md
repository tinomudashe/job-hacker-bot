<general_rules>
- **One-Issue-One-Change Principle**: Only address one specific issue per pull request. Do not mix unrelated changes.
- **Surgical Changes Only**: Modify only the code necessary to fix the identified issue. Avoid broad, unrelated refactoring.
- **Test Before You Touch**: Before making changes, ensure you understand and have tested the current behavior.
</general_rules>

<repository_structure>
- The repository is a monorepo with two primary directories: `Frontend` and `backend`.
- **`Frontend`**: A Next.js application using TypeScript and TailwindCSS.
- **`backend`**: A FastAPI application using Python, SQLAlchemy, and PostgreSQL.
- **Refactoring**: The `backend/app/orchestrator.py` file is currently being refactored. Tools are being moved from this large file into smaller, more specialized files (e.g., `job_search.py`, `resume_generator.py`). When adding new tools, place them in the appropriate existing file or create a new one if necessary.
</repository_structure>

<dependencies_and_installation>
- **Frontend**: Navigate to the `Frontend` directory and run `npm install` to install all necessary Node.js dependencies.
- **Backend**:
  - Navigate to the `backend` directory and run `pip install -r requirements.txt` to install Python dependencies.
  - The backend also has Node.js dependencies. Run `npm install` inside the `backend` directory to install them.
- **Environment Variables**: Copy the `.env.example` file to a new `.env` file in the root directory and populate it with the required configuration values before running the applications.
</dependencies_and_installation>

<testing_instructions>
- **Frontend**:
  - Run `npx tsc --noEmit` to perform a TypeScript check.
  - Run `npx eslint . --ext .ts,.tsx` to check for linting errors.
- **Backend**:
  - Tests are written using the `pytest` framework.
  - Run tests by executing `pytest` from within the `backend` directory.
  - New code, especially for critical business logic, WebSocket functionality, and API endpoints (including error cases), should be accompanied by corresponding tests.
</testing_instructions>

<pull_request_formatting>
- **Title**: Your PR title should be concise and descriptive, following the format: `type(scope): short description`. For example: `feat(frontend): add user login page` or `fix(backend): resolve database connection issue`.
- **Description**: The PR description should provide a clear overview of the changes, including the problem being solved and the implementation details. Reference any related issues.
- **Changes**: Briefly list the major changes in the PR.
- **Testing**: Describe the testing youve done to verify your changes.
- **Screenshots**: If applicable, include screenshots or GIFs to demonstrate UI changes.
</pull_request_formatting>
