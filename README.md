# 🧠 Wumpus World Logic Agent (Web-Based)

## 🔗 Live Demo
https://wumpus-logic-agent-ju2l2a38u-abdullah-ahmad-s-projects.vercel.app/

---

## 📌 Project Overview

This project implements a **Web-Based Dynamic Wumpus World Agent** that simulates a **Knowledge-Based Agent** operating in an uncertain environment. The agent navigates a grid world while using logical reasoning based on percepts to identify safe and unsafe cells.

The system demonstrates core Artificial Intelligence concepts including **Propositional Logic, Knowledge Representation, and Inference Mechanisms**.

---

## 🎯 Objectives

- To design a dynamic grid-based Wumpus World environment  
- To implement an intelligent agent capable of reasoning under uncertainty  
- To simulate percept-based decision making (Breeze and Stench)  
- To visualize agent movement and environment states in real-time  
- To deploy the application as a live web-based system  

---

## ⚙️ Features

### 🌐 Dynamic Environment
- User-defined grid size (Rows × Columns)
- Random placement of:
  - 🕳️ Pits
  - 🐉 Wumpus

---

### 👁️ Percept System
The agent receives percepts based on its current position:

- **Breeze** → Indicates a nearby Pit  
- **Stench** → Indicates a nearby Wumpus  

---

### 🧠 Knowledge-Based Agent
- Maintains a **Knowledge Base (KB)** of visited cells and percepts  
- Updates KB dynamically after each move  
- Uses logical inference to deduce safe cells  

---

### 🔍 Inference Mechanism
- If a cell has **no Breeze and no Stench**, all adjacent cells are marked safe  
- The agent prioritizes movement to **safe and unvisited cells**  
- Tracks inference steps as part of reasoning metrics  

---

### 📊 Visualization & UI
- Interactive grid displayed in the browser  
- Color-coded cells:
  - 🟢 Safe cells  
  - ⚪ Unknown cells  
  - 🟡 Agent position  
- Real-time metrics dashboard:
  - Inference steps  
  - Current percepts  

---

## 🚀 Tech Stack

- **Frontend:** HTML, CSS, JavaScript  
- **Backend (Initial Development):** Python (Flask)  
- **Deployment:** Vercel (Frontend Hosting)  
- **Version Control:** Git & GitHub  

---

## 🏗️ Project Structure
wumpus-frontend/
│── index.html # Main UI file
│── script.js # Agent logic & interaction
│── style.css # Styling (optional)


---

## ▶️ How to Run Locally

1. Download or clone the repository:
https://github.com/Abdullah003-hub/Wumpus-Logic-Agent

2. Open the project folder

3. Run the application:
- Simply open `index.html` in your browser

---

## 🌍 Deployment

The project is deployed using **Vercel** as a static frontend application.

Steps followed:
- Converted Flask-based project to frontend-only (HTML/JS)
- Uploaded code to GitHub
- Connected GitHub repo to Vercel
- Deployed without build configuration

---

## 🎥 Demo

(Add your screen recording link here)

---

## 💡 Challenges Faced

- Converting backend (Flask) logic into frontend JavaScript  
- Simulating a Knowledge Base without a full logic engine  
- Designing inference rules that approximate logical reasoning  
- Managing dynamic updates in UI based on agent decisions  

---

## 🔮 Future Improvements

- Full implementation of **Resolution Refutation (CNF-based reasoning)**  
- Smarter pathfinding algorithms (A*, BFS)  
- Probability-based Wumpus detection  
- Advanced UI with animations and dashboards  
- Backend integration for complex logic processing  

---

## 📚 AI Concepts Used

- Knowledge-Based Agents  
- Propositional Logic  
- Inference Rules  
- Environment Modeling  
- Decision Making under Uncertainty  

---

## 👨‍💻 Author

**Your Name**  
BSCS Student  

---

## ⭐ Acknowledgment

This project was developed as part of an Artificial Intelligence coursework assignment to demonstrate understanding of logic-based agents and intelligent systems.

---
