
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

        stage('Deploy') { // helm is good tools to manage the lifecycles of services
            steps {
                script {
                        echo "Deploy to target env"
                        sh "kubectl apply -f k8s/ "
                        // sh """
                        //        helm upgrade --install ads-ingestion \
                        //          ./helm-chart \
                        //          --set image.tag=${IMAGE_TAG} \
                        // """
                    } 
                }
            }
        }
    }
}
