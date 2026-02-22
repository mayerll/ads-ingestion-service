pipeline {
    agent any

    environment {
        IMAGE_NAME = "ads-ingestion-service"
    }

    stages {

        stage('Test') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'python -m py_compile app/main.py'
            }
        }

        stage('Build Docker') {
            steps {
                sh 'docker build -t $IMAGE_NAME:${BUILD_NUMBER} .'
            }
        }

        stage('Deploy Dry Run') {
            steps {
                sh 'kubectl apply --dry-run=client -f k8s/'
            }
        }
    }
}
