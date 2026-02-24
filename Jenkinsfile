
pipeline {
    agent any

    environment {
        IMAGE_NAME = "ads-ingestion-service"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Set Variables') {
            steps {
                script {
                    COMMIT_ID = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    IMAGE_TAG = "${env.BRANCH_NAME}-${COMMIT_ID}-${env.BUILD_NUMBER}"
                    echo "Docker tag will be: ${IMAGE_TAG}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest tests/'  
            }
        }

        stage('Build Docker') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Push Docker') {
            steps {
                sh "docker push docker.io/mayerll/${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Deploy') { // helm is good tools to manage the lifecycles of service
            steps {
                script {
                    if (env.BRANCH_NAME.startsWith('feature/')) {
                        echo "Feature branch - only build/test, no deployment"
                    } 
                    else if (env.BRANCH_NAME == 'develop') {
                        echo "Deploy to staging dry-run"
                        sh "kubectl apply -f k8s/ "
                    } 
                    else if (env.BRANCH_NAME == 'qa') {
                        echo "Deploy to QA environment"
                        sh "kubectl apply  -f k8s/ "
                    } 
                    else if (env.BRANCH_NAME == 'staging') {
                        echo "Deploy to staging environment"
                        sh "kubectl apply -f k8s/"
                    } 
                    else if (env.BRANCH_NAME == 'main') {
                        echo "Deploy to production"
                        sh "kubectl apply -f k8s/"
                    } 
                    else {
                        echo "Branch ${env.BRANCH_NAME} does not trigger deployment"
                    }
                }
            }
        }
    }
}
