# ReferFlow | Automated Telegram Link Exchange Bot 🚀

**ReferFlow** is a Python-powered Telegram bot designed to automate and streamline link exchanges between users. This project focuses on efficient data management using an integrated database while maintaining a clean, minimalist user interface.

---

## 🛠️ Key Features
* **Automated Exchanges:** Simplifies the process of sharing and exchanging links within groups or private chats.
* **Database Integration:** Utilizes `sqlite3` for robust, lightweight, and persistent data storage.
* **Minimalist UX:** Focused on high efficiency with low-friction command handling.
* **Privacy by Design:** Administrative functions (such as `/cari`) are restricted from public documentation to ensure secure operations.

## 🛡️ Security & SOC Alignment
As an aspiring **SOC Analyst**, I have implemented the following security best practices in this development lifecycle:
* **Secret Management:** Sensitive API tokens are managed via environment variables (`.env`) and are never hardcoded in the source code.
* **Version Control Hygiene:** A strict `.gitignore` policy is enforced to prevent the accidental exposure of credentials (`tkn.env`) and local environment binaries.
* **Input Validation:** Implementation of basic sanitization to ensure bot stability and protect against common injection vulnerabilities.

## 💻 Tech Stack
* **Language:** Python 3.x
* **Framework:** `python-telegram-bot`
* **Database:** SQLite
* **Environment Control:** `python-dotenv`

## 📋 Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Atiqlaa/ReferFlow.git
   cd ReferFlow
