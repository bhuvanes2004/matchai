# 💼 Match Maker AI – Job Resume Matching System

## 📌 Overview

Match Maker AI is a smart web-based application that connects **job seekers (candidates)** with **recruiters** using an AI-powered resume matching system.
The platform analyzes resumes, extracts skills, and matches them with job descriptions to provide a **compatibility score**.

---

## 🚀 Features

### 👤 Candidate

* Upload resume (PDF)
* Automatic skill extraction
* View recommended jobs
* AI-based match score
* Track applied jobs
* Profile strength indicator

### 🏢 Recruiter

* Post job openings
* View candidate profiles
* Match score for each candidate
* Shortlist / reject applicants

### 🧠 AI Features

* Resume parsing using keyword extraction
* Skill matching algorithm
* Match percentage calculation

---

## 🛠️ Tech Stack

* **Frontend:** HTML, CSS, Bootstrap, JavaScript
* **Backend:** Python (Flask)
* **Database:** SQLite3
* **AI Logic:** NLP (Keyword Matching)

---

## 📁 Project Structure

```
project/
│
├── app.py
├── database.db
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── jobs.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   └── images/
│
└── uploads/
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```
git clone https://github.com/your-username/match-maker-ai.git
cd match-maker-ai
```

### 2️⃣ Install Dependencies

```
pip install flask
```

### 3️⃣ Run the Application

```
python app.py
```

### 4️⃣ Open in Browser

```
http://127.0.0.1:5000/
```

---

## 🗄️ Database Schema

### Users

* id
* name
* email
* password
* role (candidate/recruiter)

### Jobs

* id
* title
* description
* skills_required
* recruiter_id

### Applications

* id
* user_id
* job_id
* match_score
* status

### Resumes

* id
* user_id
* file_path
* extracted_skills

---

## 🧮 AI Matching Logic

```
Match Score = (Matched Skills / Total Required Skills) × 100
```

---

## 🎨 UI/UX Design

* Clean and modern layout
* Responsive design (mobile + desktop)
* Bootstrap components (cards, navbar, forms)
* Blue + white professional theme

---

## 🔒 Security Features

* User authentication system
* Role-based access (Candidate / Recruiter)
* Secure file upload handling

---

## 📈 Future Enhancements

* Advanced NLP for better skill extraction
* Real-time chat system
* Job alerts & notifications
* Resume feedback system
* Machine learning-based recommendations

---

## 🤝 Contribution

Contributions are welcome!
Feel free to fork the repository and submit a pull request.

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

Developed by bhuvaneswaran A
