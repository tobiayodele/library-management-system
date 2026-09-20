# Library Management System

A system for managing a library's books, members, and lending records.

Achieved **69/70 mark** and serves a library with **1000+ members** . 

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [License](#license)
- [Author](#author)

## Features

- Add, edit, search, and remove books
- Register and manage library members
- Loan out and return books, with due dates
- Track availability of each title
- Role-based privileges

## Getting Started

### Prerequisites

- Python 3.11 or later.
- Bcrypt
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/tobiayodele/library-management-system.git
   cd library-management-system
   ```

2. Install dependencies:

   ```bash
   pip install bcrypt

   ```
> On some Linux distros tkinter is packaged separately. If you get ```No module named 'tkinter'``` install it with:
   ```bash
      sudo apt install python3-tk
   ```

4. Run the application:
   Windows:
   ```bash
   python library_manager.py
   ```
   Linux/macOS:
   ```
   python3 library_manager.py
   ```

## Usage

1. Log in as an admin or librarian.
2. Add books to the catalogue.
3. Register a member.
4. Issue a book to a member and record the due date.
5. Mark the book as returned when it comes back.

Screenshots or a short GIF of the app work well in this section.

## Project Structure

```
library-management-system/
├── Library Management System            # Application source code
│   ├── books2.db
│   ├── members2.db
│   └── library_manager.py
├── Test Videos                          # Visual Test Videos
├── LMS_report.docx                      # Report of the whole project
├── LMS_report.pdf 
└── README.md
```

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Author

**Tobi Ayodele** - [@tobiayodele](https://github.com/tobiayodele)
