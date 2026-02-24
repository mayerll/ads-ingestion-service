
pipeline {
    agent any

    environment {
        IMAGE_NAME = "ads-ingestion-service"
        QA_NAMESPACE = "qa"
        STAGING_NAMESPACE = "staging"
        PROD_NAMESPACE = "production"
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
                echo "Docker push logic here for ${IMAGE_TAG}"
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
                        sh "kubectl apply -n ${STAGING_NAMESPACE} -f k8s/ --dry-run=client"
                    } 
                    else if (env.BRANCH_NAME == 'qa') {
                        echo "Deploy to QA environment"
                        sh "kubectl apply -n ${QA_NAMESPACE} -f k8s/ --dry-run=client"
                    } 
                    else if (env.BRANCH_NAME == 'staging') {
                        echo "Deploy to staging environment"
                        sh "kubectl apply -n ${STAGING_NAMESPACE} -f k8s/"
                    } 
                    else if (env.BRANCH_NAME == 'main') {
                        echo "Deploy to production"
                        sh "kubectl apply -n ${PROD_NAMESPACE} -f k8s/"
                    } 
                    else {
                        echo "Branch ${env.BRANCH_NAME} does not trigger deployment"
                    }
                }
            }
        }
    }
}
