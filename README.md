Stock Recommender (Python + Flask, AWS-Ready)

This project is a Python + Flask web application that recommends groups of stocks based on a user’s investing goal (e.g., safe index funds, tech growth, dividend picks).  

It is currently running locally, but the design is AWS-ready for deployment (Amplify for frontend, API Gateway + Lambda for backend, DynamoDB for storage). The goal is to show backend development, API design, and cloud-readiness skills.

---
Features
- Built with Flask for lightweight web serving
- User input mapped to pre-defined stock “buckets”
- Live price lookup using external APIs/libraries (e.g., `yfinance`)
- Clear separation of logic for easy scaling
- Designed to integrate with AWS services (not yet deployed)

---

Planned AWS Architecture
- **Frontend:** AWS Amplify for static hosting  
- **Backend:** Flask app containerized or adapted to run on AWS Lambda + API Gateway  
- **Database:** DynamoDB for persisting user requests or watchlists  
- **CI/CD:** GitHub → AWS CodePipeline or Amplify build system  

Currently local only — but ready for AWS deployment with minor adjustments.

---

Contact Feel free to connect with me:

LinkedIn: https://www.linkedin.com/in/aditya-jadhav-68190a254/ Email: adityajadhav5607@gmail.com
